from pathlib import Path

import requests
import toml

from responses import _recorder


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
            requests.get(url202)

        @_recorder.record(file_path=self.out_file)
        def run():
            requests.get(url404)
            requests.get(url400)
            another()

        run()

        with open(self.out_file) as file:
            data = toml.load(file)

        assert data == {
            "responses": [
                {
                    "response": {
                        "method": "GET",
                        "url": f"http://{httpserver.host}:{httpserver.port}/404",
                        "body": "404 Not Found",
                        "status": 404,
                        "content_type": "text/plain",
                        "auto_calculate_content_length": False,
                    }
                },
                {
                    "response": {
                        "method": "GET",
                        "url": f"http://{httpserver.host}:{httpserver.port}/status/wrong",
                        "body": "Invalid status code",
                        "status": 400,
                        "content_type": "text/plain",
                        "auto_calculate_content_length": False,
                    }
                },
                {
                    "response": {
                        "method": "GET",
                        "url": f"http://{httpserver.host}:{httpserver.port}/500",
                        "body": "500 Internal Server Error",
                        "status": 500,
                        "content_type": "text/plain",
                        "auto_calculate_content_length": False,
                    }
                },
                {
                    "response": {
                        "method": "GET",
                        "url": f"http://{httpserver.host}:{httpserver.port}/202",
                        "body": "OK",
                        "status": 202,
                        "content_type": "text/plain",
                        "auto_calculate_content_length": False,
                    }
                },
            ]
        }
