from pathlib import Path

import pytest
import requests
import tomli_w
import yaml

import responses
from responses import _recorder
from responses._recorder import _dump

try:
    import tomli as _toml
except ImportError:
    # python 3.11
    import tomllib as _toml  # type: ignore[no-redef]


def get_data(host, port):
    data = {
        "responses": [
            {
                "response": {
                    "auto_calculate_content_length": False,
                    "body": "404 Not Found",
                    "content_type": "text/plain",
                    "matchers": [
                        {
                            "query_param_matcher": {
                                "args": {"params": {}, "strict_match": True},
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                        {
                            "header_matcher": {
                                "args": {
                                    "headers": {
                                        "Accept": "*/*",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Connection": "keep-alive",
                                        "User-Agent": "python-requests/2.30.0",
                                    },
                                    "strict_match": False,
                                },
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                    ],
                    "method": "GET",
                    "status": 404,
                    "url": f"http://{host}:{port}/404",
                }
            },
            {
                "response": {
                    "auto_calculate_content_length": False,
                    "body": "Invalid status code",
                    "content_type": "text/plain",
                    "matchers": [
                        {
                            "query_param_matcher": {
                                "args": {"params": {}, "strict_match": True},
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                        {
                            "header_matcher": {
                                "args": {
                                    "headers": {
                                        "Accept": "*/*",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Connection": "keep-alive",
                                        "User-Agent": "python-requests/2.30.0",
                                    },
                                    "strict_match": False,
                                },
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                    ],
                    "method": "GET",
                    "status": 400,
                    "url": f"http://{host}:{port}/status/wrong",
                }
            },
            {
                "response": {
                    "auto_calculate_content_length": False,
                    "body": "500 Internal Server Error",
                    "content_type": "text/plain",
                    "matchers": [
                        {
                            "query_param_matcher": {
                                "args": {
                                    "params": {"query": "smth"},
                                    "strict_match": True,
                                },
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                        {
                            "header_matcher": {
                                "args": {
                                    "headers": {
                                        "Accept": "*/*",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Connection": "keep-alive",
                                        "User-Agent": "python-requests/2.30.0",
                                    },
                                    "strict_match": False,
                                },
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                        {
                            "query_string_matcher": {
                                "args": {"query": "query=smth"},
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                    ],
                    "method": "GET",
                    "status": 500,
                    "url": f"http://{host}:{port}/500?query=smth",
                }
            },
            {
                "response": {
                    "auto_calculate_content_length": False,
                    "body": "OK",
                    "content_type": "text/plain",
                    "matchers": [
                        {
                            "query_param_matcher": {
                                "args": {"params": {}, "strict_match": True},
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                        {
                            "header_matcher": {
                                "args": {
                                    "headers": {
                                        "Accept": "*/*",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Connection": "keep-alive",
                                        "Content-Length": "0",
                                        "User-Agent": "python-requests/2.30.0",
                                        "XAuth": "54579",
                                    },
                                    "strict_match": False,
                                },
                                "matcher_import_path": "responses.matchers",
                            }
                        },
                    ],
                    "method": "PUT",
                    "status": 202,
                    "url": f"http://{host}:{port}/202",
                }
            },
        ]
    }
    return data


class TestRecord:
    def setup(self):
        self.out_file = Path("response_record")
        if self.out_file.exists():
            self.out_file.unlink()  # pragma: no cover

        assert not self.out_file.exists()

    def test_recorder(self, httpserver):

        url202, url400, url404, url500 = self.prepare_server(httpserver)

        def another():
            requests.get(url500, params={"query": "smth"})
            requests.put(url202, headers={"XAuth": "54579"})

        @_recorder.record(file_path=self.out_file)
        def run():
            requests.get(url404)
            requests.get(url400)
            another()

        run()

        with open(self.out_file, "r") as file:
            data = yaml.safe_load(file)

        assert data == get_data(httpserver.host, httpserver.port)

    def test_recorder_toml(self, httpserver):
        custom_recorder = _recorder.Recorder()

        def dump_to_file(file_path, registered):
            with open(file_path, "wb") as file:
                _dump(registered, file, tomli_w.dump)

        custom_recorder.dump_to_file = dump_to_file

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
            "500 Internal Server Error", status=500, content_type="text/plain"
        )
        httpserver.expect_request("/202").respond_with_data(
            "OK", status=202, content_type="text/plain"
        )
        httpserver.expect_request("/404").respond_with_data(
            "404 Not Found", status=404, content_type="text/plain"
        )
        httpserver.expect_request("/status/wrong").respond_with_data(
            "Invalid status code", status=400, content_type="text/plain"
        )
        url500 = httpserver.url_for("/500")
        url202 = httpserver.url_for("/202")
        url404 = httpserver.url_for("/404")
        url400 = httpserver.url_for("/status/wrong")
        return url202, url400, url404, url500


class TestReplay:
    def setup(self):
        self.out_file = Path("response_record.yaml")

    def teardown(self):
        if self.out_file.exists():
            self.out_file.unlink()

        assert not self.out_file.exists()

    @pytest.mark.parametrize("parser", (yaml, tomli_w))
    def test_add_from_file(self, parser):
        if parser == yaml:
            with open(self.out_file, "w") as file:
                parser.dump(get_data("example.com", "8080"), file)
        else:
            with open(self.out_file, "wb") as file:
                parser.dump(get_data("example.com", "8080"), file)

        @responses.activate
        def run():
            responses.patch("http://httpbin.org")
            if parser == tomli_w:

                def _parse_response_file(file_path):
                    with open(file_path, "rb") as file:
                        data = _toml.load(file)
                    return data

                responses.mock._parse_response_file = _parse_response_file

            responses._add_from_file(file_path=self.out_file)
            responses.post("http://httpbin.org/form")

            assert responses.registered()[0].url == "http://httpbin.org/"
            assert responses.registered()[1].url == "http://example.com:8080/404"
            assert (
                responses.registered()[2].url == "http://example.com:8080/status/wrong"
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

        run()
