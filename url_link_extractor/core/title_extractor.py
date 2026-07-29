"""TitleExtractor 标题并发提取（spec.md §5.2.1/§5.2.3、设计 §2.1.3 状态机）。

状态机：
- 2xx + 合法 HTML → extract_title → 有标题 SUCCESS / 无标题 NO_TITLE
- 4xx → FAILED（HTTP_ERROR，不重试）
- 5xx/重置/超时 → 重试耗尽后 FAILED（TIMEOUT/HTTP_ERROR）
- 解析失败 → FAILED（PARSE_ERROR）
- 明文 HTTP → FAILED（HTTP_ERROR）
单链接失败不中断整体任务。
"""

from __future__ import annotations

import asyncio

from yarl import URL

from ..exceptions import (
    HttpError,
    InsecureUrlError,
    ParseError,
)
from ..exceptions import (
    TimeoutError as ExtractorTimeoutError,
)
from ..infra.protocols import HtmlParser, HttpFetcher
from ..models.enums import ErrorCode, RecordStatus
from ..models.result import ErrorReportItem, LinkTitleRecord


class TitleExtractor:
    """标题并发提取器。"""

    def __init__(self, fetcher: HttpFetcher, parser: HtmlParser) -> None:
        self._fetcher = fetcher
        self._parser = parser

    async def extract(
        self,
        urls: list[URL],
        concurrency: int = 5,
        follow_redirect: bool = True,
    ) -> tuple[list[LinkTitleRecord], list[ErrorReportItem]]:
        """并发提取标题，返回 (records, errors)。"""
        sem = asyncio.Semaphore(concurrency)
        tasks = [self._extract_one(url, sem, follow_redirect) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        records: list[LinkTitleRecord] = []
        errors: list[ErrorReportItem] = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                # 未预期异常包装为 FAILED
                records.append(LinkTitleRecord(url=str(url), title=None, status=RecordStatus.FAILED))
                errors.append(
                    ErrorReportItem(
                        url=str(url),
                        error_code=ErrorCode.HTTP_ERROR,
                        detail=f"未预期异常：{result}",
                    )
                )
            else:
                record, error = result
                records.append(record)
                if error:
                    errors.append(error)

        return records, errors

    async def _extract_one(
        self, url: URL, sem: asyncio.Semaphore, follow_redirect: bool
    ) -> tuple[LinkTitleRecord, ErrorReportItem | None]:
        """提取单个 URL 的标题。"""
        async with sem:
            try:
                resp = await self._fetcher.fetch(url, timeout=10.0, follow_redirect=follow_redirect)
            except InsecureUrlError as exc:
                return (
                    LinkTitleRecord(url=str(url), title=None, status=RecordStatus.FAILED),
                    ErrorReportItem(url=str(url), error_code=ErrorCode.HTTP_ERROR, detail=f"非 HTTPS：{exc}"),
                )
            except ExtractorTimeoutError as exc:
                return (
                    LinkTitleRecord(url=str(url), title=None, status=RecordStatus.FAILED),
                    ErrorReportItem(url=str(url), error_code=ErrorCode.TIMEOUT, detail=str(exc)),
                )
            except HttpError as exc:
                return (
                    LinkTitleRecord(url=str(url), title=None, status=RecordStatus.FAILED),
                    ErrorReportItem(url=str(url), error_code=ErrorCode.HTTP_ERROR, detail=str(exc)),
                )
            except Exception as exc:
                return (
                    LinkTitleRecord(url=str(url), title=None, status=RecordStatus.FAILED),
                    ErrorReportItem(url=str(url), error_code=ErrorCode.HTTP_ERROR, detail=str(exc)),
                )

            # 解析标题
            try:
                title = self._parser.extract_title(resp.body)
            except ParseError as exc:
                return (
                    LinkTitleRecord(url=str(url), title=None, status=RecordStatus.FAILED),
                    ErrorReportItem(url=str(url), error_code=ErrorCode.PARSE_ERROR, detail=str(exc)),
                )
            except Exception as exc:
                return (
                    LinkTitleRecord(url=str(url), title=None, status=RecordStatus.FAILED),
                    ErrorReportItem(url=str(url), error_code=ErrorCode.PARSE_ERROR, detail=str(exc)),
                )

            if title:
                return (
                    LinkTitleRecord(url=str(url), title=title, status=RecordStatus.SUCCESS),
                    None,
                )
            return (
                LinkTitleRecord(url=str(url), title=None, status=RecordStatus.NO_TITLE),
                ErrorReportItem(url=str(url), error_code=ErrorCode.NO_TITLE, detail="标题缺失"),
            )
