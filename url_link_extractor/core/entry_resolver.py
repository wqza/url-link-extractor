"""EntryResolver 发现入口解析（设计 §2.1.3、§2.2.2-2）。

三级降级策略：
1. 前缀上一级目录页（prefix.parent）
2. 站点根 /sitemap.xml
3. /robots.txt 内 Sitemap 声明
全不可达抛 EntryUnreachableError。
"""

from __future__ import annotations

from yarl import URL

from ..exceptions import EntryUnreachableError
from ..infra.protocols import HttpFetcher


class DefaultEntryResolver:
    """默认发现入口解析器。"""

    def __init__(self, fetcher: HttpFetcher) -> None:
        self._fetcher = fetcher

    async def resolve(
        self, prefix: URL, explicit_entries: list[URL] | None = None
    ) -> list[URL]:
        """解析发现入口。"""
        if explicit_entries:
            return explicit_entries[:20]

        # 三级降级
        candidates = self._build_candidates(prefix)
        for candidate in candidates:
            try:
                resp = await self._fetcher.fetch(candidate, timeout=10.0, follow_redirect=True)
                if 200 <= resp.status < 300:
                    return [candidate]
            except Exception:
                continue

        raise EntryUnreachableError(f"全部发现入口不可达：{candidates}")

    def _build_candidates(self, prefix: URL) -> list[URL]:
        """构建三级降级候选入口。"""
        candidates: list[URL] = []

        # 候选1：前缀上一级目录页
        parent = prefix.parent
        if parent and str(parent) != str(prefix):
            candidates.append(parent)

        # 候选2：站点根 /sitemap.xml
        candidates.append(URL.build(scheme=prefix.scheme, host=prefix.host, path="/sitemap.xml"))

        # 候选3：/robots.txt
        candidates.append(URL.build(scheme=prefix.scheme, host=prefix.host, path="/robots.txt"))

        return candidates
