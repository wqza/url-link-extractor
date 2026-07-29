"""SsrfGuard SSRF 防护与 IP 锁定（spec.md §4.3-2、设计 §1.2 约束归纳-1）。

链路：DNS 解析 → IP 校验 → 返回 IP 供 HttpClient 连接前锁定（防 DNS 重绑定）。
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket

from ..exceptions import SsrfBlockedError


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    """判断 IP 是否属于禁止段。"""
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


class SsrfGuard:
    """SSRF 防护器。"""

    async def check_and_resolve(self, host: str) -> str:
        """解析 host 为 IP 并校验，返回通过校验的 IP 字符串。

        - 使用 getaddrinfo 解析主机
        - 拒绝内网/回环/链路本地/保留/组播地址
        - DNS 解析失败抛 SsrfBlockedError
        """
        if not host:
            raise SsrfBlockedError("host 为空")

        # 若 host 已是 IP 字面量，直接校验
        try:
            ip = ipaddress.ip_address(host)
            if _is_blocked_ip(ip):
                raise SsrfBlockedError(f"禁止访问的 IP 地址：{host}")
            return str(ip)
        except ValueError:
            pass

        # DNS 解析
        loop = asyncio.get_event_loop()
        try:
            infos = await loop.getaddrinfo(host, None)
        except socket.gaierror as exc:
            raise SsrfBlockedError(f"DNS 解析失败：{host} ({exc})") from exc

        for info in infos:
            addr = info[4][0]
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            if _is_blocked_ip(ip):
                raise SsrfBlockedError(f"解析到禁止地址：{host} -> {addr}")
            return str(ip)

        raise SsrfBlockedError(f"无可用 IP 地址：{host}")

    def is_blocked(self, host: str) -> bool:
        """同步纯判定（不解析 DNS，仅对 IP 字串校验）。"""
        if not host:
            return True
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return False
        return _is_blocked_ip(ip)
