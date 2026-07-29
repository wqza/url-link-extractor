"""HttpClient 单元测试（T6.02）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from yarl import URL

from url_link_extractor.exceptions import HttpError, InsecureUrlError, SsrfBlockedError
from url_link_extractor.infra.http_client import HttpxFetcher


def _mock_ssrf():
    guard = MagicMock()
    guard.check_and_resolve = AsyncMock(return_value="93.184.216.34")
    return guard


class TestFetch:
    async def test_https_success(self):
        guard = _mock_ssrf()
        fetcher = HttpxFetcher(guard, max_retries=0)
        with respx.mock() as mock:
            mock.get("https://example.com/a.html").respond(200, text="<html><title>X</title></html>")
            resp = await fetcher.fetch(URL("https://example.com/a.html"))
            assert resp.status == 200
            assert "<title>X</title>" in resp.body

    async def test_http_rejected(self):
        guard = _mock_ssrf()
        fetcher = HttpxFetcher(guard)
        with pytest.raises(InsecureUrlError):
            await fetcher.fetch(URL("http://example.com/a.html"))
        guard.check_and_resolve.assert_not_called()

    async def test_4xx_no_retry(self):
        guard = _mock_ssrf()
        fetcher = HttpxFetcher(guard, max_retries=3)
        with respx.mock(assert_all_called=False) as mock:
            route = mock.get("https://example.com/a.html").respond(404)
            with pytest.raises(HttpError):
                await fetcher.fetch(URL("https://example.com/a.html"))
            assert route.call_count == 1

    async def test_5xx_retry_then_fail(self):
        guard = _mock_ssrf()
        fetcher = HttpxFetcher(guard, max_retries=3)
        with respx.mock() as mock:
            route = mock.get("https://example.com/a.html").respond(500)
            with pytest.raises(HttpError):
                await fetcher.fetch(URL("https://example.com/a.html"))
            assert route.call_count == 4  # 初始 + 3 重试

    async def test_ssrf_blocked(self):
        guard = MagicMock()
        guard.check_and_resolve = AsyncMock(side_effect=SsrfBlockedError("blocked"))
        fetcher = HttpxFetcher(guard)
        with pytest.raises(SsrfBlockedError):
            await fetcher.fetch(URL("https://example.com/a.html"))

    async def test_timeout_retry(self):
        guard = _mock_ssrf()
        fetcher = HttpxFetcher(guard, max_retries=2, timeout=0.1)
        with respx.mock() as mock:
            route = mock.get("https://example.com/a.html").mock(side_effect=httpx.TimeoutException("timeout"))
            from url_link_extractor.exceptions import TimeoutError as ExtractorTimeoutError

            with pytest.raises(ExtractorTimeoutError):
                await fetcher.fetch(URL("https://example.com/a.html"))
            assert route.call_count == 3  # 初始 + 2 重试

    async def test_redirect_limit(self):
        guard = _mock_ssrf()
        fetcher = HttpxFetcher(guard, max_retries=0, max_redirects=1)
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://example.com/a.html").respond(302, headers={"Location": "https://example.com/b.html"})
            mock.get("https://example.com/b.html").respond(302, headers={"Location": "https://example.com/c.html"})
            mock.get("https://example.com/c.html").respond(200, text="ok")
            from url_link_extractor.exceptions import RedirectLoopError

            with pytest.raises(RedirectLoopError):
                await fetcher.fetch(URL("https://example.com/a.html"))
