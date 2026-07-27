from pathlib import Path

import pytest
import requests
import tomli_w
import yaml

import responses
from responses import _recorder
from responses._recorder import _dump
from responses._recorder import _remove_default_headers

try:
    import tomli as _toml
except ImportError:
    # python 3.11+
    import tomllib as _toml  # type: ignore[no-redef]


def get_data(host, port):
    data = {
        "responses": [
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/404",
                    "headers": {"x": "foo"},
                    "body": "404 Not Found",
                    "status": 404,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/status/wrong",
                    "headers": {"x": "foo"},
                    "body": "Invalid status code",
                    "status": 400,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/500",
                    "headers": {"x": "foo"},
                    "body": "500 Internal Server Error",
                    "status": 500,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "PUT",
                    "url": f"http://{host}:{port}/202",
                    "body": "OK",
                    "status": 202,
                    "content_type": "image/tiff",
                    "auto_calculate_content_length": False,
                }
            },
        ]
    }
    return data


def test_remove_default_headers_is_case_insensitive():
    """Default headers should be stripped regardless of their case.

    HTTP/2 servers send header names in lowercase, so the recorded file may
    contain e.g. ``content-type`` / ``date`` rather than ``Content-Type`` /
    ``Date``. These still need to be removed, otherwise the recorded file
    keeps verbose default headers (and, for content-type, a value that is
    already stored in the ``content_type`` field).
    """
    data = {
        "responses": [
            {
                "response": {
                    # mixed lower/title/upper case to pin the case-insensitive contract
                    "headers": {
                        "content-type": "application/json",
                        "Date": "Mon, 01 Jan 2024 00:00:00 GMT",
                        "SERVER": "nginx",
                        "x-custom": "keep-me",
                    }
                }
            },
            {
                # a response whose headers are all default ones is left without a
                # "headers" key at all
                "response": {
                    "headers": {"content-length": "12", "connection": "keep-alive"}
                }
            },
        ]
    }

    result = _remove_default_headers(data)

    assert result["responses"][0]["response"]["headers"] == {"x-custom": "keep-me"}
    assert "headers" not in result["responses"][1]["response"]


def test_remove_default_headers_keeps_requested_headers():
    """Headers named in ``keep_headers`` survive the default-header stripping.

    Some consumers need a normally-stripped header in the recorded file, for
    example a ``Date`` value that is part of a signed response they later
    verify. Matching is case-insensitive so a lowercase HTTP/2 name is kept
    too, while the other default headers are still removed.
    """
    data = {
        "responses": [
            {
                "response": {
                    "headers": {
                        "date": "Mon, 01 Jan 2024 00:00:00 GMT",
                        "Server": "nginx",
                        "Content-Length": "12",
                        "x-custom": "keep-me",
                    }
                }
            },
        ]
    }

    result = _remove_default_headers(data, keep_headers=["Date"])

    assert result["responses"][0]["response"]["headers"] == {
        "date": "Mon, 01 Jan 2024 00:00:00 GMT",
        "x-custom": "keep-me",
    }


def test_remove_default_headers_accepts_a_single_string():
    """A bare string is treated as one header name, not a set of characters."""
    data = {
        "responses": [
            {"response": {"headers": {"Date": "d", "Server": "nginx"}}},
        ]
    }

    result = _remove_default_headers(data, keep_headers="Date")

    assert result["responses"][0]["response"]["headers"] == {"Date": "d"}


def test_remove_default_headers_keep_non_default_is_noop():
    """Naming a non-default header does not change which headers are stripped."""
    data = {
        "responses": [
            {"response": {"headers": {"Date": "d", "x-custom": "keep-me"}}},
        ]
    }

    result = _remove_default_headers(data, keep_headers=["x-custom"])

    assert result["responses"][0]["response"]["headers"] == {"x-custom": "keep-me"}


class TestRecord:
    def setup_method(self):
        self.out_file = Path("response_record")
        if self.out_file.exists():
            self.out_file.unlink()  # pragma: no cover

        assert not self.out_file.exists()

    def test_recorder(self, httpserver):
        url202, url400, url404, url500 = self.prepare_server(httpserver)

        def another():
            requests.get(url500)
            requests.put(url202)

        @_recorder.record(file_path=self.out_file)
        def run():
            requests.get(url404)
            requests.get(url400)
            another()

        run()

        with open(self.out_file) as file:
            data = yaml.safe_load(file)
        assert data == get_data(httpserver.host, httpserver.port)

    def test_recorder_keep_headers_preserves_date(self, httpserver):
        """``keep_headers`` keeps a normally-stripped header in the record.

        Reproduces the reported need to record the ``Date`` header so a signed
        response can be verified against the recording (issue #763). Without
        ``keep_headers`` the same header is stripped as a verbose default.
        """
        httpserver.expect_request("/signed").respond_with_data(
            "ok",
            status=200,
            content_type="text/plain",
            headers={"Date": "Mon, 01 Jan 2024 00:00:00 GMT"},
        )
        url = httpserver.url_for("/signed")

        @_recorder.record(file_path=self.out_file, keep_headers=["Date"])
        def run_kept():
            requests.get(url)

        run_kept()
        with open(self.out_file) as file:
            kept = yaml.safe_load(file)
        kept_headers = kept["responses"][0]["response"]["headers"]
        # The server owns the exact Date value, so assert the header survives
        # rather than pinning its contents.
        assert "Date" in kept_headers
        assert "2024" in kept_headers["Date"]

        self.out_file.unlink()

        @_recorder.record(file_path=self.out_file)
        def run_default():
            requests.get(url)

        run_default()
        with open(self.out_file) as file:
            default = yaml.safe_load(file)
        default_headers = default["responses"][0]["response"].get("headers", {})
        assert "Date" not in default_headers

    def test_recorder_toml(self, httpserver):
        custom_recorder = _recorder.Recorder()

        def dump_to_file(file_path, registered, *, keep_headers=None):
            with open(file_path, "wb") as file:
                _dump(
                    registered,
                    file,
                    tomli_w.dump,  # type: ignore[arg-type]
                    keep_headers=keep_headers,
                )

        custom_recorder.dump_to_file = dump_to_file  # type: ignore[assignment]

        url202, url400, url404, url500 = self.prepare_server(httpserver)

        def another():
            requests.get(url500)
            requests.put(url202)

        @custom_recorder.record(file_path=self.out_file)
        def run():
            requests.get(url404)
            requests.get(url400)
            another()

        run()

        with open(self.out_file, "rb") as file:
            data = _toml.load(file)

        assert data == get_data(httpserver.host, httpserver.port)

    def prepare_server(self, httpserver):
        httpserver.expect_request("/500").respond_with_data(
            "500 Internal Server Error",
            status=500,
            content_type="text/plain",
            headers={"x": "foo"},
        )
        httpserver.expect_request("/202").respond_with_data(
            "OK",
            status=202,
            content_type="image/tiff",
        )
        httpserver.expect_request("/404").respond_with_data(
            "404 Not Found",
            status=404,
            content_type="text/plain",
            headers={"x": "foo"},
        )
        httpserver.expect_request("/status/wrong").respond_with_data(
            "Invalid status code",
            status=400,
            content_type="text/plain",
            headers={"x": "foo"},
        )
        url500 = httpserver.url_for("/500")
        url202 = httpserver.url_for("/202")
        url404 = httpserver.url_for("/404")
        url400 = httpserver.url_for("/status/wrong")
        return url202, url400, url404, url500

    def test_use_recorder_without_decorator(self, httpserver):
        """I want to be able to record in the REPL."""
        url202, url400, url404, url500 = self.prepare_server(httpserver)

        _recorder.recorder.start()

        def another():
            requests.get(url500)
            requests.put(url202)

        def run():
            requests.get(url404)
            requests.get(url400)
            another()

        run()

        _recorder.recorder.stop()
        _recorder.recorder.dump_to_file(self.out_file)

        with open(self.out_file) as file:
            data = yaml.safe_load(file)
        assert data == get_data(httpserver.host, httpserver.port)

        # Now, we test that the recorder is properly reset
        assert _recorder.recorder.get_registry().registered
        _recorder.recorder.reset()
        assert not _recorder.recorder.get_registry().registered


class TestReplay:
    def setup_method(self):
        self.out_file = Path("response_record")

    def teardown_method(self):
        if self.out_file.exists():
            self.out_file.unlink()

        # Clean up any extension variants created by individual tests
        for suffix in (".yaml", ".toml"):
            p = Path(str(self.out_file) + suffix)
            if p.exists():
                p.unlink()

        assert not self.out_file.exists()

    @pytest.mark.parametrize("parser", (yaml, tomli_w))
    def test_add_from_file(self, parser):  # type: ignore[misc]
        if parser == yaml:
            with open(self.out_file, "w") as file:
                parser.dump(get_data("example.com", "8080"), file)
        else:
            with open(self.out_file, "wb") as file:  # type: ignore[assignment]
                parser.dump(get_data("example.com", "8080"), file)

        @responses.activate
        def run():
            responses.patch("http://httpbin.org")

            original_parser = responses.mock._parse_response_file
            if parser == tomli_w:

                def _parse_resp_f(file_path):
                    with open(file_path, "rb") as file:
                        data = _toml.load(file)
                    return data

                responses.mock._parse_response_file = _parse_resp_f  # type: ignore[method-assign]

            try:
                responses._add_from_file(file_path=self.out_file)
                responses.post("http://httpbin.org/form")

                assert responses.registered()[0].url == "http://httpbin.org/"
                assert responses.registered()[1].url == "http://example.com:8080/404"
                assert (
                    responses.registered()[2].url
                    == "http://example.com:8080/status/wrong"
                )
                assert responses.registered()[3].url == "http://example.com:8080/500"
                assert responses.registered()[4].url == "http://example.com:8080/202"
                assert responses.registered()[5].url == "http://httpbin.org/form"

                assert responses.registered()[0].method == "PATCH"
                assert responses.registered()[2].method == "GET"
                assert responses.registered()[4].method == "PUT"
                assert responses.registered()[5].method == "POST"

                assert responses.registered()[2].status == 400
                assert responses.registered()[3].status == 500

                assert responses.registered()[3].body == "500 Internal Server Error"

                assert responses.registered()[3].content_type == "text/plain"
            finally:
                responses.mock._parse_response_file = original_parser  # type: ignore[method-assign]

        run()

    def test_add_from_file_content_type_in_headers(self):
        """Fixture files may contain Content-Type in both headers and content_type.

        The recorder captures ``Content-Type`` inside the ``headers`` dict *and*
        as the dedicated ``content_type`` field.  Passing both to ``add()``
        raises a ``RuntimeError`` because ``content_type`` and a ``Content-Type``
        header conflict.  ``_add_from_file`` should strip the duplicate header
        entry so that the dedicated ``content_type`` kwarg wins.

        Using mismatched values (``text/html`` in headers vs ``application/json``
        in ``content_type``) ensures the assertion is non-trivial and confirms
        that ``content_type`` takes precedence over the header value.

        The fixture is saved as a ``.yaml`` file so that ``_add_from_file``
        selects the YAML loader by extension.
        """
        data = {
            "responses": [
                {
                    "response": {
                        "method": "GET",
                        "url": "http://example.com/api",
                        "body": '{"status": "ok"}',
                        "status": 200,
                        # headers has a *different* Content-Type than content_type
                        # to verify that content_type wins (not just that both happen
                        # to be the same value).
                        "headers": {"Content-Type": "text/html"},
                        "content_type": "application/json",
                        "auto_calculate_content_length": False,
                    }
                },
                {
                    "response": {
                        "method": "POST",
                        "url": "http://example.com/submit",
                        "body": "created",
                        "status": 201,
                        "headers": {
                            "Content-Type": "text/html",
                            "X-Request-Id": "abc123",
                        },
                        "content_type": "text/plain",
                        "auto_calculate_content_length": False,
                    }
                },
            ]
        }

        yaml_file = Path(str(self.out_file) + ".yaml")
        with open(yaml_file, "w") as f:
            yaml.dump(data, f)

        @responses.activate
        def run():
            responses._add_from_file(file_path=yaml_file)

            # Verify responses were registered without RuntimeError
            assert len(responses.registered()) == 2

            # content_type must win over the conflicting Content-Type header
            assert responses.registered()[0].url == "http://example.com/api"
            assert responses.registered()[0].content_type == "application/json"

            assert responses.registered()[1].url == "http://example.com/submit"
            assert responses.registered()[1].content_type == "text/plain"
            # Non-content-type headers should be preserved
            resp = requests.post("http://example.com/submit")
            assert resp.headers["X-Request-Id"] == "abc123"

        run()
