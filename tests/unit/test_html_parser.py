"""HtmlParser 单元测试（T7.02）。"""

from __future__ import annotations

import pytest
from yarl import URL

from url_link_extractor.infra.html_parser import SelectolaxHtmlParser


@pytest.fixture
def parser():
    return SelectolaxHtmlParser()


class TestExtractTitle:
    def test_basic_title(self, parser):
        assert parser.extract_title("<html><head><title>什么是码道CLI</title></head></html>") == "什么是码道CLI"

    def test_whitespace_normalize(self, parser):
        # spec.md §5.2.1-2a
        assert parser.extract_title("<title>  什么是\n码道CLI  </title>") == "什么是 码道CLI"

    def test_multi_title_first_nonempty(self, parser):
        html = "<title></title><title>第二个</title><title>第三个</title>"
        assert parser.extract_title(html) == "第二个"

    def test_no_title(self, parser):
        assert parser.extract_title("<html><body>无标题</body></html>") is None

    def test_empty_title(self, parser):
        assert parser.extract_title("<title>   </title>") is None

    def test_og_title_not_used(self, parser):
        # spec.md §5.2.1-5a：无 <title> 但有 og:title → None
        html = '<html><head><meta property="og:title" content="OG标题"></head></html>'
        assert parser.extract_title(html) is None

    def test_h1_not_used(self, parser):
        html = "<html><body><h1>H1标题</h1></body></html>"
        assert parser.extract_title(html) is None

    def test_truncate_500(self, parser):
        long_title = "A" * 600
        result = parser.extract_title(f"<title>{long_title}</title>")
        assert len(result) == 500

    def test_empty_html(self, parser):
        assert parser.extract_title("") is None


class TestNormalizeTitle:
    def test_basic(self, parser):
        assert parser.normalize_title("  什么是\n码道CLI  ") == "什么是 码道CLI"

    def test_tabs(self, parser):
        assert parser.normalize_title("a\t\tb") == "a b"

    def test_truncate(self, parser):
        assert len(parser.normalize_title("A" * 600)) == 500

    def test_empty(self, parser):
        assert parser.normalize_title("") == ""


class TestExtractLinks:
    def test_absolute_links(self, parser):
        base = URL("https://example.com/p/")
        html = '<a href="https://example.com/p/a.html">A</a><a href="https://example.com/p/b.html">B</a>'
        links = parser.extract_links(html, base=base)
        assert links == [URL("https://example.com/p/a.html"), URL("https://example.com/p/b.html")]

    def test_relative_links(self, parser):
        base = URL("https://example.com/p/")
        html = '<a href="./a.html">A</a><a href="/b.html">B</a>'
        links = parser.extract_links(html, base=base)
        assert links == [URL("https://example.com/p/a.html"), URL("https://example.com/b.html")]

    def test_bare_filename(self, parser):
        base = URL("https://example.com/p/")
        links = parser.extract_links('<a href="c.html">C</a>', base=base)
        assert links == [URL("https://example.com/p/c.html")]

    def test_filter_javascript(self, parser):
        base = URL("https://example.com/")
        links = parser.extract_links('<a href="javascript:void(0)">X</a><a href="a.html">A</a>', base=base)
        assert links == [URL("https://example.com/a.html")]

    def test_filter_mailto(self, parser):
        base = URL("https://example.com/")
        links = parser.extract_links('<a href="mailto:a@b.com">X</a>', base=base)
        assert links == []

    def test_filter_ftp(self, parser):
        base = URL("https://example.com/")
        links = parser.extract_links('<a href="ftp://example.com/file">X</a>', base=base)
        assert links == []

    def test_filter_anchor(self, parser):
        base = URL("https://example.com/")
        links = parser.extract_links('<a href="#section">X</a>', base=base)
        assert links == []

    def test_output_absolute_no_relative_markers(self, parser):
        base = URL("https://example.com/p/")
        links = parser.extract_links('<a href="./a.html">A</a>', base=base)
        for link in links:
            s = str(link)
            assert "./" not in s
            assert "..." not in s
            assert link.scheme == "https"
            assert link.host is not None

    def test_empty_html(self, parser):
        assert parser.extract_links("", base=URL("https://example.com/")) == []
