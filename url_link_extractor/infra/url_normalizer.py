"""UrlNormalizer URL 规范化与绝对化（spec.md §5.1.1、设计 §1.1.3-B-9）。

本模块是绝对完整 URL 保障的核心：结果集、异常报告、result.xlsx URL 列的唯一 URL 形态出口。
"""

from __future__ import annotations

import ipaddress

from yarl import URL

from ..exceptions import InvalidPrefixError


class UrlNormalizer:
    """URL 规范化器，基于 yarl.URL。"""

    def normalize(self, raw: str, base: URL | None = None) -> URL:
        """将 raw 规范化为绝对完整 URL。

        - 若 raw 为相对路径，必须以 base.join 解析为绝对 URL
        - 输出必须含协议与主机
        - 任何输出均不含 ... 省略号或相对标记
        """
        if not raw or not isinstance(raw, str):
            raise InvalidPrefixError(f"非法 URL 输入：{raw!r}")

        raw_stripped = raw.strip()
        if not raw_stripped:
            raise InvalidPrefixError("URL 为空字符串")

        try:
            url = URL(raw_stripped)
        except Exception as exc:
            raise InvalidPrefixError(f"URL 解析失败：{raw!r} ({exc})") from exc

        is_absolute = bool(url.scheme) and bool(url.host)

        if not is_absolute:
            if base is None:
                raise InvalidPrefixError(f"相对路径无 base：{raw!r}")
            try:
                url = base.join(URL(raw_stripped))
            except Exception as exc:
                raise InvalidPrefixError(f"base.join 失败：{raw!r} base={base} ({exc})") from exc

        if not url.scheme or not url.host:
            raise InvalidPrefixError(f"规范化后仍非绝对 URL：{raw!r} -> {url}")

        return url

    def is_absolute_complete(self, url: URL) -> bool:
        """校验 URL 含非空 scheme（https）、非空 host、非空 path。"""
        return bool(url.scheme) and url.scheme.lower() == "https" and bool(url.host) and bool(url.path)

    def starts_with_prefix(self, url: URL, prefix: URL) -> bool:
        """逐字符比较 str(url) 是否以 str(prefix) 开头（spec.md §5.1.1-1）。"""
        return str(url).startswith(str(prefix))

    def extract_main_domain(self, url: URL) -> str:
        """提取主域：按 . 倒序取最后两段。

        - support.huaweicloud.com -> huaweicloud.com
        - IPv4 主机直接返回原值
        """
        host = url.host
        if host is None:
            return ""
        try:
            ipaddress.ip_address(host)
            return host
        except ValueError:
            pass
        parts = host.split(".")
        if len(parts) <= 2:
            return host
        return ".".join(parts[-2:])

    def is_same_main_domain(self, a: URL, b: URL) -> bool:
        """比较两个 URL 的主域是否相同。"""
        return self.extract_main_domain(a) == self.extract_main_domain(b)

    def is_same_subdomain(self, a: URL, b: URL) -> bool:
        """比较两个 URL 的完整 host 是否相同。"""
        return (a.host or "") == (b.host or "")
