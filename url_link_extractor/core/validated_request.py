"""core 层内部值对象：校验后的请求。"""

from __future__ import annotations

from dataclasses import dataclass

from yarl import URL

from ..models.enums import SortBy


@dataclass(frozen=True)
class ValidatedRequest:
    """PrefixValidator 校验通过后的规范化请求。"""

    prefix: URL
    entry_urls: list[URL] | None
    allow_cross_subdomain: bool
    follow_redirect: bool
    concurrency: int
    sort_by: SortBy
    work_dir: str | None
    warnings: list[str]
