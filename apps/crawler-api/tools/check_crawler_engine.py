"""Run using upstream Python; smoke-test imports and browser without platform login."""
import asyncio
import sys
import os
from pathlib import Path
service_root = Path(__file__).resolve().parents[1]
manifest = __import__('json').loads((service_root / 'crawler-engine.lock.json').read_text(encoding='utf-8'))
engine_root = (service_root / manifest['directory']).resolve()
sys.path.insert(0, str(engine_root))
os.chdir(engine_root)
from main import CrawlerFactory
from playwright.async_api import async_playwright
from engine_runtime import install_weibo_adapter
from tempfile import TemporaryDirectory
import config

async def main():
    assert set(CrawlerFactory.CRAWLERS) == {"xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"}
    install_weibo_adapter(CrawlerFactory)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content("<html><title>Engine smoke test</title><body>Ready</body></html>")
            assert await page.title() == "Engine smoke test"
        finally:
            await browser.close()
        with TemporaryDirectory(prefix="sentiment-browser-probe-") as profile:
            config.SAVE_LOGIN_STATE = True
            config.PLATFORM = "wb"
            config.USER_DATA_DIR = str(Path(profile) / "%s")
            crawler = CrawlerFactory.create_crawler("wb")
            context = await crawler.launch_browser(p.chromium, None, None, headless=True)
            try:
                page = await context.new_page()
                await page.set_content("<title>Weibo adapter smoke test</title>")
                assert await page.title() == "Weibo adapter smoke test"
                crawler.browser_context = context
                crawler.context_page = page
                client = await crawler.create_weibo_client(None)
                assert client.request.__func__.__name__ == "request"
                print("PASS: actual Weibo persistent-browser adapter uses bundled Chromium")
            finally:
                await context.close()
    print("PASS: seven platform adapters import; pinned Playwright browser launches")

if __name__ == "__main__":
    asyncio.run(main())
