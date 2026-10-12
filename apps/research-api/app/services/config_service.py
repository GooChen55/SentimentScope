import os
from typing import Any
from pathlib import Path
from dotenv import set_key
from engines.contracts.config import get_settings, reload_settings, Settings, ENV_FILE

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_KEYS = [
    "DB_HOST", "DB_PORT", "DB_USER", "DB_NAME", "DB_PASSWORD",
    "INSIGHT_ENGINE_API_KEY", "INSIGHT_ENGINE_BASE_URL", "INSIGHT_ENGINE_MODEL_NAME", "INSIGHT_ENGINE_MODEL_PROVIDER",
    "MEDIA_ENGINE_API_KEY", "MEDIA_ENGINE_BASE_URL", "MEDIA_ENGINE_MODEL_NAME", "MEDIA_ENGINE_MODEL_PROVIDER",
    "REPORT_ENGINE_API_KEY", "REPORT_ENGINE_BASE_URL", "REPORT_ENGINE_MODEL_NAME", "REPORT_ENGINE_MODEL_PROVIDER",
    "HOST_API_KEY", "HOST_BASE_URL", "HOST_MODEL_NAME", "HOST_MODEL_PROVIDER",
    "SEARCH_TOOL_TYPE", "TAVILY_API_KEY", "BOCHA_API_KEY", "BOCHA_BASE_URL",
    "ANSPIRE_API_KEY", "ANSPIRE_BASE_URL"
]


class ConfigService:

    def read_config_info(self) -> dict[str, Any]:
        """
        返回Settings实例对象的属性
        :return:
        """

        current_config = get_settings()

        return {
            key: ("********" if getattr(current_config, key, None) and (key.endswith("API_KEY") or key == "DB_PASSWORD")
                  else str(getattr(current_config, "SEARCH_SWITCH" if key == "SEARCH_TOOL_TYPE" else key, None) or ""))
            for key in CONFIG_KEYS
        }

    def update_config_info(self, update_info: dict[str, Any]):
        """将更新写入 .env 并触发全局热加载。"""
        env_file_path = ENV_FILE

        if set(update_info) - set(CONFIG_KEYS):
            raise ValueError("包含不允许修改的配置字段")
        changes = {}
        for key, value in update_info.items():
            if not isinstance(value, (str, int)):
                raise ValueError("配置值必须为文本或整数")
            if str(value) == '********' and (key.endswith('API_KEY') or key == 'DB_PASSWORD'):
                continue
            changes['SEARCH_SWITCH' if key == 'SEARCH_TOOL_TYPE' else key] = str(value)
        Settings.model_validate({**get_settings().model_dump(), **changes})

        # python-dotenv 的 set_key 自动处理读取、转义、写入和追加
        for key, value in changes.items():
            set_key(env_file_path, key, str(value))
            os.environ[key] = value  # 保险(两次同步 environ>.env)

        # 触发热更新
        reload_settings()
        return self.read_config_info()
