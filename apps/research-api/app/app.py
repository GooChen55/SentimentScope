from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.routers import config, research, report, host, events
from app.dependencies import get_research_service, get_report_service


# 定义lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_research_service().activate()
        # 初始化资源动作
        yield  # FASTAPI处理路由
    finally:
        # 应用关闭的时候，清理资源
        await get_research_service().close()
        await get_report_service().close()
        from engines.insight_agent.tools.connection import close_async_engine
        await close_async_engine()


app = FastAPI(title="SentimentScope · 研究 API", description="舆情研判平台的研究编排、证据、讨论与报告服务", lifespan=lifespan)

# app配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由

app.include_router(config.router)
app.include_router(research.router)
app.include_router(report.router)
app.include_router(host.router)
app.include_router(events.router)


@app.get("/health", tags=["健康检查"])
def health():
    return {"status": "ok"}
