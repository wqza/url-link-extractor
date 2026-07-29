"""PrefixValidator 单元测试（T9.02）。"""

from __future__ import annotations

import pytest

from url_link_extractor.core.prefix_validator import PrefixValidator
from url_link_extractor.exceptions import InvalidPrefixError
from url_link_extractor.models.enums import SortBy
from url_link_extractor.models.request import ExtractRequest


@pytest.fixture
def validator():
    return PrefixValidator()


class TestValidate:
    def test_valid_https(self, validator):
        req = ExtractRequest(url_prefix="https://example.com/p/")
        result = validator.validate(req)
        assert str(result.prefix) == "https://example.com/p/"
        assert result.concurrency == 5

    def test_empty_prefix(self, validator):
        with pytest.raises(InvalidPrefixError):
            validator.validate(ExtractRequest(url_prefix=""))

    def test_non_https(self, validator):
        with pytest.raises(InvalidPrefixError):
            validator.validate(ExtractRequest(url_prefix="http://example.com/p/"))

    def test_too_long(self, validator):
        with pytest.raises(InvalidPrefixError):
            validator.validate(ExtractRequest(url_prefix="https://x.com/" + "a" * 2048))

    def test_concurrency_clamp_low(self, validator):
        req = ExtractRequest(url_prefix="https://x.com/", concurrency=0)
        result = validator.validate(req)
        assert result.concurrency == 1
        assert len(result.warnings) == 1

    def test_concurrency_clamp_high(self, validator):
        req = ExtractRequest(url_prefix="https://x.com/", concurrency=100)
        result = validator.validate(req)
        assert result.concurrency == 20
        assert len(result.warnings) == 1

    def test_concurrency_in_range(self, validator):
        req = ExtractRequest(url_prefix="https://x.com/", concurrency=10)
        result = validator.validate(req)
        assert result.concurrency == 10
        assert result.warnings == []

    def test_entry_urls_valid(self, validator):
        req = ExtractRequest(
            url_prefix="https://x.com/",
            entry_urls=["https://x.com/a", "https://y.com/b"],
        )
        result = validator.validate(req)
        assert len(result.entry_urls) == 2

    def test_entry_urls_too_many(self, validator):
        req = ExtractRequest(
            url_prefix="https://x.com/",
            entry_urls=[f"https://x.com/{i}" for i in range(21)],
        )
        with pytest.raises(InvalidPrefixError):
            validator.validate(req)

    def test_entry_url_non_https(self, validator):
        req = ExtractRequest(
            url_prefix="https://x.com/",
            entry_urls=["http://x.com/a"],
        )
        with pytest.raises(InvalidPrefixError):
            validator.validate(req)

    def test_sort_by_preserved(self, validator):
        req = ExtractRequest(url_prefix="https://x.com/", sort_by=SortBy.TITLE)
        result = validator.validate(req)
        assert result.sort_by == SortBy.TITLE
