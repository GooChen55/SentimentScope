from typing import Optional, Literal
from pathlib import Path
from pydantic import Field
from functools import  lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

from engines.contracts.paths import SERVICE_ROOT, DATA_ROOT, ENV_FILE
PROJECT_ROOT: Path = SERVICE_ROOT


class Settings(BaseSettings):
    # ================== 服务器 ==================
    HOST: str = Field("0.0.0.0", description="监听地址")
    PORT: int = Field(5001, description="监听端口")

    # ================== 舆情库==================
    DB_DIALECT: str = Field("mysql", description="数据库类型:mysql 或 postgresql")
    DB_HOST: str = Field("localhost", description="数据库主机")
    DB_PORT: int = Field(3306, description="数据库端口")
    DB_USER: str = Field("root", description="数据库用户名")
    DB_PASSWORD: str = Field("", description="数据库密码")
    DB_NAME: str = Field("media_crawler", description="数据库名称")
    DB_CHARSET: str = Field("utf8mb4", description="字符集")

    # ================== insight 研究角色 LLM信息 ==================
    INSIGHT_ENGINE_API_KEY: Optional[str] = Field(None, description="Insight 角色 API 密钥")
    INSIGHT_ENGINE_BASE_URL: Optional[str] = Field("https://api.moonshot.cn/v1", description="Insight 角色 BaseUrl")
    INSIGHT_ENGINE_MODEL_NAME: str = Field("kimi-k2-0711-preview", description="Insight 角色模型名")
    INSIGHT_ENGINE_MODEL_PROVIDER: str = Field("openai", description="Insight 角色厂商(langchain provider)")

    # ================== media 研究角色 LLM信息==================
    MEDIA_ENGINE_API_KEY: Optional[str] = Field(None, description="Media 角色 API 密钥")
    MEDIA_ENGINE_BASE_URL: Optional[str] = Field("https://aihubmix.com/v1", description="Media 角色 BaseUrl")
    MEDIA_ENGINE_MODEL_NAME: str = Field("gemini-2.5-pro", description="Media 角色模型名")
    MEDIA_ENGINE_MODEL_PROVIDER: str = Field("openai", description="Media 角色厂商(langchain provider)")

    # ================== 报告引擎  LLM信息==================
    REPORT_ENGINE_API_KEY: Optional[str] = Field(None, description="报告引擎 API 密钥")
    REPORT_ENGINE_BASE_URL: Optional[str] = Field("https://aihubmix.com/v1", description="报告引擎 BaseUrl")
    REPORT_ENGINE_MODEL_NAME: str = Field("gemini-2.5-pro", description="报告引擎模型名")
    REPORT_ENGINE_MODEL_PROVIDER: str = Field("openai", description="报告引擎厂商(langchain provider)")

    # ================== HostAgent LLM信息 ==================
    HOST_API_KEY: Optional[str] = Field(None, description="HostAgent API 密钥")
    HOST_BASE_URL: Optional[str] = Field(None, description="HostAgent BaseUrl")
    HOST_MODEL_NAME: Optional[str] = Field(None, description="HostAgent 模型名")
    HOST_MODEL_PROVIDER: str = Field("openai", description="HostAgent 厂商(langchain provider)")

    # ================== Web 搜索 ==================
    SEARCH_SWITCH: Literal["TavilyAPI", "AnspireAPI", "BochaAPI"] = Field(
        "TavilyAPI", description="Web 搜索提供方"
    )
    TAVILY_API_KEY: Optional[str] = Field(None, description="Tavily API 密钥")
    BOCHA_BASE_URL: Optional[str] = Field("https://api.bocha.cn/v1/ai-search", description="Bocha BaseUrl")
    BOCHA_API_KEY: Optional[str] = Field(None, description="Bocha API 密钥")
    ANSPIRE_BASE_URL: Optional[str] = Field(
        "https://plugin.anspire.cn/api/ntsearch/search", description="Anspire BaseUrl"
    )
    ANSPIRE_API_KEY: Optional[str] = Field(None, description="Anspire API 密钥")

    # ================== 研究引擎 ==================
    MAX_SECTIONS: int = Field(5, description="报告最大章节数")
    SEARCH_TIMEOUT: int = Field(240, description="单次搜索请求超时(秒)")
    SEARCH_CONTENT_MAX_LENGTH: int = Field(20000, description="供 LLM 的搜索结果最大长度")
    MAX_CONTENT_LENGTH: int = Field(500000, description="搜索最大内容长度")
    OUTPUT_DIR: str = Field(str(DATA_ROOT / "report"), description="报告输出目录")
    HOST_REPORT_DIR: str = Field(str(DATA_ROOT / "report/host"), description="Host 研判报告输出目录")
    INSIGHT_REPORT_DIR: str = Field(str(DATA_ROOT / "report/insight"), description="Insight 研究报告输出目录")
    MEDIA_REPORT_DIR: str = Field(str(DATA_ROOT / "report/media"), description="Media 研究报告输出目录")

    # ================== Insight 向量检索、聚类==================
    INSIGHT_VECTOR_ENABLED: bool = Field(False, description="是否为 InsightAgent 启用 Milvus 向量检索")
    MILVUS_URI: str = Field("http://localhost:19530", description="Milvus 服务器地址(URI)")
    MILVUS_DB_NAME: str = Field("default", description="Milvus 数据库名称")
    MILVUS_INSIGHT_COLLECTION: str = Field("insight_evidence", description="Insight 证据集合(Collection)名称")
    INSIGHT_EMBEDDING_MODEL: str = Field("BAAI/bge-m3", description="Insight 检索所使用的 Embedding 模型名称/路径")
    INSIGHT_EMBEDDING_DEVICE: Optional[str] = Field(None, description="Embedding 模型运行设备，例如 'cuda' 或 'cpu'")
    INSIGHT_DENSE_DIM: int = Field(1024, description="BGE-M3 稠密向量维度")
    INSIGHT_VECTOR_TOP_K: int = Field(80, description="Milvus 每个检索通道的召回数量(Top K)")
    INSIGHT_VECTOR_FILTER_DAYS: int = Field(365, description="Milvus 检索的时间窗口天数限制；小于等于0则禁用时间过滤")
    INSIGHT_SYNC_BATCH_SIZE: int = Field(64, description="Milvus 批量计算 Embedding 和数据上载(Upsert)的批次大小")
    INSIGHT_CLUSTERING_ENABLED: bool = Field(True, description="是否为 InsightAgent 启用语义聚类")
    INSIGHT_CLUSTER_MODEL: Optional[str] = Field(None, description="用于语义聚类的 SentenceTransformer 模型路径或名称")
    INSIGHT_CLUSTER_MAX_RECORDS: int = Field(100, description="用于语义聚类的最大证据记录条数限制")
    INSIGHT_CLUSTER_MAX_CLUSTERS: int = Field(10, description="最大允许划分的语义聚类簇数，桶的数量")
    INSIGHT_CLUSTER_MIN_CLUSTER_SIZE: int = Field(5, description="期望的最小语义聚类簇大小，桶的记录数量")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_prefix="",
        case_sensitive=False,
        extra="allow",
    )





@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（带缓存）"""
    return Settings()




def reload_settings():
    """清理配置缓存以触发热更新"""
    get_settings.cache_clear()

    return get_settings()
