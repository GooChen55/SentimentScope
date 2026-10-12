"""Local runtime adapters; the pinned upstream source remains untouched."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from types import MethodType

def install_empty_comments_adapter(client, fetch_error_type):
    from tenacity import retry, stop_after_attempt, wait_fixed
    original = client.request
    raw_request = getattr(original, "__wrapped__", None)
    if raw_request is None:
        raise RuntimeError("微博客户端接口不匹配，无法安装评论适配器")

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(3))
    async def comments_request(self, method, url, **kwargs):
        try:
            return await raw_request(self, method, url, **kwargs)
        except fetch_error_type as exc:
            if str(exc).startswith("暂无评论"):
                return {"data": [], "max_id": 0, "max_id_type": 0}
            raise

    async def request(self, method, url, **kwargs):
        parsed = urlsplit(url)
        if method.upper() == "GET" and parsed.hostname == "m.weibo.cn" and parsed.path == "/comments/hotflow":
            return await comments_request(self, method, url, **kwargs)
        return await original(method, url, **kwargs)
    client.request = MethodType(request, client)
    return client

class BundledChromium:
    """Use the browser installed for this Playwright version, not system Chrome."""
    def __init__(self, browser_type):
        self.browser_type = browser_type

    def __getattr__(self, name):
        return getattr(self.browser_type, name)

    async def launch(self, **kwargs):
        kwargs.pop("channel", None)
        return await self.browser_type.launch(**kwargs)

    async def launch_persistent_context(self, **kwargs):
        kwargs.pop("channel", None)
        return await self.browser_type.launch_persistent_context(**kwargs)

def install_weibo_adapter(factory):
    original = factory.CRAWLERS["wb"]
    class StableWeiboCrawler(original):
        async def launch_browser(self, chromium, playwright_proxy, user_agent, headless=True):
            return await super().launch_browser(BundledChromium(chromium), playwright_proxy, user_agent, headless)
        async def create_weibo_client(self, httpx_proxy):
            from media_platform.weibo.exception import DataFetchError
            client = await super().create_weibo_client(httpx_proxy)
            return install_empty_comments_adapter(client, DataFetchError)
    factory.CRAWLERS["wb"] = StableWeiboCrawler

def failure_details(error):
    name = type(error).__name__
    if name == "TargetClosedError":
        return {"error_code": "browser_closed", "error": "采集浏览器连接已关闭，任务未完成。扫码后请保持采集浏览器打开，直到控制台显示完成；若未手动关闭，请重试以检查浏览器稳定性。"}
    if name == "RetryError":
        return {"error_code": "login_or_request_timeout", "error": "登录或平台请求多次重试仍未成功，请确认扫码授权完成及平台是否可正常访问。"}
    if name == "TimeoutError":
        return {"error_code": "browser_timeout", "error": "页面或登录等待超时，请检查网络和平台页面后重试。"}
    return {"error_code": "engine_failed", "error": f"采集引擎执行失败（{name}），详细诊断保存在本机日志。"}

def write_failure(output_path, error):
    details = failure_details(error)
    (Path(output_path) / "engine-status.json").write_text(json.dumps(details, ensure_ascii=False), encoding="utf-8")
    return details
