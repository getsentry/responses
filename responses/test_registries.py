import pytest

import responses
from responses import registries
from responses.test_responses import assert_reset


def test_set_registry_not_empty():
    class CustomRegistry(registries.FirstMatchRegistry):
        pass

    @responses.activate
    def run():
        url = "http://fizzbuzz/foo"
        responses.add(method=responses.GET, url=url)
        with pytest.raises(AttributeError) as excinfo:
            responses.mock._set_registry(CustomRegistry)
        msg = str(excinfo.value)
        assert "Cannot replace Registry, current registry has responses" in msg

    run()
    assert_reset()


def test_set_registry():
    class CustomRegistry(registries.FirstMatchRegistry):
        pass

    @responses.activate(registry=CustomRegistry)
    def run_with_registry():
        assert type(responses.mock._get_registry()) == CustomRegistry

    @responses.activate
    def run():
        # test that registry does not leak to another test
        assert type(responses.mock._get_registry()) == registries.FirstMatchRegistry

    run_with_registry()
    run()
    assert_reset()


def test_set_registry_context_manager():
    def run():
        class CustomRegistry(registries.FirstMatchRegistry):
            pass

        with responses.RequestsMock(
            assert_all_requests_are_fired=False, registry=CustomRegistry
        ) as rsps:
            assert type(rsps._get_registry()) == CustomRegistry
            assert type(responses.mock._get_registry()) == registries.FirstMatchRegistry

    run()
    assert_reset()


def test_registry_reset():
    def run():
        class CustomRegistry(registries.FirstMatchRegistry):
            pass

        with responses.RequestsMock(
            assert_all_requests_are_fired=False, registry=CustomRegistry
        ) as rsps:
            rsps._get_registry().reset()
            assert not rsps.registered()

    run()
    assert_reset()
