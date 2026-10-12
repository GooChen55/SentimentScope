import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.dependencies import ResearchServiceDep

router = APIRouter(prefix="/api/events", tags=["实时事件"])


@router.get("/stream")
async def stream(request: Request, service: ResearchServiceDep, research_id: str | None = None):
    service.activate()
    queue = asyncio.Queue(maxsize=256)
    service.subscribers.add(queue)

    async def events():
        try:
            yield 'event: connected\ndata: {"connected":true}\n\n'
            if research_id:
                try:
                    after = max(0, int(request.headers.get("last-event-id", "0") or 0))
                except ValueError:
                    after = 0
                for event in service.store.events(research_id, after):
                    yield f"id: {event['id']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            while not await request.is_disconnected():
                try:
                    event = await asyncio.wait_for(queue.get(), 15)
                    if not research_id or event["data"].get("research_id") == research_id:
                        yield f"id: {event['id']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            service.subscribers.discard(queue)

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
