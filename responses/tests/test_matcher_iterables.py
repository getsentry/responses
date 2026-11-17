from typing import Any
from typing import Callable
from typing import Iterable

import pytest
import requests

import responses
from responses import matchers


@pytest.mark.parametrize("container", ["tuple", "list", "iterator"])
@pytest.mark.parametrize("response_kind", ["static", "callback"])
def test_matcher_iterable_is_reusable(container: str, response_kind: str) -> None:
    url = "https://example.test/items"
    callbacks: Iterable[Callable[..., Any]] = [
        matchers.header_matcher({"X-Mode": "allowed"})
    ]
    if container == "tuple":
        callbacks = tuple(callbacks)
    elif container == "iterator":
        callbacks = iter(callbacks)
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        if response_kind == "static":
            route = mock.get(url, body="accepted", match=callbacks)
        else:
            route = mock.add_callback(
                responses.GET,
                url,
                callback=lambda request: (200, {}, "accepted"),
                match=callbacks,
            )
        assert requests.get(url, headers={"X-Mode": "allowed"}).text == "accepted"
        for _ in range(2):
            with pytest.raises(requests.ConnectionError, match="Headers do not match"):
                requests.get(url, headers={"X-Mode": "denied"})
        assert requests.get(url, headers={"X-Mode": "allowed"}).text == "accepted"
        assert route.call_count == 2


def test_generator_matchers_restart_after_failed_request():
    url = "https://example.test/items"
    callbacks = (
        matcher
        for matcher in (
            matchers.header_matcher({"X-Mode": "allowed"}),
            matchers.query_param_matcher({"page": "1"}),
        )
    )
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        route = mock.get(url, body="accepted", match=callbacks)
        for _ in range(2):
            with pytest.raises(requests.ConnectionError, match="Headers do not match"):
                requests.get(url, params={"page": "1"}, headers={"X-Mode": "denied"})
        with pytest.raises(requests.ConnectionError, match="Parameters do not match"):
            requests.get(url, params={"page": "2"}, headers={"X-Mode": "allowed"})
        assert (
            requests.get(url, params={"page": "1"}, headers={"X-Mode": "allowed"}).text
            == "accepted"
        )
        assert route.call_count == 1


def test_generator_matchers_allow_repeated_response_registration():
    url = "https://example.test/items"
    route = responses.Response(
        responses.GET,
        url,
        body="accepted",
        match=(matcher for matcher in [matchers.header_matcher({"X-Mode": "allowed"})]),
    )
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        first = mock.add(route)
        second = mock.add(route)
        assert first is not second
        assert requests.get(url, headers={"X-Mode": "allowed"}).text == "accepted"
        with pytest.raises(requests.ConnectionError, match="Headers do not match"):
            requests.get(url, headers={"X-Mode": "denied"})
        assert requests.get(url, headers={"X-Mode": "allowed"}).text == "accepted"
        assert first.call_count == second.call_count == 1
