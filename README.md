# Travel Aggregation Engine

Backend distribuido de agregación de viajes con motor de scraping asíncrono anti-bot.

## Stack

| Capa | Tecnología |
|------|-----------|
| API | FastAPI + Pydantic v2 |
| DB | PostgreSQL 16 + SQLAlchemy 2.0 async + asyncpg |
| Migraciones | Alembic |
| Scraping | Playwright async + playwright-stealth |
| Cola de tareas | Celery 5 + Redis 7 (broker) |
| Resiliencia | Circuit Breaker (Redis) + Proxy pool |
| Tipado | mypy strict mode |

## Arquitectura

```
src/travel/
├── domain/          # Entidades puras (dataclasses) + interfaces repositorio (ABCs)
├── application/     # Esquemas Pydantic v2 (DTOs)
├── infrastructure/
│   ├── database/    # Engine async, session factory, DeclarativeBase
│   ├── models/      # Modelos SQLAlchemy (Flight, Train, Accommodation)
│   └── scraping/    # Motor de scraping distribuido
│       ├── circuit_breaker.py   # Circuit Breaker Redis
│       ├── session_manager.py   # Playwright + fingerprint injection
│       ├── network_middleware.py # Bloqueo recursos + detección 429
│       ├── proxy_pool.py        # Rotación de proxies residenciales
│       ├── scraper_factory.py   # Factory de estrategias
│       └── providers/           # Booking, Airbnb, Renfe, Iberia
├── presentation/    # FastAPI routers + DI de sesiones DB
└── worker/
    ├── celery_app.py  # Configuración Celery (gevent pool, I/O-bound)
    └── tasks.py       # Tareas: scrape_provider, scrape_all_providers
```

## Inicio rápido

```bash
# 1. Infraestructura (PostgreSQL + Redis)
docker compose up -d postgres redis

# 2. Entorno Python
python -m pip install -e ".[dev]"
playwright install chromium

# 3. Variables de entorno
cp .env.example .env   # Editar DATABASE_URL, PROXY_LIST, etc.

# 4. Migraciones
alembic upgrade head

# 5. API
uvicorn travel.presentation.app:app --reload

# 6. Worker Celery (en otra terminal)
celery -A travel.worker.celery_app worker --pool=gevent --concurrency=20 -l INFO
```

## Tests

```bash
pytest tests/ -v
```

## Circuit Breaker

El Circuit Breaker se activa automáticamente:
- **3 errores 429 consecutivos** → dominio pausado 15 minutos en Redis
- Las claves Redis tienen TTL automático: el circuito se auto-cierra sin intervención manual
- Estado inspectable: `CircuitBreaker.get_state()`

## ScraperFactory

```python
from travel.infrastructure.scraping.scraper_factory import ScraperFactory

# Por dominio
scraper = ScraperFactory.create("booking.com")

# Por URL completa
scraper = ScraperFactory.from_url("https://www.iberia.com/vuelos-baratos/mad-bcn/")

# Registrar nuevo proveedor dinámicamente
ScraperFactory.register("nuevoproveedor.com", NuevoProveedorScraper)
```

## Lanzar scrape distribuido

```python
from travel.worker.tasks import scrape_all_providers

result = scrape_all_providers.delay({
    "origin": "MAD",
    "destination": "BCN",
    "departure_date": "2025-09-01",
    "return_date": "2025-09-08",
    "adults": 2,
})
```
