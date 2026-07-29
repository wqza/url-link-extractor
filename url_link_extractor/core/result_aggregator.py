"""ResultAggregator 结果汇总（spec.md §5.3.1/§5.3.3、设计 §2.1.3 事务设计）。

职责：排序、统计计算（守恒校验）、异常聚合。
"""

from __future__ import annotations

from ..models.enums import ErrorCode, RecordStatus, SortBy
from ..models.result import ErrorReportItem, ExtractStatistics, LinkTitleRecord


class ResultAggregator:
    """结果汇总器。"""

    def aggregate(
        self,
        records: list[LinkTitleRecord],
        errors: list[ErrorReportItem],
        sort_by: SortBy = SortBy.URL,
    ) -> tuple[list[LinkTitleRecord], ExtractStatistics, list[ErrorReportItem], list[ErrorReportItem]]:
        """聚合结果：排序 + 统计 + 异常合并 + 守恒校验。"""
        sorted_records = self._sort(records, sort_by)
        statistics = self._compute_stats(records)
        merged_errors = list(errors)
        warnings = self._check_consistency(records, statistics)
        return sorted_records, statistics, merged_errors, warnings

    def _sort(self, records: list[LinkTitleRecord], sort_by: SortBy) -> list[LinkTitleRecord]:
        if sort_by == SortBy.URL:
            return sorted(records, key=lambda r: r.url)
        if sort_by == SortBy.TITLE:
            return sorted(records, key=lambda r: (r.title is None, r.title or ""))
        return list(records)

    def _compute_stats(self, records: list[LinkTitleRecord]) -> ExtractStatistics:
        total = len(records)
        success = sum(1 for r in records if r.status == RecordStatus.SUCCESS)
        no_title = sum(1 for r in records if r.status == RecordStatus.NO_TITLE)
        failed = sum(1 for r in records if r.status == RecordStatus.FAILED)
        return ExtractStatistics(total=total, success=success, no_title=no_title, failed=failed)

    def _check_consistency(
        self, records: list[LinkTitleRecord], stats: ExtractStatistics
    ) -> list[ErrorReportItem]:
        warnings: list[ErrorReportItem] = []
        if not stats.is_consistent():
            warnings.append(
                ErrorReportItem(
                    url="",
                    error_code=ErrorCode.STATS_INCONSISTENT,
                    detail=f"统计守恒破坏：total={stats.total} != {stats.success + stats.no_title + stats.failed}",
                )
            )
        return warnings
