import requests
import responses
import pytest

from requests.exceptions import ConnectionError


def assert_response(resp, body=None):
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/plain'
    assert resp.text == body


def test_response():
    @responses.activate
    def run():
        responses.add(responses.GET, 'http://example.com', body='test')
        resp = requests.get('http://example.com')
        assert_response(resp, 'test')

    run()


def test_connection_error():
    @responses.activate
    def run():
        responses.add(responses.GET, 'http://example.com')

        with pytest.raises(ConnectionError):
            requests.get('http://example.com/foo')
    run()


def test_reset():
    @responses.activate
    def run():
        responses.add(responses.GET, 'http://example.com')

    run()
    assert len(responses._default_mock._urls) == 0


def test_match_querystring():
    @responses.activate
    def run():
        url = 'http://example.com?test=1'
        responses.add(
            responses.GET, url,
            match_querystring=True, body='test')
        resp = requests.get(url)
        assert_response(resp, 'test')

    run()


def test_match_querystring_error():
    @responses.activate
    def run():
        responses.add(
            responses.GET, 'http://example.com/?test=1',
            match_querystring=True)

        with pytest.raises(ConnectionError):
            requests.get('http://example.com/foo/?test=2')

    run()
