"""Celery application factory and worker configuration.

Design decisions
----------------
* **Pool: ``gevent``** — Playwright in each task runs inside an event loop
  created by ``asyncio.run()``.  Gevent is the best Celery pool for I/O-bound
  tasks because it allows thousands of concurrent green threads without the
  overhead of OS threads.  If gevent is unavailable, ``threads`` pool is used
  as fallback.

* **Concurrency: 20** — Each slot corresponds to one gevent greenlet running
  one Playwright page asynchronously.  The page count is further bounded by
  ``Settings.scraper_max_concurrent_pages`` inside the task itself.

* **Task acknowledgement: ``acks_late=True``** — Tasks are acknowledged only
  after completion, preventing data loss if the worker crashes mid-scrape.

* **Rate limiting: per-task** — ``rate_limit="10/m"`` on scraping tasks
  prevents a single domain from being hammered; the circuit breaker provides
  a secondary layer.

* **Result backend** — Redis (same broker) stores task results for 1 hour.

Usage
-----
Start the worker::

    celery -A travel.worker.celery_app worker --pool=gevent --concurrency=20 -l INFO

Beat scheduler (for periodic tasks)::

    celery -A travel.worker.celery_app beat -l INFO
"""
from __future__ import annotations

import logging

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from travel.config import get_settings

logger = logging.getLogger(__name__)


def create_celery_app() -> Celery:
    """Build and configure the Celery application."""
    settings = get_settings()

    app = Celery(
        "travel",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "travel.worker.tasks",  # auto-discover tasks module
        ],
    )

    app.conf.update(
        # -------------------------------------------------------------------
        # Serialisation
        # -------------------------------------------------------------------
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        # -------------------------------------------------------------------
        # Execution
        # -------------------------------------------------------------------
        task_acks_late=True,              # ack only after task completes
        task_reject_on_worker_lost=True,  # re-queue if worker crashes
        task_track_started=True,
        # -------------------------------------------------------------------
        # Result storage
        # -------------------------------------------------------------------
        result_expires=3600,              # TTL: 1 hour
        result_persistent=True,
        # -------------------------------------------------------------------
        # I/O-bound optimisation
        # -------------------------------------------------------------------
        worker_prefetch_multiplier=1,     # one task at a time per greenlet
        # -------------------------------------------------------------------
        # Beat schedule (periodic tasks)
        # -------------------------------------------------------------------
        beat_schedule={
            # Example: sweep all providers every 30 minutes
            # "scrape-all-providers": {
            #     "task": "travel.worker.tasks.scrape_provider",
            #     "schedule": 1800.0,
            #     "args": ["booking.com", ...],
            # },
        },
        timezone="UTC",
        enable_utc=True,
    )

    return app


celery_app: Celery = create_celery_app()


# ---------------------------------------------------------------------------
# Worker lifecycle hooks — initialise/teardown per-process resources
# ---------------------------------------------------------------------------

@worker_process_init.connect
def init_worker(**kwargs: object) -> None:
    """Called once per worker process on startup."""
    logger.info("Celery worker process initialised.")


@worker_process_shutdown.connect
def shutdown_worker(**kwargs: object) -> None:
    """Called once per worker process on shutdown."""
    logger.info("Celery worker process shutting down.")
