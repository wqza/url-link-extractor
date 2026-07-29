"""LinkDiscoverer 单元测试（T10.03）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from yarl import URL

from url_link_extractor.core.link_discoverer import LinkDiscoverer
from url_link_extractor.infra.protocols import FetchResponse
from url_link_extractor.models.enums import ErrorCode


def _mock_ssrf():
    guard = MagicMock()
    guard.check_and_resolve = AsyncMock(return_value="93.184.216.34")
    return guard


def _mock_blocked_ssrf():
    guard = MagicMock()
    guard.check_and_resolve = AsyncMock(side_effect=Exception("SSRF"))
    from url_link_extractor.exceptions import SsrfBlockedError

    guard.check_and_resolve = AsyncMock(side_effect=SsrfBlockedError("blocked"))
    return guard


PREFIX = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/")


class TestDiscover:
    async def test_basic_match(self):
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(
                status=200,
                final_url=PREFIX,
                body='<a href="codeartsagent_cli_0001.html">A</a>',
                content_type="text/html",
            )
        )
        parser = MagicMock()
        parser.extract_links = MagicMock(
            return_value=[URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/codeartsagent_cli_0001.html")]
        )
        guard = _mock_ssrf()
        discoverer = LinkDiscoverer(fetcher, parser, guard)
        result = await discoverer.discover(PREFIX, [PREFIX], allow_cross_subdomain=False)
        assert len(result.matched) == 1
        assert result.errors == []

    async def test_dedup(self):
        url = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/a.html")
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(status=200, final_url=PREFIX, body="", content_type="text/html")
        )
        parser = MagicMock()
        parser.extract_links = MagicMock(return_value=[url, url, url])
        guard = _mock_ssrf()
        discoverer = LinkDiscoverer(fetcher, parser, guard)
        result = await discoverer.discover(PREFIX, [PREFIX], allow_cross_subdomain=False)
        assert len(result.matched) == 1

    async def test_cross_main_domain_rejected(self):
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(status=200, final_url=PREFIX, body="", content_type="text/html")
        )
        parser = MagicMock()
        parser.extract_links = MagicMock(
            return_value=[URL("https://other.example.com/intl/zh-cn/usermanual-cli/a.html")]
        )
        guard = _mock_ssrf()
        discoverer = LinkDiscoverer(fetcher, parser, guard)
        result = await discoverer.discover(PREFIX, [PREFIX], allow_cross_subdomain=False)
        assert len(result.matched) == 0

    async def test_cross_subdomain_allowed_when_flag(self):
        # 前缀字符串匹配下，跨子域 URL 不会通过前缀匹配；
        # 此测试验证同子域链接在 allow_cross_subdomain=True 时正常收录
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(status=200, final_url=PREFIX, body="", content_type="text/html")
        )
        parser = MagicMock()
        same_sub_url = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/a.html")
        parser.extract_links = MagicMock(return_value=[same_sub_url])
        guard = _mock_ssrf()
        discoverer = LinkDiscoverer(fetcher, parser, guard)
        result = await discoverer.discover(PREFIX, [PREFIX], allow_cross_subdomain=True)
        assert len(result.matched) == 1

    async def test_cross_subdomain_rejected_by_default(self):
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(status=200, final_url=PREFIX, body="", content_type="text/html")
        )
        parser = MagicMock()
        sub_url = URL("https://console.huaweicloud.com/intl/zh-cn/usermanual-cli/a.html")
        parser.extract_links = MagicMock(return_value=[sub_url])
        guard = _mock_ssrf()
        discoverer = LinkDiscoverer(fetcher, parser, guard)
        result = await discoverer.discover(PREFIX, [PREFIX], allow_cross_subdomain=False)
        assert len(result.matched) == 0

    async def test_ssrf_blocked(self):
        url = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/a.html")
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(status=200, final_url=PREFIX, body="", content_type="text/html")
        )
        parser = MagicMock()
        parser.extract_links = MagicMock(return_value=[url])
        guard = _mock_blocked_ssrf()
        discoverer = LinkDiscoverer(fetcher, parser, guard)
        result = await discoverer.discover(PREFIX, [PREFIX], allow_cross_subdomain=False)
        assert len(result.matched) == 0
        assert any(e.error_code == ErrorCode.SSRF_BLOCKED for e in result.errors)

    async def test_no_prefix_match_filtered(self):
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(status=200, final_url=PREFIX, body="", content_type="text/html")
        )
        parser = MagicMock()
        parser.extract_links = MagicMock(
            return_value=[URL("https://support.huaweicloud.com/intl/zh-cn/other.html")]
        )
        guard = _mock_ssrf()
        discoverer = LinkDiscoverer(fetcher, parser, guard)
        result = await discoverer.discover(PREFIX, [PREFIX], allow_cross_subdomain=False)
        assert len(result.matched) == 0
        assert result.errors == []
