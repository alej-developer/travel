"""Playwright SessionManager — injects randomized, coherent browser fingerprints.

Each ``BrowserSession`` encapsulates a Playwright ``BrowserContext`` configured with:
- A randomly-selected, realistic User-Agent string
- Matching ``navigator`` JS overrides (platform, vendor, languages, hardware)
- Canvas fingerprint noise (small random pixel perturbations)
- WebGL renderer/vendor spoofing
- playwright-stealth patches to remove all Playwright automation signals

The session is designed to be created once per scraping task and disposed after use.

Usage
-----
    async with SessionManager(playwright) as session:
        page = await session.new_page()
        await page.goto("https://www.booking.com")
"""
from __future__ import annotations

import random
import secrets
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright
from playwright_stealth import Stealth  # type: ignore[import-untyped]

from travel.config import get_settings

# ---------------------------------------------------------------------------
# Fingerprint data pools
# ---------------------------------------------------------------------------

_USER_AGENTS: list[str] = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:128.0) Gecko/20100101 Firefox/128.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
]

_PLATFORMS: dict[str, str] = {
    "Windows": "Win32",
    "macOS": "MacIntel",
    "Linux": "Linux x86_64",
}

_WEBGL_RENDERERS: list[dict[str, str]] = [
    {"renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)", "vendor": "Google Inc. (NVIDIA)"},
    {"renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)", "vendor": "Google Inc. (Intel)"},
    {"renderer": "ANGLE (AMD, Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)", "vendor": "Google Inc. (AMD)"},
    {"renderer": "Apple GPU", "vendor": "Apple"},
]

_LOCALES: list[str] = ["es-ES", "en-US", "en-GB", "de-DE", "fr-FR", "it-IT"]

_TIMEZONES: list[str] = [
    "Europe/Madrid", "America/New_York", "Europe/London",
    "Europe/Berlin", "America/Chicago",
]

_SCREEN_SIZES: list[dict[str, int]] = [
    {"width": 1920, "height": 1080},
    {"width": 2560, "height": 1440},
    {"width": 1680, "height": 1050},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
]


# ---------------------------------------------------------------------------
# Fingerprint dataclass
# ---------------------------------------------------------------------------

@dataclass
class BrowserFingerprint:
    """A coherent, randomized set of browser fingerprint attributes."""

    user_agent: str = field(default_factory=lambda: random.choice(_USER_AGENTS))
    platform: str = field(default_factory=lambda: random.choice(list(_PLATFORMS.values())))
    locale: str = field(default_factory=lambda: random.choice(_LOCALES))
    timezone_id: str = field(default_factory=lambda: random.choice(_TIMEZONES))
    screen: dict[str, int] = field(
        default_factory=lambda: random.choice(_SCREEN_SIZES)
    )
    webgl: dict[str, str] = field(
        default_factory=lambda: random.choice(_WEBGL_RENDERERS)
    )
    # Small canvas noise seed (0-255) — each session gets unique noise
    canvas_noise_seed: int = field(
        default_factory=lambda: secrets.randbelow(256)
    )
    hardware_concurrency: int = field(
        default_factory=lambda: random.choice([4, 6, 8, 12, 16])
    )
    device_memory: int = field(
        default_factory=lambda: random.choice([4, 8, 16, 32])
    )

    @property
    def viewport(self) -> dict[str, int]:
        # Slight randomisation of viewport vs screen (common in real browsers)
        return {
            "width": self.screen["width"] - random.randint(0, 100),
            "height": self.screen["height"] - random.randint(60, 120),
        }


# ---------------------------------------------------------------------------
# JS injection scripts
# ---------------------------------------------------------------------------

def _build_fingerprint_script(fp: BrowserFingerprint) -> str:
    """Return a JS snippet that overrides navigator / WebGL / Canvas APIs."""
    return f"""
    (() => {{
      // ── Navigator overrides ─────────────────────────────────────────────
      Object.defineProperty(navigator, 'platform', {{
        get: () => '{fp.platform}',
      }});
      Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {fp.hardware_concurrency},
      }});
      Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {fp.device_memory},
      }});
      Object.defineProperty(navigator, 'languages', {{
        get: () => ['{fp.locale}', 'en'],
      }});

      // ── WebGL renderer / vendor spoofing ────────────────────────────────
      const getParam = WebGLRenderingContext.prototype.getParameter;
      WebGLRenderingContext.prototype.getParameter = function(param) {{
        if (param === 37445) return '{fp.webgl["vendor"]}';   // UNMASKED_VENDOR_WEBGL
        if (param === 37446) return '{fp.webgl["renderer"]}'; // UNMASKED_RENDERER_WEBGL
        return getParam.call(this, param);
      }};
      const getParam2 = WebGL2RenderingContext.prototype.getParameter;
      WebGL2RenderingContext.prototype.getParameter = function(param) {{
        if (param === 37445) return '{fp.webgl["vendor"]}';
        if (param === 37446) return '{fp.webgl["renderer"]}';
        return getParam2.call(this, param);
      }};

      // ── Canvas noise ────────────────────────────────────────────────────
      // Add imperceptible noise to canvas pixel data per session
      const seed = {fp.canvas_noise_seed};
      const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
      HTMLCanvasElement.prototype.toDataURL = function(...args) {{
        const ctx = this.getContext('2d');
        if (ctx) {{
          const imageData = ctx.getImageData(0, 0, this.width, this.height);
          for (let i = 0; i < imageData.data.length; i += 4) {{
            imageData.data[i]   = Math.min(255, imageData.data[i]   + (seed % 3));
            imageData.data[i+1] = Math.min(255, imageData.data[i+1] + ((seed >> 2) % 3));
          }}
          ctx.putImageData(imageData, 0, 0);
        }}
        return origToDataURL.apply(this, args);
      }};
    }})();
    """


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------

class BrowserSession:
    """A configured Playwright BrowserContext with anti-detection measures.

    Do not instantiate directly — use :class:`SessionManager` as a context manager.
    """

    def __init__(
        self,
        context: BrowserContext,
        fingerprint: BrowserFingerprint,
        proxy: str | None = None,
    ) -> None:
        self.context = context
        self.fingerprint = fingerprint
        self.proxy = proxy

    async def new_page(self) -> Page:
        """Open a new page with fingerprint script injected and stealth applied."""
        page = await self.context.new_page()
        await Stealth().apply_stealth_async(page)
        await page.add_init_script(_build_fingerprint_script(self.fingerprint))
        return page

    async def close(self) -> None:
        await self.context.close()


class SessionManager:
    """Factory + context manager for Playwright BrowserSessions.

    Parameters
    ----------
    playwright:
        The ``Playwright`` instance (from ``async_playwright().start()``).
    proxy:
        Optional proxy URL to use for the browser context.
        E.g. ``"socks5://user:pass@host:1080"``.
    fingerprint:
        Optional explicit fingerprint; if None a random one is generated.

    Example
    -------
    ::

        async with async_playwright() as pw:
            async with SessionManager(pw, proxy="socks5://...") as session:
                page = await session.new_page()
                await page.goto("https://www.booking.com")
    """

    def __init__(
        self,
        playwright: Playwright,
        proxy: str | None = None,
        fingerprint: BrowserFingerprint | None = None,
    ) -> None:
        self._playwright = playwright
        self._proxy = proxy
        self._fingerprint = fingerprint or BrowserFingerprint()
        self._browser: Browser | None = None
        self._session: BrowserSession | None = None

    async def __aenter__(self) -> BrowserSession:
        fp = self._fingerprint
        proxy_config: dict[str, Any] | None = (
            {"server": self._proxy} if self._proxy else None
        )

        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--window-size={fp.screen['width']},{fp.screen['height']}",
            ],
        )
        context = await self._browser.new_context(
            user_agent=fp.user_agent,
            viewport=fp.viewport,
            locale=fp.locale,
            timezone_id=fp.timezone_id,
            proxy=proxy_config,
            # Avoid WebRTC leaks
            java_script_enabled=True,
            ignore_https_errors=False,
        )
        self._session = BrowserSession(context, fp, self._proxy)
        return self._session

    async def __aexit__(self, *_: object) -> None:
        if self._session:
            await self._session.close()
        if self._browser:
            await self._browser.close()
