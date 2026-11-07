from email.utils import formatdate

import pytest
import requests
import urllib3
from cachecontrol import CacheControl

import responses


@pytest.mark.parametrize("callback", [False, True])
@pytest.mark.parametrize("body", [b"", b"cached response body"])
@pytest.mark.parametrize("read_method", ["content", "stream", "raw"])
@pytest.mark.parametrize("content_length", [False, True])
def test_cachecontrol_caches_consumed_response(
    callback: bool, body: bytes, read_method: str, content_length: bool
) -> None:
    url = "http://example.test/cached"
    headers = {"Cache-Control": "max-age=3600", "Date": formatdate(usegmt=True)}
    if content_length:
        headers["Content-Length"] = str(len(body))
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        if callback:
            mock.add_callback(
                responses.GET, url, callback=lambda request: (200, headers, body)
            )
        else:
            mock.add(responses.GET, url, body=body, headers=headers)
        with CacheControl(requests.Session()) as session:
            first = session.get(url, stream=True)
            assert not getattr(first, "from_cache")
            if read_method == "content":
                received = first.content
            elif read_method == "stream":
                received = b"".join(first.iter_content(chunk_size=3))
            else:
                received = first.raw.read()
            assert received == body
            mock.add(responses.GET, url, body=requests.ConnectionError("not cached"))
            second = session.get(url)
            assert getattr(second, "from_cache")
            assert second.content == body
            assert len(mock.calls) == 1


def test_cachecontrol_waits_for_stream_consumption() -> None:
    url = "http://example.test/stream"
    body = b"one-two-three"
    headers = {"Cache-Control": "max-age=3600", "Date": formatdate(usegmt=True)}
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add(responses.GET, url, body=body, headers=headers)
        with CacheControl(requests.Session()) as session:
            first = session.get(url, stream=True)
            chunks = first.iter_content(chunk_size=3)
            start = next(chunks)
            mock.add(responses.GET, url, body=requests.ConnectionError("not cached"))
            with pytest.raises(requests.ConnectionError, match="not cached"):
                session.get(url)
            assert start + b"".join(chunks) == body
            assert getattr(session.get(url), "from_cache")
            assert len(mock.calls) == 2


def test_cachecontrol_preserves_no_store() -> None:
    url = "http://example.test/no-store"
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add(responses.GET, url, body="body", headers={"Cache-Control": "no-store"})
        with CacheControl(requests.Session()) as session:
            assert session.get(url).content == b"body"
            mock.add(responses.GET, url, body=requests.ConnectionError("not cached"))
            with pytest.raises(requests.ConnectionError, match="not cached"):
                session.get(url)


@pytest.mark.parametrize("stream", [False, True])
def test_cachecontrol_preserves_incomplete_read(
    stream: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_init = urllib3.HTTPResponse.__init__

    def enforce_length(self, *args, **kwargs):
        kwargs["enforce_content_length"] = True
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(urllib3.HTTPResponse, "__init__", enforce_length)
    url = "http://example.test/incomplete"
    headers = {
        "Cache-Control": "max-age=3600",
        "Date": formatdate(usegmt=True),
        "Content-Length": "100",
    }
    with responses.RequestsMock() as mock:
        mock.add(responses.GET, url, body=b"short", headers=headers)
        with CacheControl(requests.Session()) as session:
            with pytest.raises(requests.exceptions.ChunkedEncodingError):
                response = session.get(url, stream=stream)
                if stream:
                    b"".join(response.iter_content(chunk_size=1))
