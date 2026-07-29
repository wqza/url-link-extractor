"""SsrfGuard 单元测试（T5.02）。"""

from __future__ import annotations

import asyncio
import socket
from unittest.mock import patch

import pytest

from url_link_extractor.exceptions import SsrfBlockedError
from url_link_extractor.infra.ssrf_guard import SsrfGuard


@pytest.fixture
def guard():
    return SsrfGuard()


class TestIsBlocked:
    @pytest.mark.parametrize(
        "ip",
        ["127.0.0.1", "10.0.0.1", "192.168.1.1", "169.254.1.1", "::1", "0.0.0.0", "224.0.0.1"],
    )
    def test_blocked_ips(self, guard, ip):
        assert guard.is_blocked(ip) is True

    @pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1", "140.82.112.4"])
    def test_public_ips(self, guard, ip):
        assert guard.is_blocked(ip) is False

    def test_hostname_not_ip(self, guard):
        # 非字面 IP 返回 False（is_blocked 不做 DNS）
        assert guard.is_blocked("example.com") is False


class TestCheckAndResolve:
    @pytest.mark.parametrize(
        "ip",
        ["127.0.0.1", "10.0.0.1", "192.168.1.1", "169.254.1.1", "::1"],
    )
    async def test_blocked_ip_literal(self, guard, ip):
        with pytest.raises(SsrfBlockedError):
            await guard.check_and_resolve(ip)

    async def test_public_ip_literal(self, guard):
        assert await guard.check_and_resolve("8.8.8.8") == "8.8.8.8"

    async def test_dns_rebinding_blocked(self, guard):
        loop = asyncio.get_event_loop()
        async def fake_getaddrinfo(host, port, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]
        with patch.object(loop, "getaddrinfo", side_effect=fake_getaddrinfo):
            with pytest.raises(SsrfBlockedError):
                await guard.check_and_resolve("example.com")

    async def test_dns_resolve_public(self, guard):
        loop = asyncio.get_event_loop()
        async def fake_getaddrinfo(host, port, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        with patch.object(loop, "getaddrinfo", side_effect=fake_getaddrinfo):
            assert await guard.check_and_resolve("example.com") == "93.184.216.34"

    async def test_dns_failure(self, guard):
        loop = asyncio.get_event_loop()
        async def fake_getaddrinfo(host, port, **kwargs):
            raise socket.gaierror("DNS 失败")
        with patch.object(loop, "getaddrinfo", side_effect=fake_getaddrinfo):
            with pytest.raises(SsrfBlockedError):
                await guard.check_and_resolve("nonexistent.invalid")

    async def test_empty_host(self, guard):
        with pytest.raises(SsrfBlockedError):
            await guard.check_and_resolve("")
