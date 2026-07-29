"""ResultAggregator 单元测试（T12.02）。"""

from __future__ import annotations

import pytest

from url_link_extractor.core.result_aggregator import ResultAggregator
from url_link_extractor.models.enums import ErrorCode, RecordStatus, SortBy
from url_link_extractor.models.result import ErrorReportItem, LinkTitleRecord


@pytest.fixture
def aggregator():
    return ResultAggregator()


def _record(url, title="T", status=RecordStatus.SUCCESS):
    return LinkTitleRecord(url=url, title=title, status=status)


class TestAggregate:
    async def test_sort_by_url(self, aggregator):
        records = [
            _record("https://e.com/c.html"),
            _record("https://e.com/a.html"),
            _record("https://e.com/b.html"),
        ]
        sorted_r, stats, errors, warnings = aggregator.aggregate(records, [], SortBy.URL)
        assert [r.url for r in sorted_r] == [
            "https://e.com/a.html",
            "https://e.com/b.html",
            "https://e.com/c.html",
        ]

    async def test_sort_by_title(self, aggregator):
        records = [
            _record("https://e.com/1.html", title="C"),
            _record("https://e.com/2.html", title="A"),
            _record("https://e.com/3.html", title="B"),
        ]
        sorted_r, _, _, _ = aggregator.aggregate(records, [], SortBy.TITLE)
        assert [r.title for r in sorted_r] == ["A", "B", "C"]

    async def test_sort_by_title_none_last(self, aggregator):
        records = [
            _record("https://e.com/1.html", title=None, status=RecordStatus.NO_TITLE),
            _record("https://e.com/2.html", title="A"),
        ]
        sorted_r, _, _, _ = aggregator.aggregate(records, [], SortBy.TITLE)
        assert sorted_r[0].title == "A"
        assert sorted_r[1].title is None

    async def test_sort_none(self, aggregator):
        records = [
            _record("https://e.com/c.html"),
            _record("https://e.com/a.html"),
        ]
        sorted_r, _, _, _ = aggregator.aggregate(records, [], SortBy.NONE)
        assert [r.url for r in sorted_r] == ["https://e.com/c.html", "https://e.com/a.html"]

    async def test_stats_consistent(self, aggregator):
        records = [
            _record("https://e.com/1.html", status=RecordStatus.SUCCESS),
            _record("https://e.com/2.html", title=None, status=RecordStatus.NO_TITLE),
            _record("https://e.com/3.html", title=None, status=RecordStatus.FAILED),
        ]
        _, stats, _, warnings = aggregator.aggregate(records, [], SortBy.URL)
        assert stats.total == 3
        assert stats.success == 1
        assert stats.no_title == 1
        assert stats.failed == 1
        assert stats.is_consistent()
        assert warnings == []

    async def test_empty_records(self, aggregator):
        _, stats, _, _ = aggregator.aggregate([], [], SortBy.URL)
        assert stats.total == 0
        assert stats.is_consistent()

    async def test_errors_merged(self, aggregator):
        errors = [ErrorReportItem(url="https://e.com/x", error_code=ErrorCode.HTTP_ERROR, detail="err")]
        _, _, merged, _ = aggregator.aggregate([], errors, SortBy.URL)
        assert len(merged) == 1
        assert merged[0].error_code == ErrorCode.HTTP_ERROR
