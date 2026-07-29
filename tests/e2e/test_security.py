"""安全与约束验证测试（T15.03）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from url_link_extractor.exceptions import InsecureUrlError, SsrfBlockedError
from url_link_extractor.infra.http_client import HttpxFetcher
from url_link_extractor.models.enums import RecordStatus


class TestSecurity:
    async def test_ssrf_no_request(self):
        """SSRF 链接不发起请求（spec.md §4.3-2）。"""
        guard = MagicMock()
        guard.check_and_resolve = AsyncMock(side_effect=SsrfBlockedError("blocked"))
        fetcher = HttpxFetcher(guard, max_retries=0)
        with pytest.raises(SsrfBlockedError):
            await fetcher.fetch(URL("https://internal.example.com/"))

    async def test_http_rejected(self):
        """HTTP 明文不发起请求（spec.md §4.3-1）。"""
        guard = MagicMock()
        guard.check_and_resolve = AsyncMock()
        fetcher = HttpxFetcher(guard, max_retries=0)
        with pytest.raises(InsecureUrlError):
            await fetcher.fetch(URL("http://example.com/"))
        guard.check_and_resolve.assert_not_called()

    async def test_concurrency_max_20(self):
        """并发度 ≤ 20（spec.md §4.1-3）。"""
        from url_link_extractor.core.prefix_validator import PrefixValidator
        from url_link_extractor.models.request import ExtractRequest

        validator = PrefixValidator()
        result = validator.validate(ExtractRequest(url_prefix="https://x.com/", concurrency=100))
        assert result.concurrency == 20

    async def test_retry_max_3(self):
        """重试次数 ≤ 3（spec.md §4.2-2）。"""
        import respx

        from url_link_extractor.exceptions import HttpError

        guard = MagicMock()
        guard.check_and_resolve = AsyncMock(return_value="93.184.216.34")
        fetcher = HttpxFetcher(guard, max_retries=3)
        with respx.mock(assert_all_called=False) as mock:
            route = mock.get("https://example.com/a.html").respond(500)
            with pytest.raises(HttpError):
                await fetcher.fetch(URL("https://example.com/a.html"))
            assert route.call_count == 4  # 初始 + 3 重试

    async def test_redirect_max_5(self):
        """重定向跳数 ≤ 5（spec.md §6.1-4）。"""
        import respx

        from url_link_extractor.exceptions import RedirectLoopError

        guard = MagicMock()
        guard.check_and_resolve = AsyncMock(return_value="93.184.216.34")
        fetcher = HttpxFetcher(guard, max_retries=0, max_redirects=1)
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://example.com/a").respond(302, headers={"Location": "https://example.com/b"})
            mock.get("https://example.com/b").respond(302, headers={"Location": "https://example.com/c"})
            mock.get("https://example.com/c").respond(200, text="ok")
            with pytest.raises(RedirectLoopError):
                await fetcher.fetch(URL("https://example.com/a"))


class TestStatsConservation:
    async def test_total_equals_sum(self):
        """统计守恒：total = success + no_title + failed（spec.md §5.3.3-2）。"""
        from url_link_extractor.core.result_aggregator import ResultAggregator
        from url_link_extractor.models.enums import SortBy
        from url_link_extractor.models.result import LinkTitleRecord

        records = [
            LinkTitleRecord(url="https://e.com/1.html", title="A", status=RecordStatus.SUCCESS),
            LinkTitleRecord(url="https://e.com/2.html", title=None, status=RecordStatus.NO_TITLE),
            LinkTitleRecord(url="https://e.com/3.html", title=None, status=RecordStatus.FAILED),
        ]
        aggregator = ResultAggregator()
        _, stats, _, _ = aggregator.aggregate(records, [], SortBy.URL)
        assert stats.total == stats.success + stats.no_title + stats.failed
