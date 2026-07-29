"""URL 链接标题提取组件 - 错误码与状态枚举定义。

对齐 spec.md §6.4（异常报告项 error_code 取值集合）与 §6.2（记录 status 取值集合）。
错误码枚举仅可新增不可删改（设计文档红线约束）。
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    """异常报告错误码枚举（spec.md §6.4）。

    取值集合严格对齐：
    TIMEOUT / HTTP_ERROR / PARSE_ERROR / NO_TITLE / SSRF_BLOCKED /
    ENTRY_UNREACHABLE / INVALID_PREFIX / STATS_INCONSISTENT / EXPORT_WRITE_ERROR
    """

    TIMEOUT = "TIMEOUT"
    HTTP_ERROR = "HTTP_ERROR"
    PARSE_ERROR = "PARSE_ERROR"
    NO_TITLE = "NO_TITLE"
    SSRF_BLOCKED = "SSRF_BLOCKED"
    ENTRY_UNREACHABLE = "ENTRY_UNREACHABLE"
    INVALID_PREFIX = "INVALID_PREFIX"
    STATS_INCONSISTENT = "STATS_INCONSISTENT"
    EXPORT_WRITE_ERROR = "EXPORT_WRITE_ERROR"


class RecordStatus(str, Enum):
    """单条链接提取结果状态枚举（spec.md §6.2-3）。"""

    SUCCESS = "success"
    NO_TITLE = "no_title"
    FAILED = "failed"


class SortBy(str, Enum):
    """结果集排序方式枚举（spec.md §6.1-6）。

    - URL：按 URL 字典序升序（默认）
    - TITLE：按标题字典序（None 排末尾）
    - NONE：保持原序
    """

    URL = "url"
    TITLE = "title"
    NONE = "none"
