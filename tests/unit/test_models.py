"""领域数据模型单元测试（T2.02）。"""

from __future__ import annotations

import pytest

from url_link_extractor.models.enums import ErrorCode, RecordStatus, SortBy
from url_link_extractor.models.export_spec import EXPORT_FILE_SPEC
from url_link_extractor.models.request import ExtractRequest
from url_link_extractor.models.result import (
    ErrorReportItem,
    ExportOutcome,
    ExtractResult,
    ExtractStatistics,
    LinkTitleRecord,
)


class TestExtractRequest:
    def test_default_values(self):
        req = ExtractRequest(url_prefix="https://example.com/p/")
        assert req.url_prefix == "https://example.com/p/"
        assert req.entry_urls is None
        assert req.allow_cross_subdomain is False
        assert req.follow_redirect is True
        assert req.concurrency == 5
        assert req.sort_by == SortBy.URL
        assert req.work_dir is None

    def test_frozen(self):
        req = ExtractRequest(url_prefix="https://example.com/p/")
        with pytest.raises(Exception):
            req.url_prefix = "x"  # type: ignore[misc]


class TestExportFileSpec:
    def test_spec_values(self):
        assert EXPORT_FILE_SPEC.file_name == "result.xlsx"
        assert EXPORT_FILE_SPEC.column_count == 2
        assert EXPORT_FILE_SPEC.column_1_name == "URL 完整链接"
        assert EXPORT_FILE_SPEC.column_2_name == "页面标题"

    def test_frozen(self):
        with pytest.raises(Exception):
            EXPORT_FILE_SPEC.file_name = "x"  # type: ignore[misc]


class TestLinkTitleRecord:
    def test_success_record(self):
        r = LinkTitleRecord(url="https://example.com/a.html", title="T", status=RecordStatus.SUCCESS)
        assert r.title == "T"

    def test_title_none_means_missing(self):
        r = LinkTitleRecord(url="https://example.com/a.html", title=None, status=RecordStatus.NO_TITLE)
        assert r.title is None


class TestExtractStatistics:
    def test_consistent(self):
        s = ExtractStatistics(total=100, success=90, no_title=5, failed=5)
        assert s.is_consistent() is True

    def test_inconsistent(self):
        s = ExtractStatistics(total=100, success=80, no_title=5, failed=5)
        assert s.is_consistent() is False

    def test_zero(self):
        s = ExtractStatistics()
        assert s.is_consistent() is True


class TestExtractResultValidate:
    def test_consistent_no_warnings(self):
        records = [
            LinkTitleRecord(url="https://e.com/1.html", title="A", status=RecordStatus.SUCCESS),
            LinkTitleRecord(url="https://e.com/2.html", title=None, status=RecordStatus.NO_TITLE),
            LinkTitleRecord(url="https://e.com/3.html", title=None, status=RecordStatus.FAILED),
        ]
        stats = ExtractStatistics(total=3, success=1, no_title=1, failed=1)
        result = ExtractResult(result_set=records, statistics=stats, task_id="t1")
        assert result.validate() == []

    def test_stats_inconsistent(self):
        records = [
            LinkTitleRecord(url="https://e.com/1.html", title="A", status=RecordStatus.SUCCESS),
        ]
        stats = ExtractStatistics(total=2, success=1, no_title=0, failed=0)
        result = ExtractResult(result_set=records, statistics=stats, task_id="t1")
        warnings = result.validate()
        assert len(warnings) == 2
        assert all(w.error_code == ErrorCode.STATS_INCONSISTENT for w in warnings)

    def test_url_uniqueness_not_checked_by_validate(self):
        # validate 仅校验统计守恒与大小，URL 唯一性由 LinkDiscoverer 保证
        records = [
            LinkTitleRecord(url="https://e.com/1.html", title="A", status=RecordStatus.SUCCESS),
            LinkTitleRecord(url="https://e.com/1.html", title="A", status=RecordStatus.SUCCESS),
        ]
        stats = ExtractStatistics(total=2, success=2, no_title=0, failed=0)
        result = ExtractResult(result_set=records, statistics=stats, task_id="t1")
        assert result.validate() == []


class TestExportOutcome:
    def test_success(self):
        o = ExportOutcome(file_path="/tmp/result.xlsx", error=None)
        assert o.file_path == "/tmp/result.xlsx"
        assert o.error is None

    def test_failure(self):
        err = ErrorReportItem(url="/tmp/result.xlsx", error_code=ErrorCode.EXPORT_WRITE_ERROR, detail="disk full")
        o = ExportOutcome(file_path=None, error=err)
        assert o.file_path is None
        assert o.error.error_code == ErrorCode.EXPORT_WRITE_ERROR
