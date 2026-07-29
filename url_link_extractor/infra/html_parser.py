"""HtmlParser selectolax 封装（设计 §2.2.2-4、spec.md §5.1.1/§5.2.1）。

约束：
- extract_links：提取 <a href>，经 UrlNormalizer 绝对化，过滤协议白名单
- extract_title：取第一个非空 <title>，规整空白，截断 500 字符
- 禁止以 <h1>/og:title/文档首行替代 <title>
"""

from __future__ import annotations

from selectolax.parser import HTMLParser as _SelectolaxParser
from yarl import URL

from ..exceptions import ParseError
from ..infra.url_normalizer import UrlNormalizer

_TITLE_MAX_LEN = 500
_PROTOCOL_WHITELIST = {"http", "https"}


class SelectolaxHtmlParser:
    """selectolax HTML 解析器封装。"""

    def __init__(self, normalizer: UrlNormalizer | None = None) -> None:
        self._norm = normalizer or UrlNormalizer()

    def extract_links(self, html: str, base: URL) -> list[URL]:
        """提取所有 <a href> 并转为绝对完整 URL。

        - 过滤协议白名单外的链接（javascript:、mailto:、ftp: 等）
        - 解析异常时抛 ParseError
        """
        if not html:
            return []
        try:
            parser = _SelectolaxParser(html)
        except Exception as exc:
            raise ParseError(f"HTML 解析失败：{exc}") from exc

        result: list[URL] = []
        for node in parser.css("a[href]"):
            href = node.attributes.get("href")
            if not href:
                continue
            href = href.strip()
            if not href:
                continue
            # 协议白名单过滤
            try:
                lower = href.lower()
                if lower.startswith(("javascript:", "mailto:", "ftp:", "tel:", "data:", "#")):
                    continue
            except Exception:
                continue
            try:
                url = self._norm.normalize(href, base=base)
            except Exception:
                continue
            if url.scheme.lower() in _PROTOCOL_WHITELIST:
                result.append(url)
        return result

    def extract_title(self, html: str) -> str | None:
        """提取第一个非空 <title> 文本，规整后返回。

        - 无 <title> 或全空白返回 None
        - 禁止使用 <h1>/og:title 等替代
        """
        if not html:
            return None
        try:
            parser = _SelectolaxParser(html)
        except Exception as exc:
            raise ParseError(f"HTML 解析失败：{exc}") from exc

        for node in parser.css("title"):
            raw = node.text(strip=True)
            if raw:
                return self.normalize_title(raw)
        return None

    def normalize_title(self, raw: str) -> str:
        """规整标题：首尾去空白，内部连续空白合并为单空格，超 500 截断。"""
        if not raw:
            return ""
        normalized = " ".join(raw.split())
        if len(normalized) > _TITLE_MAX_LEN:
            normalized = normalized[:_TITLE_MAX_LEN]
        return normalized
