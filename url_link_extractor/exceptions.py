"""URL 链接标题提取组件 - 统一异常体系。

所有细分异常均继承 ExtractorError，承载 code（ErrorCode）与 detail（可选字符串）。
对齐 design.md §2.3.1 异常体系。
"""

from __future__ import annotations

from .models.enums import ErrorCode


class ExtractorError(Exception):
    """组件顶层异常基类。"""

    def __init__(self, code: ErrorCode, detail: str | None = None) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code.value}] {detail or ''}")


class InvalidPrefixError(ExtractorError):
    """URL 前缀格式非法（spec.md §5.1.3-1）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.INVALID_PREFIX, detail)


class EntryUnreachableError(ExtractorError):
    """发现入口全部不可访问（spec.md §5.1.3-2）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.ENTRY_UNREACHABLE, detail)


class TimeoutError(ExtractorError):
    """网页拉取超时（spec.md §5.2.3-1）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.TIMEOUT, detail)


class HttpError(ExtractorError):
    """网页返回非 2xx 状态码（spec.md §5.2.3-2）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.HTTP_ERROR, detail)


class InsecureUrlError(ExtractorError):
    """非 HTTPS 明文链接（spec.md §4.3-1）。映射到 HTTP_ERROR。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.HTTP_ERROR, detail)


class RedirectLoopError(ExtractorError):
    """重定向跳数超限（spec.md §6.1-4）。映射到 HTTP_ERROR。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.HTTP_ERROR, detail)


class ParseError(ExtractorError):
    """HTML 解析失败（spec.md §5.2.3-3）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.PARSE_ERROR, detail)


class SsrfBlockedError(ExtractorError):
    """SSRF 拦截：链接指向内网/本地地址（spec.md §5.1.3-3、§4.3-2）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.SSRF_BLOCKED, detail)


class StatsInconsistentError(ExtractorError):
    """统计守恒破坏（spec.md §5.3.3-2）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.STATS_INCONSISTENT, detail)


class ExcelWriteError(ExtractorError):
    """result.xlsx 导出写入失败（spec.md §5.3.3-3）。"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(ErrorCode.EXPORT_WRITE_ERROR, detail)
