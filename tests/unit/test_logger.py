"""TaskLogger 单元测试（T3.01）。"""

from __future__ import annotations

import io
import json
import logging

from url_link_extractor.infra.logger import TaskLogger
from url_link_extractor.models.enums import ErrorCode
from url_link_extractor.models.result import ExtractStatistics


def _make_logger(stream: io.StringIO, task_id: str = "t1") -> TaskLogger:
    """构造输出到 stream 的 TaskLogger。"""
    logger = TaskLogger(task_id)
    # 重定向 handler 到 stream
    for h in logger._logger.handlers:
        logger._logger.removeHandler(h)
    handler = logging.StreamHandler(stream=stream)
    from url_link_extractor.infra.logger import _StructuredFormatter

    handler.setFormatter(_StructuredFormatter())
    logger._logger.addHandler(handler)
    return logger


def _parse_lines(stream: io.StringIO) -> list[dict]:
    lines = [ln for ln in stream.getvalue().splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines]


class TestTaskLogger:
    def test_task_id_present(self):
        stream = io.StringIO()
        logger = _make_logger(stream, "task-abc")
        logger.log_task_start("https://example.com/p/")
        entries = _parse_lines(stream)
        assert entries[0]["task_id"] == "task-abc"
        assert entries[0]["event"] == "task_start"

    def test_html_detail_redacted(self):
        stream = io.StringIO()
        logger = _make_logger(stream)
        logger.log_error(
            "https://example.com/x.html",
            ErrorCode.PARSE_ERROR,
            detail="<title>敏感标题</title> 正文内容",
        )
        entries = _parse_lines(stream)
        assert entries[0]["detail"] == "[REDACTED:敏感内容已过滤]"

    def test_title_content_not_in_detail(self):
        stream = io.StringIO()
        logger = _make_logger(stream)
        logger.log_error("https://example.com/x.html", ErrorCode.NO_TITLE, detail="无标题")
        entries = _parse_lines(stream)
        assert "什么是码道CLI" not in entries[0]["detail"]

    def test_stats_logging(self):
        stream = io.StringIO()
        logger = _make_logger(stream)
        logger.log_task_end(ExtractStatistics(total=10, success=8, no_title=1, failed=1))
        entries = _parse_lines(stream)
        assert entries[0]["event"] == "task_end"
        assert "total=10" in entries[0]["detail"]

    def test_request_logging(self):
        stream = io.StringIO()
        logger = _make_logger(stream)
        logger.log_request("https://example.com/a.html", 200)
        entries = _parse_lines(stream)
        assert entries[0]["url"] == "https://example.com/a.html"
        assert entries[0]["status_code"] == 200

    def test_export_logging(self):
        stream = io.StringIO()
        logger = _make_logger(stream)
        logger.log_export("/tmp/result.xlsx", True)
        entries = _parse_lines(stream)
        assert entries[0]["event"] == "export"
        assert "success=True" in entries[0]["detail"]

    def test_detail_truncation(self):
        stream = io.StringIO()
        logger = _make_logger(stream)
        long_detail = "x" * 500
        logger.log_error("https://e.com/a.html", ErrorCode.HTTP_ERROR, detail=long_detail)
        entries = _parse_lines(stream)
        assert entries[0]["detail"].endswith("[截断]")
