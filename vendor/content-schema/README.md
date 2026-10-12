# Content table compatibility schema

`models.py` 原样保留旧 MediaCrawler 的 SQLAlchemy 内容表定义，仅供采集 API 建表兼容使用，不执行爬取、登录或浏览器操作。

原出处：NanmiCoder/MediaCrawler 的 `database/models.py`；原文件版权头和 `LICENSE` 保留。完整旧源码归档于 `archive/legacy-mediacrawler/`；实际采集只使用 `vendor/mediacrawler/` 中固定提交的官方引擎。

业务代码通过 `apps/crawler-api/app/db/content_schema.py` 加载表元数据，禁止再把旧爬虫目录注入全局 Python 导入路径。
