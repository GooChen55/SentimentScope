from typing import Any
from engines.insight_agent.state import InsightState
from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.insight_agent.tools.retrival_service import InsightRetrivalService
from engines.insight_agent.evidence_processor  import EvidencePool
from engines.common.io.evidence_io import save_evidence


class RetrievalNode(BaseNode):

    def __init__(self, context: ResearchNodeContext) -> None:
        super().__init__(context)  # 显示调用父类的构造函数

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """
        自动调用到__call__ 执行该节点
        :param state:
        :return:
        """

        # 1. 接收用户查询问题
        user_query = state['query']

        # 2. 调用检索服务
        retrival_service = InsightRetrivalService()
        evidence_records = await retrival_service.retrival_evidence(user_query)
        save_evidence('insight', evidence_records)

        evidence_pool = EvidencePool(
            query=user_query,
            records=evidence_records,
            clusters=[],
        )

        # 5. 返回
        return {"evidence_pool": evidence_pool}
