"""HostAgent 主持人 LLM 研判:章节配对裁决 + 最终报告生成。"""

import json
from dataclasses import dataclass, field

from engines.common.llm.llm_client import LLMClient
from engines.common.runtime.call_retry import with_graceful_retry
from engines.host_agent import prompts
from engines.common.llm.llm_output import sanitize_markdown
from engines.host_agent.schemas import SectionJudgement, SectionPair, SectionResult

from langchain_core.prompts import PromptTemplate


@dataclass(slots=True)
class Judge:
    llm: LLMClient = field(default_factory=lambda: LLMClient.from_role("host"))

    async def judge_section(
            self,
            pair: SectionPair,
            previous: list[SectionJudgement],
    ) -> SectionJudgement | None:
        content = await self._call_llm(
            prompts.SYSTEM_PROMPT,
            PromptTemplate.from_template(prompts.SECTION_USER_PROMPT_TEMPLATE).format(
                evidence=self._build_section_evidence(pair, previous)
            )
        )
        if content is None:
            return None
        return SectionJudgement(section_key=pair.section_key, content=sanitize_markdown(content))

    async def generate_final_report(self, results: list[SectionJudgement]) -> str | None:
        content = await self._call_llm(
            prompts.FINAL_SYSTEM_PROMPT,
            PromptTemplate.from_template(prompts.FINAL_USER_PROMPT_TEMPLATE).format(
                evidence=self._build_final_evidence(results)
            ),
        )
        if content is None:
            return None
        return sanitize_markdown(content)

    def _build_section_evidence(self, pair: SectionPair, previous: list[SectionJudgement]) -> str:
        section_evidence = {
            "section": {"key": pair.section_key, "title": pair.title},
            "insight": self._extract_evidence(pair.insight),
            "media": self._extract_evidence(pair.media),
            "previous_host_judgements": [m.to_dict() for m in previous[-3:]],
        }
        return json.dumps(section_evidence, ensure_ascii=False)

    def _build_final_evidence(self, results: list[SectionJudgement]) -> str:
        return json.dumps([m.to_dict() for m in results], ensure_ascii=False)

    @staticmethod
    def _extract_evidence(result: SectionResult) -> dict:
        return {
            "title": result.title,
            "body": result.body[:5000],
            "hit_count": result.hit_count,
            "strength": result.strength,
        }

    @with_graceful_retry
    async def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str | None:
        content = await self.llm.generate_text(
            system_prompt, user_prompt, temperature=temperature
        )
        if not content:
            raise ValueError("返回空内容")
        return content
