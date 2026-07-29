"""infra 层 Protocol 接口定义（设计 §2.2.2）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from yarl import URL


@dataclass(frozen=True)
class FetchResponse:
    """HTTP 拉取响应。"""

    status: int
    final_url: URL
    body: str
    content_type: str | None = None


class HttpFetcher(Protocol):
    """HTTP 拉取器协议（设计 §2.2.2-3）。"""

    async def fetch(
        self, url: URL, *, timeout: float, follow_redirect: bool
    ) -> FetchResponse: ...


class HtmlParser(Protocol):
    """HTML 解析器协议（设计 §2.2.2-4）。"""

    def extract_links(self, html: str, base: URL) -> list[URL]: ...

    def extract_title(self, html: str) -> str | None: ...


class EntryResolver(Protocol):
    """发现入口解析器协议（设计 §2.2.2-2）。"""

    async def resolve(
        self, prefix: URL, explicit_entries: list[URL] | None = None
    ) -> list[URL]: ...


class ResultExporter(Protocol):
    """结果导出器协议（设计 §2.2.2-5）。"""

    async def export(self, result_set: list, work_dir) -> object: ...
