"""Exercise the shared-context recipe used to compose pytest API fixtures."""

from typing import Generator

import pytest
import requests

import responses


@pytest.fixture
def mocked_http() -> Generator[responses.RequestsMock, None, None]:
    with responses.RequestsMock() as rsps:
        assert not rsps.registered()
        assert len(rsps.calls) == 0
        yield rsps


@pytest.fixture
def foo_api(mocked_http: responses.RequestsMock) -> responses.RequestsMock:
    mocked_http.get("https://example.foo/", json={"msg": "foo"})
    return mocked_http


@pytest.fixture
def bar_api(mocked_http: responses.RequestsMock) -> responses.RequestsMock:
    mocked_http.get("https://example.bar/", json={"msg": "bar"})
    return mocked_http


@pytest.mark.parametrize("fixture_name", ["foo_api", "bar_api"])
def test_single_api_fixture(request: pytest.FixtureRequest, fixture_name: str) -> None:
    mock = request.getfixturevalue(fixture_name)
    name = fixture_name[:-4]
    assert requests.get(f"https://example.{name}/").json() == {"msg": name}
    assert len(mock.calls) == 1


def test_composed_api_fixtures(
    foo_api: responses.RequestsMock, bar_api: responses.RequestsMock
) -> None:
    """https://github.com/getsentry/responses/issues/779"""
    assert foo_api is bar_api
    assert requests.get("https://example.foo/").json() == {"msg": "foo"}
    assert requests.get("https://example.bar/").json() == {"msg": "bar"}
    assert len(foo_api.calls) == 2


def test_composed_api_fixtures_in_reverse_order(
    bar_api: responses.RequestsMock, foo_api: responses.RequestsMock
) -> None:
    assert foo_api is bar_api
    assert requests.get("https://example.bar/").json() == {"msg": "bar"}
    assert requests.get("https://example.foo/").json() == {"msg": "foo"}
    assert len(bar_api.calls) == 2
