"""HostAgent 维度配对存储。

职责:按 section_key 累积 insight/media 章节结果,同维度齐备即就绪配对;
已研判的维度拒绝重入,低质量重复按 _quality_score 过滤。
"""

from loguru import logger

from engines.contracts.dimensions import DIMENSIONS
from engines.host_agent.schemas import SectionPair, SectionResult

_STRENGTH_RANK = {"missing": 0, "weak": 1, "medium": 2, "strong": 3}
_REQUIRED_SOURCES = ("insight", "media")


class PairStore:
    """按 section_key 维度累积 insight/media 章节结果;同维度齐备即就绪配对。"""

    def __init__(self) -> None:
        self._results: dict[str, dict[str, SectionResult]] = {}
        self._done: set[str] = set()

    def add(self, result: SectionResult) -> bool:
        """入队;已研判或低质量重复返回 False。"""
        if self._is_done(result.section_key):
            logger.info(f"HostAgent: 忽略已研判章节结果 source={result.source} section_key={result.section_key}")
            return False
        if self._is_weaker_duplicate(result):
            logger.info(f"HostAgent: 忽略低质量重复章节结果 source={result.source} section_key={result.section_key}")
            return False
        self._store(result)
        logger.info(
            f"HostAgent: 章节结果已入队 section_key={result.section_key} sources={sorted(self._results[result.section_key])}")
        return True

    def ready_pairs(self) -> list[SectionPair]:
        """返回所有 insight+media 齐备且未研判的维度配对,按 DIMENSION_KEYS 固定顺序。"""
        return [self._build_pair(key) for key in DIMENSIONS.keys() if self._is_ready(key)]

    def mark_done(self, section_key: str) -> None:
        self._done.add(section_key)
        logger.info(f"HostAgent: 章节研判完成 section_key={section_key}")

    def all_done(self) -> bool:
        return self._done.issuperset(DIMENSIONS.keys())

    def clear(self) -> None:
        self._results.clear()
        self._done.clear()

    def _is_done(self, section_key: str) -> bool:
        return section_key in self._done

    def _is_weaker_duplicate(self, result: SectionResult) -> bool:
        existing = self._results.get(result.section_key, {}).get(result.source)
        return existing is not None and _quality_score(existing) >= _quality_score(result)

    def _is_ready(self, section_key: str) -> bool:
        bucket = self._results.get(section_key, {})
        return section_key not in self._done and all(source in bucket for source in _REQUIRED_SOURCES)

    def _store(self, result: SectionResult) -> None:
        self._results.setdefault(result.section_key, {})[result.source] = result

    def _build_pair(self, section_key: str) -> SectionPair:
        bucket = self._results[section_key]
        return SectionPair(
            section_key=section_key,
            title=DIMENSIONS[section_key].title,
            insight=bucket["insight"],
            media=bucket["media"],
        )


def _quality_score(result: SectionResult) -> tuple[int, int, int]:
    """章节结果质量评分:证据强度 > 命中数 > 正文长度。"""
    return (
        _STRENGTH_RANK.get(result.strength, 0),
        result.hit_count,
        len(result.body),
    )


if __name__ == '__main__':
    _done = { "heat_and_spread", "sentiment_and_opinion", "platform_and_group_diff",
             "deep_causes_and_impact"}
    print(_done.issuperset(DIMENSIONS.keys()))
