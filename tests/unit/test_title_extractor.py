"""TitleExtractor 单元测试（T11.02）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from yarl import URL

from url_link_extractor.core.title_extractor import TitleExtractor
from url_link_extractor.exceptions import HttpError, InsecureUrlError, ParseError
from url_link_extractor.exceptions import TimeoutError as ExtractorTimeoutError
from url_link_extractor.infra.protocols import FetchResponse
from url_link_extractor.models.enums import ErrorCode, RecordStatus


def _make_fetcher(response=None, exc=None):
    fetcher = MagicMock()
    if exc:
        fetcher.fetch = AsyncMock(side_effect=exc)
    else:
        fetcher.fetch = AsyncMock(return_value=response)
    return fetcher


def _make_parser(title=None, exc=None):
    parser = MagicMock()
    if exc:
        parser.extract_title = MagicMock(side_effect=exc)
    else:
        parser.extract_title = MagicMock(return_value=title)
    return parser


URL_A = URL("https://example.com/a.html")


class TestExtract:
    async def test_success(self):
        fetcher = _make_fetcher(FetchResponse(200, URL_A, "<html><title>T</title></html>", "text/html"))
        parser = _make_parser(title="T")
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A])
        assert records[0].status == RecordStatus.SUCCESS
        assert records[0].title == "T"
        assert errors == []

    async def test_no_title(self):
        fetcher = _make_fetcher(FetchResponse(200, URL_A, "<html></html>", "text/html"))
        parser = _make_parser(title=None)
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A])
        assert records[0].status == RecordStatus.NO_TITLE
        assert records[0].title is None
        assert errors[0].error_code == ErrorCode.NO_TITLE

    async def test_timeout(self):
        fetcher = _make_fetcher(exc=ExtractorTimeoutError("timeout"))
        parser = _make_parser()
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A])
        assert records[0].status == RecordStatus.FAILED
        assert errors[0].error_code == ErrorCode.TIMEOUT

    async def test_http_error_4xx(self):
        fetcher = _make_fetcher(exc=HttpError("HTTP 404"))
        parser = _make_parser()
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A])
        assert records[0].status == RecordStatus.FAILED
        assert errors[0].error_code == ErrorCode.HTTP_ERROR

    async def test_insecure_url(self):
        fetcher = _make_fetcher(exc=InsecureUrlError("http"))
        parser = _make_parser()
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A])
        assert records[0].status == RecordStatus.FAILED
        assert errors[0].error_code == ErrorCode.HTTP_ERROR

    async def test_parse_error(self):
        fetcher = _make_fetcher(FetchResponse(200, URL_A, "bad", "text/html"))
        parser = _make_parser(exc=ParseError("parse fail"))
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A])
        assert records[0].status == RecordStatus.FAILED
        assert errors[0].error_code == ErrorCode.PARSE_ERROR

    async def test_single_failure_does_not_abort(self):
        url_b = URL("https://example.com/b.html")
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            side_effect=[
                HttpError("500"),
                FetchResponse(200, url_b, "<html><title>B</title></html>", "text/html"),
            ]
        )
        parser = _make_parser(title="B")
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A, url_b])
        assert len(records) == 2
        assert records[0].status == RecordStatus.FAILED
        assert records[1].status == RecordStatus.SUCCESS

    async def test_concurrency_limit(self):
        urls = [URL(f"https://example.com/{i}.html") for i in range(10)]
        fetcher = MagicMock()
        fetcher.fetch = AsyncMock(
            return_value=FetchResponse(200, URL_A, "<html><title>T</title></html>", "text/html")
        )
        parser = _make_parser(title="T")
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract(urls, concurrency=2)
        assert len(records) == 10
        assert all(r.status == RecordStatus.SUCCESS for r in records)

    async def test_h1_not_used_as_title(self):
        # parser.extract_title 返回 None（因 <title> 缺失），不取 <h1>
        fetcher = _make_fetcher(FetchResponse(200, URL_A, "<html><body><h1>H</h1></body></html>", "text/html"))
        parser = _make_parser(title=None)
        extractor = TitleExtractor(fetcher, parser)
        records, errors = await extractor.extract([URL_A])
        assert records[0].status == RecordStatus.NO_TITLE
