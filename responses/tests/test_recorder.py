import collections.abc
import shutil
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

_NOT_CARE = object()


class _CompareDict:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        if self.obj is _NOT_CARE:
            return True
        elif isinstance(self.obj, collections.abc.Mapping):
            if not isinstance(other, collections.abc.Mapping):
                return False
            if sorted(self.obj.keys()) != sorted(other.keys()):
                return False
            for key in self.obj.keys():
                if _CompareDict(self.obj[key]) != other[key]:
                    return False
            return True
        elif isinstance(self.obj, list):
            if not isinstance(other, list):
                return False
            if len(self.obj) != len(other):
                return False
            for i, (obj_item, other_item) in enumerate(zip(self.obj, other)):
                if _CompareDict(obj_item) != other_item:
                    return False
            return True
        else:
            return self.obj == other


def get_data_for_cmp(host, port):
    data = {
        "responses": [
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/404",
                    "body_file": _NOT_CARE,
                    "headers": {
                        "Connection": "keep-alive",
                        "Content-Length": "13",
                        "Date": _NOT_CARE,
                        "Keep-Alive": _NOT_CARE,
                        "Proxy-Connection": "keep-alive",
                        "Server": _NOT_CARE,
                    },
                    "status": 404,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/status/wrong",
                    "body_file": _NOT_CARE,
                    "headers": {
                        "Connection": "keep-alive",
                        "Content-Length": "19",
                        "Date": _NOT_CARE,
                        "Keep-Alive": _NOT_CARE,
                        "Proxy-Connection": "keep-alive",
                        "Server": _NOT_CARE,
                    },
                    "status": 400,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/500",
                    "body_file": _NOT_CARE,
                    "headers": {
                        "Connection": "keep-alive",
                        "Content-Length": "25",
                        "Date": _NOT_CARE,
                        "Keep-Alive": _NOT_CARE,
                        "Proxy-Connection": "keep-alive",
                        "Server": _NOT_CARE,
                    },
                    "status": 500,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "PUT",
                    "url": f"http://{host}:{port}/202",
                    "body_file": _NOT_CARE,
                    "headers": {
                        "Connection": "keep-alive",
                        "Content-Length": "2",
                        "Date": _NOT_CARE,
                        "Keep-Alive": _NOT_CARE,
                        "Proxy-Connection": "keep-alive",
                        "Server": _NOT_CARE,
                    },
                    "status": 202,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
        ]
    }
    return _CompareDict(data)


def get_data_for_dump(host, port):
    data = {
        "responses": [
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/404",
                    "body": "404 Not Found",  # test the backward support for 0.23.3
                    "status": 404,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/status/wrong",
                    "body_file": "example_bins/400.bin",
                    "headers": {
                        "Connection": "keep-alive",
                        "Content-Length": "19",
                        "Date": "Fri, 20 Oct 2023 10:12:13 " "GMT",
                        "Keep-Alive": "timeout=4",
                        "Proxy-Connection": "keep-alive",
                        "Server": "Werkzeug/3.0.0 " "Python/3.8.10",
                    },
                    "status": 400,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/500",
                    "body_file": "example_bins/500.bin",
                    "headers": {
                        "Connection": "keep-alive",
                        "Content-Length": "25",
                        "Date": "Fri, 20 Oct 2023 10:12:13 " "GMT",
                        "Keep-Alive": "timeout=4",
                        "Proxy-Connection": "keep-alive",
                        "Server": "Werkzeug/3.0.0 " "Python/3.8.10",
                    },
                    "status": 500,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
            {
                "response": {
                    "method": "PUT",
                    "url": f"http://{host}:{port}/202",
                    "body_file": "example_bins/202.bin",
                    "headers": {
                        "Connection": "keep-alive",
                        "Content-Length": "2",
                        "Date": "Fri, 20 Oct 2023 10:12:13 " "GMT",
                        "Keep-Alive": "timeout=4",
                        "Proxy-Connection": "keep-alive",
                        "Server": "Werkzeug/3.0.0 " "Python/3.8.10",
                    },
                    "status": 202,
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
        ]
    }
    return data


class TestRecord:
    def setup_method(self):
        self.out_file = Path("response_record")
        if self.out_file.exists():
            self.out_file.unlink()  # pragma: no cover

        self.out_bins_dir = Path("response_record_bins")
        if self.out_bins_dir.exists():
            shutil.rmtree(self.out_bins_dir)  # pragma: no cover

        assert not self.out_file.exists()

    def teardown_method(self):
        if self.out_file.exists():
            self.out_file.unlink()
        if self.out_bins_dir.exists():
            shutil.rmtree(self.out_bins_dir)

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

        import pprint

        pprint.pprint(data)
        assert data == get_data_for_cmp(httpserver.host, httpserver.port)

    def test_recorder_toml(self, httpserver):
        custom_recorder = _recorder.Recorder()

        def dump_to_file(file_path, registered):
            _dump(registered, file_path, tomli_w.dump, "wb")

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

        assert data == get_data_for_cmp(httpserver.host, httpserver.port)

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
    def setup_method(self):
        self.out_file = Path("response_record")
        self.out_bins_dir = Path("response_record_bins")

    def teardown_method(self):
        if self.out_file.exists():
            self.out_file.unlink()
        if self.out_bins_dir.exists():
            shutil.rmtree(self.out_bins_dir)

        assert not self.out_file.exists()

    @pytest.mark.parametrize("parser", (yaml, tomli_w))
    def test_add_from_file(self, parser):
        if parser == yaml:
            with open(self.out_file, "w") as file:
                parser.dump(get_data_for_dump("example.com", "8080"), file)
        else:
            with open(self.out_file, "wb") as file:
                parser.dump(get_data_for_dump("example.com", "8080"), file)

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

            assert responses.registered()[1].status == 404
            assert responses.registered()[2].status == 400
            assert responses.registered()[3].status == 500

            assert (
                responses.registered()[1].body == "404 Not Found"
            )  # test the backward support for 0.23.3
            assert responses.registered()[2].body == b"Invalid status code"
            assert responses.registered()[3].body == b"500 Internal Server Error"

            assert responses.registered()[3].content_type == "text/plain"

        run()
