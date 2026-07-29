"""Entry 流水线编排主入口（设计 §2.2.2-1）。

流水线：PrefixValidator → EntryResolver → LinkDiscoverer → TitleExtractor → ResultAggregator → ResultExporter
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

from ..core.entry_resolver import DefaultEntryResolver
from ..core.link_discoverer import LinkDiscoverer
from ..core.prefix_validator import PrefixValidator
from ..core.result_aggregator import ResultAggregator
from ..core.result_exporter import ExcelResultExporter
from ..core.title_extractor import TitleExtractor
from ..exceptions import EntryUnreachableError, InvalidPrefixError
from ..infra.excel_writer import ExcelWriter
from ..infra.html_parser import SelectolaxHtmlParser
from ..infra.http_client import HttpxFetcher
from ..infra.logger import TaskLogger
from ..infra.ssrf_guard import SsrfGuard
from ..infra.url_normalizer import UrlNormalizer
from ..models.enums import ErrorCode
from ..models.request import ExtractRequest
from ..models.result import ErrorReportItem, ExtractResult, ExtractStatistics


async def extract_async(request: ExtractRequest) -> ExtractResult:
    """异步主入口：编排完整流水线。"""
    task_id = uuid4().hex
    logger = TaskLogger(task_id)

    # 1. 参数校验
    normalizer = UrlNormalizer()
    validator = PrefixValidator(normalizer)
    try:
        validated = validator.validate(request)
    except InvalidPrefixError as exc:
        logger.log_error("", ErrorCode.INVALID_PREFIX, str(exc))
        return ExtractResult(
            result_set=[],
            statistics=ExtractStatistics(),
            errors=[ErrorReportItem(url=request.url_prefix, error_code=ErrorCode.INVALID_PREFIX, detail=str(exc))],
            task_id=task_id,
            export_path=None,
        )

    logger.log_task_start(str(validated.prefix), [str(u) for u in (validated.entry_urls or [])])

    # 初始化 infra
    ssrf_guard = SsrfGuard()
    fetcher = HttpxFetcher(ssrf_guard, logger)
    parser = SelectolaxHtmlParser(normalizer)

    # 2. 发现入口解析
    entry_resolver = DefaultEntryResolver(fetcher)
    try:
        entries = await entry_resolver.resolve(validated.prefix, validated.entry_urls)
    except EntryUnreachableError as exc:
        logger.log_error(str(validated.prefix), ErrorCode.ENTRY_UNREACHABLE, str(exc))
        return ExtractResult(
            result_set=[],
            statistics=ExtractStatistics(),
            errors=[ErrorReportItem(url=str(validated.prefix), error_code=ErrorCode.ENTRY_UNREACHABLE, detail=str(exc))],
            task_id=task_id,
            export_path=None,
        )

    # 3. 链接发现
    discoverer = LinkDiscoverer(fetcher, parser, ssrf_guard, normalizer)
    discovery = await discoverer.discover(
        validated.prefix, entries, validated.allow_cross_subdomain
    )
    all_errors = list(discovery.errors)

    # 4. 标题提取
    extractor = TitleExtractor(fetcher, parser)
    records, title_errors = await extractor.extract(
        discovery.matched, validated.concurrency, validated.follow_redirect
    )
    all_errors.extend(title_errors)

    # 5. 结果汇总
    aggregator = ResultAggregator()
    sorted_records, statistics, merged_errors, warnings = aggregator.aggregate(
        records, all_errors, validated.sort_by
    )

    # 6. 导出
    exporter = ExcelResultExporter(ExcelWriter())
    export_outcome = exporter.export(sorted_records, work_dir=validated.work_dir)
    export_path: str | None = None
    if export_outcome.error:
        merged_errors.append(export_outcome.error)
        logger.log_export(export_outcome.error.url, False)
    else:
        export_path = export_outcome.file_path
        logger.log_export(export_path, True)

    logger.log_task_end(statistics)

    return ExtractResult(
        result_set=sorted_records,
        statistics=statistics,
        errors=merged_errors,
        warnings=warnings,
        task_id=task_id,
        export_path=export_path,
    )


def extract(request: ExtractRequest) -> ExtractResult:
    """同步主入口：包装 extract_async。"""
    return asyncio.run(extract_async(request))
