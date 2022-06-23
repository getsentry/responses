from functools import wraps
from itertools import groupby
from urllib.parse import parse_qsl
from urllib.parse import urlsplit

from responses import RequestsMock
from responses import Response
from responses import _real_send
from responses.registries import OrderedRegistry


class Recorder(RequestsMock):
    def __init__(
        self, target="requests.adapters.HTTPAdapter.send", registry=OrderedRegistry
    ):
        super().__init__(target=target, registry=registry)

    def reset(self):
        self._registry = OrderedRegistry()

    def record(self, *, file_path=None):
        def deco_record(function):
            @wraps(function)
            def wrapper(*args, **kwargs):
                with self:
                    ret = function(*args, **kwargs)
                    with open(file_path, "w") as file:
                        self.get_registry()._dump(file)

                    return ret

            return wrapper

        return deco_record

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

    def stop(self, **kwargs):
        super().stop(allow_assert=False)


recorder = Recorder()
record = recorder.record
