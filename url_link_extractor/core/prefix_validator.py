"""PrefixValidator 参数校验与规范化（spec.md §5.1.3-1、§6.1）。

非法时抛 InvalidPrefixError，不发起任何网络请求。
concurrency 超出 [1,20] 钳制到边界并记录告警。
"""

from __future__ import annotations

from yarl import URL

from ..exceptions import InvalidPrefixError
from ..infra.url_normalizer import UrlNormalizer
from ..models.request import ExtractRequest
from .validated_request import ValidatedRequest

_MAX_PREFIX_LEN = 2048
_MAX_ENTRY_COUNT = 20
_CONCURRENCY_MIN = 1
_CONCURRENCY_MAX = 20


class PrefixValidator:
    """请求参数校验器。"""

    def __init__(self, normalizer: UrlNormalizer | None = None) -> None:
        self._norm = normalizer or UrlNormalizer()

    def validate(self, request: ExtractRequest) -> ValidatedRequest:
        """校验并规范化请求。"""
        warnings: list[str] = []

        # url_prefix 校验
        prefix_str = request.url_prefix
        if not prefix_str or not isinstance(prefix_str, str):
            raise InvalidPrefixError("url_prefix 为空或非字符串")
        if len(prefix_str) > _MAX_PREFIX_LEN:
            raise InvalidPrefixError(f"url_prefix 长度超 {_MAX_PREFIX_LEN}")

        try:
            prefix_url = self._norm.normalize(prefix_str)
        except InvalidPrefixError:
            raise
        if prefix_url.scheme.lower() != "https":
            raise InvalidPrefixError(f"url_prefix 必须为 HTTPS：{prefix_str}")

        # entry_urls 校验
        entry_urls: list[URL] | None = None
        if request.entry_urls is not None:
            if len(request.entry_urls) > _MAX_ENTRY_COUNT:
                raise InvalidPrefixError(f"entry_urls 数量超 {_MAX_ENTRY_COUNT}")
            entry_urls = []
            for entry in request.entry_urls:
                try:
                    url = self._norm.normalize(entry)
                except InvalidPrefixError:
                    raise
                if url.scheme.lower() != "https":
                    raise InvalidPrefixError(f"entry_url 必须 HTTPS：{entry}")
                entry_urls.append(url)

        # concurrency 钳制
        concurrency = request.concurrency
        if concurrency < _CONCURRENCY_MIN:
            warnings.append(f"concurrency={concurrency} 钳制为 {_CONCURRENCY_MIN}")
            concurrency = _CONCURRENCY_MIN
        elif concurrency > _CONCURRENCY_MAX:
            warnings.append(f"concurrency={concurrency} 钳制为 {_CONCURRENCY_MAX}")
            concurrency = _CONCURRENCY_MAX

        return ValidatedRequest(
            prefix=prefix_url,
            entry_urls=entry_urls,
            allow_cross_subdomain=request.allow_cross_subdomain,
            follow_redirect=request.follow_redirect,
            concurrency=concurrency,
            sort_by=request.sort_by,
            work_dir=request.work_dir,
            warnings=warnings,
        )
