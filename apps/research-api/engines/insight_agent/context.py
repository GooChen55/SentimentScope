from typing import Callable
from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate


class InsightContext:
    def __init__(
            self,
            role: str,
            llm_client: LLMClient,
            output_dir: str,
            progress_callback: Callable[[ProgressUpdate], None] | None,
    ) -> None:
        self.role = role
        self.llm_client = llm_client
        self.output_dir = output_dir
        self.progress_callback = progress_callback
