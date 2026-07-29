"""URL 链接标题提取组件。

按指定 URL 前缀批量发现匹配网页链接，提取每个网页的 <title>，
输出"链接-标题"配对结果集，并导出为 result.xlsx。

稳定 API：
    extract / extract_async / ExtractRequest / ExtractResult /
    LinkTitleRecord / ExtractStatistics / ErrorReportItem /
    ErrorCode / RecordStatus / SortBy
"""

from __future__ import annotations

from .exceptions import (
    EntryUnreachableError,
    ExcelWriteError,
    ExtractorError,
    HttpError,
    InsecureUrlError,
    InvalidPrefixError,
    ParseError,
    RedirectLoopError,
    SsrfBlockedError,
    StatsInconsistentError,
    TimeoutError,
)
from .models.enums import ErrorCode, RecordStatus, SortBy
from .models.export_spec import EXPORT_FILE_SPEC, ExportFileSpec
from .models.request import ExtractRequest
from .models.result import (
    ErrorReportItem,
    ExportOutcome,
    ExtractResult,
    ExtractStatistics,
    LinkTitleRecord,
)

__all__ = [
    # 主入口
    "extract",
    "extract_async",
    # 请求/结果模型
    "ExtractRequest",
    "ExtractResult",
    "LinkTitleRecord",
    "ExtractStatistics",
    "ErrorReportItem",
    "ExportOutcome",
    "ExportFileSpec",
    "EXPORT_FILE_SPEC",
    # 枚举
    "ErrorCode",
    "RecordStatus",
    "SortBy",
    # 异常
    "ExtractorError",
    "InvalidPrefixError",
    "EntryUnreachableError",
    "TimeoutError",
    "HttpError",
    "InsecureUrlError",
    "RedirectLoopError",
    "ParseError",
    "SsrfBlockedError",
    "StatsInconsistentError",
    "ExcelWriteError",
]


def __getattr__(name: str):
    """惰性导入主入口函数，避免循环导入。"""
    if name in ("extract", "extract_async"):
        from .entry.extractor import extract, extract_async

        return {"extract": extract, "extract_async": extract_async}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
