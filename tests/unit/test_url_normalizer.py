"""UrlNormalizer 单元测试（T4.02）。"""

from __future__ import annotations

import pytest
from yarl import URL

from url_link_extractor.exceptions import InvalidPrefixError
from url_link_extractor.infra.url_normalizer import UrlNormalizer


@pytest.fixture
def norm():
    return UrlNormalizer()


class TestNormalize:
    def test_relative_with_base(self, norm):
        base = URL("https://h.com/p/")
        assert norm.normalize("./x.html", base=base) == URL("https://h.com/p/x.html")

    def test_absolute_path_with_base(self, norm):
        base = URL("https://h.com/x/")
        assert norm.normalize("/a/b.html", base=base) == URL("https://h.com/a/b.html")

    def test_bare_filename_with_prefix_base(self, norm):
        # spec.md §5.1.1-6a 验收用例
        prefix = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/")
        result = norm.normalize("codeartsagent_cli_0001.html", base=prefix)
        assert result == URL(
            "https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/codeartsagent_cli_0001.html"
        )
        assert "..." not in str(result)

    def test_already_absolute(self, norm):
        assert norm.normalize("https://h.com/a.html") == URL("https://h.com/a.html")

    def test_empty_raises(self, norm):
        with pytest.raises(InvalidPrefixError):
            norm.normalize("")

    def test_relative_no_base_raises(self, norm):
        with pytest.raises(InvalidPrefixError):
            norm.normalize("./x.html")

    def test_output_no_ellipsis(self, norm):
        base = URL("https://h.com/p/")
        result = norm.normalize("y.html", base=base)
        assert "..." not in str(result)
        assert "./" not in str(result)


class TestIsAbsoluteComplete:
    def test_https_with_path(self, norm):
        assert norm.is_absolute_complete(URL("https://h.com/a.html")) is True

    def test_http_rejected(self, norm):
        assert norm.is_absolute_complete(URL("http://h.com/a.html")) is False

    def test_root_path_is_valid(self, norm):
        # yarl 中 https://h.com 的 path 为 "/"，视为非空有效
        assert norm.is_absolute_complete(URL("https://h.com")) is True


class TestStartsWithPrefix:
    def test_match(self, norm):
        prefix = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/")
        url = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/codeartsagent_cli_0001.html")
        assert norm.starts_with_prefix(url, prefix) is True

    def test_no_match(self, norm):
        prefix = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/")
        url = URL("https://support.huaweicloud.com/intl/zh-cn/other.html")
        assert norm.starts_with_prefix(url, prefix) is False

    def test_char_by_char(self, norm):
        # 逐字符比较，非域名匹配
        prefix = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/")
        url = URL("https://support.huaweicloud.com/intl/zh-cn/usermanual-cli-other.html")
        assert norm.starts_with_prefix(url, prefix) is False


class TestExtractMainDomain:
    def test_multi_subdomain(self, norm):
        assert norm.extract_main_domain(URL("https://support.huaweicloud.com/")) == "huaweicloud.com"

    def test_two_parts(self, norm):
        assert norm.extract_main_domain(URL("https://example.com/")) == "example.com"

    def test_ipv4(self, norm):
        assert norm.extract_main_domain(URL("https://8.8.8.8/")) == "8.8.8.8"

    def test_localhost(self, norm):
        assert norm.extract_main_domain(URL("https://localhost/")) == "localhost"


class TestSameDomain:
    def test_same_main_domain(self, norm):
        a = URL("https://support.huaweicloud.com/")
        b = URL("https://console.huaweicloud.com/")
        assert norm.is_same_main_domain(a, b) is True

    def test_diff_main_domain(self, norm):
        a = URL("https://support.huaweicloud.com/")
        b = URL("https://other.example.com/")
        assert norm.is_same_main_domain(a, b) is False

    def test_same_subdomain(self, norm):
        a = URL("https://support.huaweicloud.com/")
        b = URL("https://support.huaweicloud.com/")
        assert norm.is_same_subdomain(a, b) is True

    def test_diff_subdomain(self, norm):
        a = URL("https://support.huaweicloud.com/")
        b = URL("https://console.huaweicloud.com/")
        assert norm.is_same_subdomain(a, b) is False
