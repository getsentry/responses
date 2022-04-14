from functools import wraps
from itertools import groupby
from unittest import mock as std_mock
from urllib.parse import parse_qsl
from urllib.parse import urlsplit

from responses import Response
from responses import _real_send
from responses.registries import OrderedRegistry


class Recorder(object):
    def __init__(
        self, target="requests.adapters.HTTPAdapter.send", registry=OrderedRegistry
    ):
        self.target = target
        self._patcher = None
        self._registry = registry()

    def reset(self):
        self.get_registry().reset()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        success = type is None
        self.stop()
        self.reset()
        return success

    def get_registry(self):
        return self._registry

    def record(self, func=None, *, file_path=None):
        def deco_activate(function):
            @wraps(function)
            def wrapper(*args, **kwargs):
                with self:
                    ret = function(*args, **kwargs)
                    with open(file_path, "w") as file:
                        self.get_registry()._dump(file)

                    return ret

            return wrapper

        return deco_activate

    def _parse_request_params(self, url):
        params = {}
        for key, val in groupby(parse_qsl(urlsplit(url).query), lambda kv: kv[0]):
            values = list(map(lambda x: x[1], val))
            if len(values) == 1:
                values = values[0]
            params[key] = values
        return params

    def _on_request(self, adapter, request, **kwargs):
        # add attributes params and req_kwargs to 'request' object for further match comparison
        # original request object does not have these attributes
        request.params = self._parse_request_params(request.path_url)
        request.req_kwargs = kwargs
        requests_response = _real_send(adapter, request, **kwargs)
        responses_response = Response(
            method=request.method,
            url=requests_response.request.url,
            status=requests_response.status_code,
        )
        self._registry.add(responses_response)
        return requests_response

    def start(self):
        if self._patcher:
            # we must not override value of the _patcher if already applied
            # this prevents issues when one decorated function is called from
            # another decorated function
            return

        def unbound_on_send(adapter, request, *a, **kwargs):
            return self._on_request(adapter, request, *a, **kwargs)

        self._patcher = std_mock.patch(target=self.target, new=unbound_on_send)
        self._patcher.start()

    def stop(self):
        if self._patcher:
            # prevent stopping unstarted patchers
            self._patcher.stop()

            # once patcher is stopped, clean it. This is required to create a new
            # fresh patcher on self.start()
            self._patcher = None


recorder = Recorder()
record = recorder.record
