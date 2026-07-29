"""结果领域对象（spec.md §6.2/§6.3/§6.4、设计 §2.3.2）。

包含：LinkTitleRecord / ExtractStatistics / ErrorReportItem / ExportOutcome / ExtractResult。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import ErrorCode, RecordStatus


@dataclass(frozen=True)
class LinkTitleRecord:
    """链接-标题记录（spec.md §6.2）。

    - url：绝对完整网页 URL（含协议、主机、完整路径）
    - title：规整后的标题文本；None 表示标题缺失（spec.md §6.2-2）
    - status：提取结果状态
    """

    url: str
    title: str | None
    status: RecordStatus


@dataclass(frozen=True)
class ExtractStatistics:
    """提取统计（spec.md §6.3）。

    约束：total = success + no_title + failed
    """

    total: int = 0
    success: int = 0
    no_title: int = 0
    failed: int = 0

    def is_consistent(self) -> bool:
        """校验统计守恒：total == success + no_title + failed。"""
        return self.total == self.success + self.no_title + self.failed


@dataclass(frozen=True)
class ErrorReportItem:
    """异常报告项（spec.md §6.4）。

    - url：发生异常的链接或入口地址（绝对完整 URL）
    - error_code：错误码枚举
    - detail：可选补充说明，不得包含正文敏感内容
    """

    url: str
    error_code: ErrorCode
    detail: str | None = None


@dataclass(frozen=True)
class ExportOutcome:
    """导出结果。

    - file_path：成功时为 result.xlsx 绝对路径；失败时为 None
    - error：失败时含 EXPORT_WRITE_ERROR 异常项；成功时为 None
    """

    file_path: str | None
    error: ErrorReportItem | None


@dataclass
class ExtractResult:
    """提取任务最终结果。

    - result_set：链接-标题记录列表（已排序、已去重）
    - statistics：提取统计
    - errors：异常报告列表
    - warnings：告警列表（如 STATS_INCONSISTENT）
    - task_id：任务标识，贯穿全链路日志
    - export_path：result.xlsx 绝对路径；未导出时为 None
    """

    result_set: list[LinkTitleRecord] = field(default_factory=list)
    statistics: ExtractStatistics = field(default_factory=ExtractStatistics)
    errors: list[ErrorReportItem] = field(default_factory=list)
    warnings: list[ErrorReportItem] = field(default_factory=list)
    task_id: str = ""
    export_path: str | None = None

    def validate(self) -> list[ErrorReportItem]:
        """校验结果一致性，返回告警项列表。

        校验项：
        1. 统计守恒：total == success + no_title + failed
        2. 结果集大小：len(result_set) == statistics.total
        """
        warnings: list[ErrorReportItem] = []
        if not self.statistics.is_consistent():
            warnings.append(
                ErrorReportItem(
                    url="",
                    error_code=ErrorCode.STATS_INCONSISTENT,
                    detail=f"统计守恒破坏：total={self.statistics.total} "
                    f"!= success+no_title+failed="
                    f"{self.statistics.success + self.statistics.no_title + self.statistics.failed}",
                )
            )
        if len(self.result_set) != self.statistics.total:
            warnings.append(
                ErrorReportItem(
                    url="",
                    error_code=ErrorCode.STATS_INCONSISTENT,
                    detail=f"结果集大小 {len(self.result_set)} != statistics.total {self.statistics.total}",
                )
            )
        return warnings
