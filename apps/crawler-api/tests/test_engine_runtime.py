import importlib.util
from pathlib import Path
import json
import pytest

spec = importlib.util.spec_from_file_location("engine_runtime", Path(__file__).resolve().parents[1] / "tools/engine_runtime.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

@pytest.mark.asyncio
async def test_weibo_adapter_preserves_profile_and_uses_pinned_browser():
    class Browser:
        async def launch_persistent_context(self, **kwargs):
            self.kwargs = kwargs
            return "context"
    class Upstream:
        async def launch_browser(self, chromium, proxy, user_agent, headless=True):
            return await chromium.launch_persistent_context(user_data_dir="existing_profile", channel="chrome", headless=headless)
    class Factory:
        CRAWLERS = {"wb": Upstream}
    runtime.install_weibo_adapter(Factory)
    browser = Browser()
    assert await Factory.CRAWLERS["wb"]().launch_browser(browser, None, None, False) == "context"
    assert browser.kwargs == {"user_data_dir": "existing_profile", "headless": False}

def test_safe_browser_closed_diagnosis(tmp_path):
    TargetClosedError = type("TargetClosedError", (Exception,), {})
    details = runtime.write_failure(tmp_path, TargetClosedError("cookie=secret signed-url"))
    assert details["error_code"] == "browser_closed"
    assert "secret" not in json.dumps(details)
    assert json.loads((tmp_path / "engine-status.json").read_text(encoding="utf-8")) == details

@pytest.mark.asyncio
async def test_empty_comments_ends_after_one_request_and_search_is_unchanged():
    from tenacity import retry, stop_after_attempt
    class FetchError(Exception):
        pass
    class Client:
        calls = 0
        @retry(stop=stop_after_attempt(1))
        async def request(self, method, url, **kwargs):
            self.calls += 1
            if url.endswith("hotflow"):
                raise FetchError("暂无评论哦~快来抢沙发")
            return {"search": True}
    client = runtime.install_empty_comments_adapter(Client(), FetchError)
    assert await client.request("GET", "https://m.weibo.cn/comments/hotflow") == {"data": [], "max_id": 0, "max_id_type": 0}
    assert client.calls == 1
    assert await client.request("GET", "https://m.weibo.cn/api/search") == {"search": True}

@pytest.mark.asyncio
async def test_permission_denial_is_not_treated_as_no_comments():
    from tenacity import retry, stop_after_attempt
    class FetchError(Exception):
        pass
    class Client:
        @retry(stop=stop_after_attempt(1), reraise=True)
        async def request(self, method, url, **kwargs):
            raise FetchError("登录已失效")
    client = runtime.install_empty_comments_adapter(Client(), FetchError)
    with pytest.raises(FetchError):
        await client.request("GET", "https://m.weibo.cn/api/search")
