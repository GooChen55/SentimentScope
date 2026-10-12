"""Upstream imports and configuration belong only to this isolated interpreter."""
import asyncio
import json
import sys
from pathlib import Path
from engine_runtime import install_weibo_adapter, write_failure

def main():
    request = json.load(sys.stdin)
    sys.path.insert(0, request["engine_path"])
    import config
    settings = {
        "PLATFORM": request["platform"], "KEYWORDS": ",".join(request["keywords"]),
        "LOGIN_TYPE": request["login_type"], "CRAWLER_TYPE": "search",
        "CRAWLER_MAX_NOTES_COUNT": request["max_notes"], "MAX_CONCURRENCY_NUM": 1,
        "HEADLESS": request["headless"], "ENABLE_CDP_MODE": request["cdp"],
        "DISABLE_SSL_VERIFY": False, "ENABLE_GET_COMMENTS": True,
        "CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES": 20,
        "ENABLE_GET_MEDIA": False, "ENABLE_GET_WORDCLOUD": False,
        "SAVE_DATA_OPTION": "jsonl", "SAVE_DATA_PATH": request["output_path"],
        "SAVE_LOGIN_STATE": True,
        "USER_DATA_DIR": str(Path(request["profile_root"]) / "%s_user_data_dir"),
    }
    for key, value in settings.items():
        setattr(config, key, value)
    from main import CrawlerFactory
    install_weibo_adapter(CrawlerFactory)
    from var import crawler_type_var
    crawler_type_var.set("search")
    async def crawl():
        crawler = CrawlerFactory.create_crawler(request["platform"])
        try:
            await crawler.start()
        except BaseException as error:
            write_failure(request["output_path"], error)
            raise
        finally:
            cdp = getattr(crawler, "cdp_manager", None)
            context = getattr(crawler, "browser_context", None)
            try:
                if cdp:
                    await cdp.cleanup(force=True)
                elif context:
                    await context.close()
            except Exception:
                # Cleanup must not replace the original diagnosis.
                pass
    asyncio.run(crawl())

if __name__ == "__main__":
    main()
