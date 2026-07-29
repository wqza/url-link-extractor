"""CLI 命令行入口（T14.02）。"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from url_link_extractor.models.enums import SortBy
from url_link_extractor.models.request import ExtractRequest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="url-link-extractor",
        description="按 URL 前缀批量发现网页链接并提取 <title>，导出 result.xlsx",
    )
    parser.add_argument("--url-prefix", required=True, help="URL 前缀（必填，HTTPS）")
    parser.add_argument("--entry-url", action="append", default=None, help="发现入口 URL（可多次指定）")
    parser.add_argument("--allow-cross-subdomain", action="store_true", help="允许跨子域")
    parser.add_argument("--no-follow-redirect", action="store_true", help="不跟随重定向")
    parser.add_argument("--concurrency", type=int, default=5, help="并发度（1-20，默认 5）")
    parser.add_argument(
        "--sort-by",
        choices=[s.value for s in SortBy],
        default=SortBy.URL.value,
        help="排序方式（url/title/none，默认 url）",
    )
    parser.add_argument("--work-dir", default=None, help="result.xlsx 工作目录")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI 主入口。"""
    parser = _build_parser()
    args = parser.parse_args(argv)

    request = ExtractRequest(
        url_prefix=args.url_prefix,
        entry_urls=args.entry_url,
        allow_cross_subdomain=args.allow_cross_subdomain,
        follow_redirect=not args.no_follow_redirect,
        concurrency=args.concurrency,
        sort_by=SortBy(args.sort_by),
        work_dir=args.work_dir,
    )

    from ..entry.extractor import extract

    try:
        result = extract(request)
    except Exception as exc:
        print(f"任务失败：{exc}", file=sys.stderr)
        return 1

    print(f"任务 ID：{result.task_id}")
    print(f"统计：total={result.statistics.total} success={result.statistics.success} "
          f"no_title={result.statistics.no_title} failed={result.statistics.failed}")
    if result.export_path:
        print(f"已导出：{result.export_path}")
    else:
        print("未导出 result.xlsx")
    for record in result.result_set:
        status_label = record.status.value
        title_display = record.title or "(缺失)"
        print(f"  [{status_label}] {record.url}  |  {title_display}")
    if result.errors:
        print(f"异常报告（{len(result.errors)} 条）：")
        for err in result.errors:
            print(f"  [{err.error_code.value}] {err.url}  |  {err.detail or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
