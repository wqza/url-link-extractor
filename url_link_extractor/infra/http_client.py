"""HttpClient httpx 封装（设计 §2.2.2-3、spec.md §4.3-1）。

约束：
- 强制 HTTPS，HTTP 明文抛 InsecureUrlError
- 集成 SsrfGuard 进行 IP 锁定
- 超时 10s、重试上限 3、退避指数递增、重定向跳数上限 5
- 4xx 不重试，5xx/重置/超时重试
"""

from __future__ import annotations

import asyncio

import httpx
from yarl import URL

from ..exceptions import (
    HttpError,
    InsecureUrlError,
    RedirectLoopError,
)
from ..exceptions import (
    TimeoutError as ExtractorTimeoutError,
)
from ..infra.logger import TaskLogger
from ..infra.protocols import FetchResponse
from ..infra.ssrf_guard import SsrfGuard

_DEFAULT_UA = "url-link-extractor/0.1 (+https://github.com/loopy1997/url-link-extractor)"


class HttpxFetcher:
    """httpx 异步 HTTP 拉取器。"""

    def __init__(
        self,
        ssrf_guard: SsrfGuard,
        logger: TaskLogger | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        max_redirects: int = 5,
        follow_redirect: bool = True,
        user_agent: str = _DEFAULT_UA,
    ) -> None:
        self._ssrf = ssrf_guard
        self._logger = logger
        self._timeout = timeout
        self._max_retries = max_retries
        self._max_redirects = max_redirects
        self._follow_redirect = follow_redirect
        self._ua = user_agent

    async def fetch(
        self, url: URL, *, timeout: float | None = None, follow_redirect: bool | None = None
    ) -> FetchResponse:
        """拉取 URL，返回 FetchResponse。

        - 强制 HTTPS
        - SsrfGuard IP 锁定
        - 5xx/超时重试（指数退避），4xx 不重试
        """
        if url.scheme.lower() != "https":
            raise InsecureUrlError(f"非 HTTPS 协议：{url}")

        effective_timeout = timeout if timeout is not None else self._timeout
        effective_follow = follow_redirect if follow_redirect is not None else self._follow_redirect

        # SSRF 校验（IP 锁定）
        host = url.host or ""
        await self._ssrf.check_and_resolve(host)

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=effective_timeout,
                    follow_redirects=effective_follow,
                    max_redirects=self._max_redirects,
                    trust_env=False,
                ) as client:
                    resp = await client.get(
                        str(url),
                        headers={"User-Agent": self._ua},
                    )
                    status = resp.status_code
                    if self._logger:
                        self._logger.log_request(str(url), status)
                    content_type = resp.headers.get("content-type")
                    if 200 <= status < 300:
                        return FetchResponse(
                            status=status,
                            final_url=URL(str(resp.url)),
                            body=resp.text,
                            content_type=content_type,
                        )
                    if 400 <= status < 500:
                        # 4xx 不重试，立即抛出
                        raise HttpError(f"HTTP {status} {url}")
                    # 5xx：可重试
                    last_exc = HttpError(f"HTTP {status} {url}")
            except httpx.TimeoutException as exc:
                last_exc = ExtractorTimeoutError(f"超时 {url}: {exc}")
            except httpx.TooManyRedirects as exc:
                raise RedirectLoopError(f"重定向超限 {url}: {exc}") from exc
            except HttpError as exc:
                # 4xx HttpError 含 "HTTP 4" 前缀，立即抛出；5xx 可重试
                if exc.detail and exc.detail.startswith("HTTP 4"):
                    raise
                last_exc = exc
            except httpx.ConnectError as exc:
                last_exc = HttpError(f"连接失败 {url}: {exc}")

            if attempt < self._max_retries:
                await asyncio.sleep(2**attempt)

        assert last_exc is not None
        raise last_exc
