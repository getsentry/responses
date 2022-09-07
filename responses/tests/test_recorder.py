from pathlib import Path

import requests
import toml

import responses
from responses import _recorder


def get_data(host, port):
    data = {
        "responses": [
            {
                "response": {
                    "method": "GET",
                    "url": f"http://{host}:{port}/404",
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
                    "content_type": "text/plain",
                    "auto_calculate_content_length": False,
                }
            },
        ]
    }
    return data


class TestRecord:
    def setup(self):
        self.out_file = Path("out.toml")
        if self.out_file.exists():
            self.out_file.unlink()  # pragma: no cover

        assert not self.out_file.exists()

    def test_recorder(self, httpserver):

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
            data = toml.load(file)

        assert data == get_data(httpserver.host, httpserver.port)


class TestReplay:
    def teardown(self):
        out_file = Path("out.toml")
        if out_file.exists():
            out_file.unlink()

        assert not out_file.exists()

    def test_add_from_file(self):
        with open("out.toml", "w") as file:
            toml.dump(get_data("example.com", "8080"), file)

        @responses.activate
        def run():
            responses.patch("http://httpbin.org")
            responses._add_from_file(file_path="out.toml")
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
