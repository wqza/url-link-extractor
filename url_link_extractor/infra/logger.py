"""TaskLogger 结构化任务日志（spec.md §4.4、§4.3-3）。

约束：
- 贯穿 task_id
- 禁止输出 HTTP 响应体、HTML 正文、<title> 内容等敏感字段
- detail 超长时截断
- 输出到 stderr，不写文件
- 日志级别由环境变量 URL_EXTRACTOR_LOG_LEVEL 控制，默认 INFO
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone

from ..models.enums import ErrorCode
from ..models.result import ExtractStatistics

_DETAIL_MAX_LEN = 200
_SENSITIVE_MARKERS = ("<title", "<html", "<body", "<head", "<a href", "password", "token", "secret")


def _sanitize_detail(detail: str | None) -> str | None:
    """清洗 detail：截断超长、拒绝含 HTML 标签的敏感内容。"""
    if detail is None:
        return None
    if any(marker in detail.lower() for marker in _SENSITIVE_MARKERS):
        return "[REDACTED:敏感内容已过滤]"
    if len(detail) > _DETAIL_MAX_LEN:
        return detail[:_DETAIL_MAX_LEN] + "...[截断]"
    return detail


class _StructuredFormatter(logging.Formatter):
    """JSON 结构化格式器。"""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": getattr(record, "task_id", ""),
            "level": record.levelname,
            "event": getattr(record, "event", ""),
            "url": getattr(record, "url", None),
            "status_code": getattr(record, "status_code", None),
            "error_code": getattr(record, "error_code", None),
            "detail": _sanitize_detail(getattr(record, "detail", None)),
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


class TaskLogger:
    """任务级结构化日志器。"""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        level_name = os.environ.get("URL_EXTRACTOR_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
        logger_name = f"url_link_extractor.task.{task_id}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.StreamHandler(stream=sys.stderr)
            handler.setFormatter(_StructuredFormatter())
            logger.addHandler(handler)
        self._logger = logger

    def _emit(
        self,
        level: int,
        event: str,
        url: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
        detail: str | None = None,
        message: str = "",
    ) -> None:
        self._logger.log(
            level,
            message,
            extra={
                "task_id": self.task_id,
                "event": event,
                "url": url,
                "status_code": status_code,
                "error_code": error_code,
                "detail": detail,
            },
        )

    def log_task_start(self, prefix: str, entry_urls: list[str] | None = None) -> None:
        self._emit(
            logging.INFO,
            event="task_start",
            detail=f"prefix={prefix}",
            message=f"任务开始 prefix={prefix} entries={entry_urls}",
        )

    def log_task_end(self, statistics: ExtractStatistics) -> None:
        self._emit(
            logging.INFO,
            event="task_end",
            detail=f"total={statistics.total} success={statistics.success} "
            f"no_title={statistics.no_title} failed={statistics.failed}",
            message=f"任务结束 {statistics}",
        )

    def log_request(self, url: str, status_code: int) -> None:
        self._emit(
            logging.INFO,
            event="request",
            url=url,
            status_code=status_code,
            message=f"请求 {url} -> {status_code}",
        )

    def log_error(self, url: str, error_code: ErrorCode, detail: str | None = None) -> None:
        self._emit(
            logging.WARNING,
            event="error",
            url=url,
            error_code=error_code.value,
            detail=detail,
            message=f"错误 {url} {error_code.value} {detail or ''}",
        )

    def log_export(self, path: str, success: bool) -> None:
        self._emit(
            logging.INFO if success else logging.WARNING,
            event="export",
            detail=f"path={path} success={success}",
            message=f"导出 {path} success={success}",
        )
