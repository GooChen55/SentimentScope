# -*- coding: utf-8 -*-
"""平台信息路由"""

from fastapi import APIRouter

from app.config import (
    SUPPORTED_PLATFORMS,
    DEFAULT_MAX_KEYWORDS,
    DEFAULT_MAX_NOTES,
    DEFAULT_LOGIN_TYPE,
)
from app.web.schemas import PlatformInfo, ConfigOptions

router = APIRouter(prefix="/api", tags=["platforms"])

_PLATFORM_LABELS: dict[str, str] = {
    "xhs": "小红书",
    "dy": "抖音",
    "ks": "快手",
    "bili": "B站",
    "wb": "微博",
    "tieba": "贴吧",
    "zhihu": "知乎",
}

_PLATFORM_DESCRIPTIONS: dict[str, str] = {
    "xhs": "美妆、生活、时尚内容为主，图文笔记+短视频",
    "dy": "短视频、娱乐、生活内容，算法推荐流量大",
    "ks": "生活、娱乐、农村题材内容，社区氛围浓厚",
    "bili": "科技、学习、游戏、动漫内容，中长视频为主",
    "wb": "热点新闻、明星、社会话题，热搜榜单实时更新",
    "tieba": "兴趣讨论、游戏、学习，社区化板块",
    "zhihu": "知识问答、深度讨论，高质量内容社区",
}

_LOGIN_TYPES = [
    {"value": "qrcode", "label": "二维码扫码登录"},
    {"value": "phone", "label": "手机验证码登录"},
    {"value": "cookie", "label": "Cookie 登录"},
]


@router.get("/platforms", response_model=list[PlatformInfo])
async def list_platforms():
    return [
        PlatformInfo(
            value=p,
            label=_PLATFORM_LABELS.get(p, p),
            description=_PLATFORM_DESCRIPTIONS.get(p, ""),
        )
        for p in SUPPORTED_PLATFORMS
    ]


@router.get("/config/options", response_model=ConfigOptions)
async def get_config_options():
    return ConfigOptions(
        login_types=_LOGIN_TYPES,
        default_max_keywords=DEFAULT_MAX_KEYWORDS,
        default_max_notes=DEFAULT_MAX_NOTES,
        default_login_type=DEFAULT_LOGIN_TYPE,
        supported_platforms=[
            PlatformInfo(
                value=p,
                label=_PLATFORM_LABELS.get(p, p),
                description=_PLATFORM_DESCRIPTIONS.get(p, ""),
            )
            for p in SUPPORTED_PLATFORMS
        ],
    )
