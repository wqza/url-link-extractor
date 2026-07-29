"""LinkDiscoverer 链接发现（spec.md §5.1.1、设计 §2.1.3）。

链路：入口拉取 → 链接解析 → 过滤管道 → 去重 → 匹配候选集
过滤管道：协议白名单 → 绝对化 → 前缀匹配 → 网页资源限定 → 跨域控制 → SSRF 拦截
"""

from __future__ import annotations

from dataclasses import dataclass, field

from yarl import URL

from ..exceptions import SsrfBlockedError
from ..infra.protocols import FetchResponse, HtmlParser, HttpFetcher
from ..infra.ssrf_guard import SsrfGuard
from ..infra.url_normalizer import UrlNormalizer
from ..models.enums import ErrorCode
from ..models.result import ErrorReportItem

_HTML_EXTENSIONS = (".html", ".htm")


@dataclass
class DiscoveryResult:
    """链接发现结果。"""

    matched: list[URL] = field(default_factory=list)
    errors: list[ErrorReportItem] = field(default_factory=list)


class LinkDiscoverer:
    """链接发现器。"""

    def __init__(
        self,
        fetcher: HttpFetcher,
        parser: HtmlParser,
        ssrf_guard: SsrfGuard,
        normalizer: UrlNormalizer | None = None,
    ) -> None:
        self._fetcher = fetcher
        self._parser = parser
        self._ssrf = ssrf_guard
        self._norm = normalizer or UrlNormalizer()

    async def discover(
        self, prefix: URL, entries: list[URL], allow_cross_subdomain: bool
    ) -> DiscoveryResult:
        """发现匹配前缀的链接。"""
        matched: list[URL] = []
        seen: set[str] = set()
        errors: list[ErrorReportItem] = []

        for entry in entries:
            try:
                resp = await self._fetcher.fetch(entry, timeout=10.0, follow_redirect=True)
            except SsrfBlockedError as exc:
                errors.append(ErrorReportItem(url=str(entry), error_code=ErrorCode.SSRF_BLOCKED, detail=str(exc)))
                continue
            except Exception as exc:
                errors.append(
                    ErrorReportItem(
                        url=str(entry),
                        error_code=ErrorCode.HTTP_ERROR,
                        detail=f"入口拉取失败：{exc}",
                    )
                )
                continue

            try:
                candidate_urls = self._parser.extract_links(resp.body, base=entry)
            except Exception as exc:
                errors.append(
                    ErrorReportItem(
                        url=str(entry),
                        error_code=ErrorCode.PARSE_ERROR,
                        detail=f"入口链接解析失败：{exc}",
                    )
                )
                continue

            for candidate in candidate_urls:
                # 前缀逐字符匹配
                if not self._norm.starts_with_prefix(candidate, prefix):
                    continue

                # 网页资源限定
                if not self._is_html_resource(candidate, resp):
                    continue

                # 跨域控制
                if not self._check_cross_domain(candidate, prefix, allow_cross_subdomain):
                    continue

                # SSRF 拦截
                try:
                    await self._ssrf.check_and_resolve(candidate.host or "")
                except SsrfBlockedError as exc:
                    errors.append(
                        ErrorReportItem(
                            url=str(candidate),
                            error_code=ErrorCode.SSRF_BLOCKED,
                            detail=str(exc),
                        )
                    )
                    continue

                # 去重
                key = str(candidate)
                if key in seen:
                    continue
                seen.add(key)
                matched.append(candidate)

        return DiscoveryResult(matched=matched, errors=errors)

    def _is_html_resource(self, url: URL, resp: FetchResponse) -> bool:
        """网页资源限定：.html/.htm 结尾或 Content-Type 为 text/html。"""
        path = str(url.path).lower()
        if path.endswith(_HTML_EXTENSIONS):
            return True
        content_type = (resp.content_type or "").lower()
        if "text/html" in content_type:
            return True
        return False

    def _check_cross_domain(self, candidate: URL, prefix: URL, allow_cross_subdomain: bool) -> bool:
        """跨域控制：默认同主域；allow_cross_subdomain 同主域不同子域；禁止跨主域。"""
        if not self._norm.is_same_main_domain(candidate, prefix):
            return False
        if not allow_cross_subdomain:
            if not self._norm.is_same_subdomain(candidate, prefix):
                return False
        return True
