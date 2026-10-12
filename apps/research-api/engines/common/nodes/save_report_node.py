"""公共基础设施模块：engines/common/nodes/save_report_node.py。"""
from typing import Any
from loguru import logger
from engines.common.io.report_io import save_md_report
from engines.common.nodes.base_node import BaseNode
from engines.contracts.roles import ROLE_INFOS
from engines.insight_agent.state import InsightState




class SaveReportNode(BaseNode):
    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """负责将最终生成的 Markdown 报告持久化到文件系统中。"""
        # 1. 提取基础信息用于构建日志
        role = state.get("role")
        info = ROLE_INFOS.get(role)
        agent_name = info.display_name
        title = state.get("report_title")

        logger.info(f"开始执行报告落盘 [{agent_name}]，准备保存报告: '{title}'...")

        # 2. 防御性检查：确保真的有报告内容可以保存
        final_report = state.get("final_report")
        if not final_report:
            logger.error(f"[{agent_name}] 状态机中缺失 final_report 数据，跳过落盘流程。")
            return {}

        # 3. 执行文件写入
        try:
            md_path = save_md_report(
                self.context.output_dir,
                role,
                state.get("query") or title,
                final_report
            )
            # 标志着整个 InsightAgent 结束
            logger.info(f"报告落盘完成 [{agent_name}],文件已成功保存至: {md_path}")
            return {}
        except Exception as exc:
            logger.error(f"[{agent_name}] 报告落盘失败，出现异常: {exc}")
            raise
