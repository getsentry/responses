import requests
import responses
import pytest

from requests.exceptions import ConnectionError


def test_simple():
    @responses.activate
    def run():
        responses.add(responses.GET, 'http://example.com', body='test')

        resp = requests.get('http://example.com')

        assert resp.status_code == 200
        assert resp.headers['Content-Type'] == 'text/plain'
        assert resp.text == 'test'

        with pytest.raises(ConnectionError):
            requests.get('http://example.com/foo')

    run()

    # make sure we actually reset things
    assert responses._default_mock._urls == []
