from typing import Literal
from dataclasses import dataclass
from engines.insight_agent.prompts import FORMAT_SYSTEM_PROMPT_TEMPLATE
from engines.media_agent.prompts import SYSTEM_PROMPT_FORMAT

ROLE_KEY: Literal["insight", "media", "report", "host"]


@dataclass
class RoleInfo:
    config_prefix: str
    display_name: str
    format_system_prompt: str = ""


ROLE_INFOS: dict[str, RoleInfo] = {

    "insight": RoleInfo(
        config_prefix="INSIGHT_ENGINE",
        display_name="私域检索智能体专家",
        format_system_prompt=FORMAT_SYSTEM_PROMPT_TEMPLATE
    ),
    "media": RoleInfo(
        config_prefix="MEDIA_ENGINE",
        display_name="公域检索智能体专家",
        format_system_prompt=SYSTEM_PROMPT_FORMAT

    ),
    "report": RoleInfo(
        config_prefix="REPORT_ENGINE",
        display_name="报告引擎智能体专家"
    ),
    "host": RoleInfo(
        config_prefix="HOST",
        display_name="研判智能体专家"
    )

}


def role_display_name(role: str) -> str:
    info = ROLE_INFOS.get(role)
    return info.display_name
