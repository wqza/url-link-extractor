"""ExtractRequest 请求领域对象（spec.md §6.1、设计 §2.3.2）。

使用 frozen dataclass 保证请求不可变。
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import SortBy


@dataclass(frozen=True)
class ExtractRequest:
    """提取请求。

    字段对齐 spec.md §6.1：
    - url_prefix：必填，合法 HTTPS URL 前缀，长度 ≤ 2048
    - entry_urls：可选，字符串列表，每项合法 URL，大小 ≤ 20
    - allow_cross_subdomain：默认 False
    - follow_redirect：默认 True，重定向跳数上限 5
    - concurrency：默认 5，范围 [1, 20]
    - sort_by：默认 SortBy.URL
    - work_dir：可选，result.xlsx 工作目录；None 表示当前目录
    """

    url_prefix: str
    entry_urls: list[str] | None = None
    allow_cross_subdomain: bool = False
    follow_redirect: bool = True
    concurrency: int = 5
    sort_by: SortBy = SortBy.URL
    work_dir: str | None = None
