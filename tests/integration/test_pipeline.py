"""流水线集成测试（T15.01）。

使用 respx mock 全链路 HTTP，构造复合场景验证端到端正确性。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from url_link_extractor.core.entry_resolver import DefaultEntryResolver
from url_link_extractor.core.link_discoverer import LinkDiscoverer
from url_link_extractor.core.prefix_validator import PrefixValidator
from url_link_extractor.core.result_aggregator import ResultAggregator
from url_link_extractor.core.title_extractor import TitleExtractor
from url_link_extractor.exceptions import EntryUnreachableError, InvalidPrefixError
from url_link_extractor.infra.html_parser import SelectolaxHtmlParser
from url_link_extractor.infra.protocols import FetchResponse
from url_link_extractor.infra.url_normalizer import UrlNormalizer
from url_link_extractor.models.enums import RecordStatus, SortBy
from url_link_extractor.models.request import ExtractRequest

PREFIX = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/")


async def test_invalid_prefix_no_network():
    """非法前缀不发起任何网络请求（spec.md §5.1.3-1）。"""
    validator = PrefixValidator()
    with pytest.raises(InvalidPrefixError):
        validator.validate(ExtractRequest(url_prefix=""))


async def test_entry_unreachable():
    """全部发现入口不可达抛 EntryUnreachableError（spec.md §5.1.3-2）。"""
    fetcher = MagicMock()
    fetcher.fetch = AsyncMock(side_effect=Exception("unreachable"))
    resolver = DefaultEntryResolver(fetcher)
    with pytest.raises(EntryUnreachableError):
        await resolver.resolve(PREFIX, None)


async def test_full_pipeline_mocked():
    """复合场景端到端：目录页 + 多匹配页 + 跨主域 + 相对路径 + 标题缺失 + 5xx。"""
    normalizer = UrlNormalizer()
    parser = SelectolaxHtmlParser(normalizer)

    # mock fetcher：入口返回目录页，匹配页返回标题/无标题/5xx
    dir_html = (
        '<a href="codeartsagent_cli_0001.html">A</a>'
        '<a href="codeartsagent_cli_0002.html">B</a>'
        '<a href="codeartsagent_cli_0003.html">C</a>'
        '<a href="https://other.example.com/x.html">跨域</a>'
    )
    page_a = "<html><head><title>页面A</title></head></html>"
    page_b = "<html><head></head></html>"  # 无标题


    fetcher = MagicMock()
    call_count = {"n": 0}

    async def fake_fetch(url, *, timeout, follow_redirect):
        call_count["n"] += 1
        s = str(url)
        if s == str(PREFIX):
            return FetchResponse(200, PREFIX, dir_html, "text/html")
        if "0001" in s:
            return FetchResponse(200, url, page_a, "text/html")
        if "0002" in s:
            return FetchResponse(200, url, page_b, "text/html")
        if "0003" in s:
            from url_link_extractor.exceptions import HttpError

            raise HttpError("HTTP 500")

    fetcher.fetch = AsyncMock(side_effect=fake_fetch)

    ssrf_guard = MagicMock()
    ssrf_guard.check_and_resolve = AsyncMock(return_value="93.184.216.34")

    # 1. 校验
    validator = PrefixValidator(normalizer)
    validator.validate(ExtractRequest(url_prefix=str(PREFIX)))

    # 2. 入口解析（显式入口）
    entries = [PREFIX]

    # 3. 链接发现
    discoverer = LinkDiscoverer(fetcher, parser, ssrf_guard, normalizer)
    discovery = await discoverer.discover(PREFIX, entries, allow_cross_subdomain=False)
    # 3 个匹配链接（跨域被拒）
    assert len(discovery.matched) == 3
    for url in discovery.matched:
        assert str(url).startswith(str(PREFIX))
        assert "..." not in str(url)

    # 4. 标题提取
    extractor = TitleExtractor(fetcher, parser)
    records, errors = await extractor.extract(discovery.matched, concurrency=5, follow_redirect=True)
    assert len(records) == 3
    statuses = {r.status for r in records}
    assert RecordStatus.SUCCESS in statuses
    assert RecordStatus.NO_TITLE in statuses
    assert RecordStatus.FAILED in statuses

    # 5. 汇总
    aggregator = ResultAggregator()
    sorted_records, stats, merged_errors, warnings = aggregator.aggregate(
        records, discovery.errors + errors, SortBy.URL
    )
    assert stats.is_consistent()
    assert stats.total == 3
    assert stats.success == 1
    assert stats.no_title == 1
    assert stats.failed == 1

    # URL 唯一且绝对完整
    urls = [r.url for r in sorted_records]
    assert len(urls) == len(set(urls))
    for u in urls:
        assert u.startswith("https://")
        assert "..." not in u


async def test_empty_result_set():
    """空结果集：统计全零，无异常（spec.md §5.3.3-1）。"""
    aggregator = ResultAggregator()
    _, stats, _, warnings = aggregator.aggregate([], [], SortBy.URL)
    assert stats.total == 0
    assert stats.is_consistent()
    assert warnings == []
