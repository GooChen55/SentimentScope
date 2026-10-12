import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines.common.llm.llm_client import LLMClient


async def check(role):
    client = LLMClient.from_role(role)
    client.timeout = 60
    try:
        # 思考型模型会优先消耗思维链 token，max_tokens 过小会让 content 为空而误判为不可用。
        model = client._build_chat_model(False, max_tokens=512)
        result = await asyncio.wait_for(model.ainvoke('仅回复 OK'), 90)
        text = (getattr(result, 'text', '') or '').strip()
        print(role, 'reachable' if text else 'reachable-empty-content', text[:20])
    except Exception as exc:
        # Do not print HTTP exception URLs or request headers containing keys.
        print(role, 'failed', type(exc).__name__, getattr(exc, 'status_code', None))

async def main():
    await asyncio.gather(*(check(role) for role in ('insight', 'media', 'host')))

asyncio.run(main())
