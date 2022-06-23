from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Type
    from typing import Union
    import os
    from responses import FirstMatchRegistry
    from responses import HTTPAdapter
    from responses import PreparedRequest
    from responses import models

from responses import RequestsMock
from responses import Response
from responses import _real_send
from responses.registries import OrderedRegistry


class Recorder(RequestsMock):
    def __init__(
        self,
        target: str = "requests.adapters.HTTPAdapter.send",
        registry: "Type[FirstMatchRegistry]" = OrderedRegistry,
    ) -> None:
        super().__init__(target=target, registry=registry)

    def reset(self) -> None:
        self._registry = OrderedRegistry()

    def record(self, *, file_path: "Union[str, bytes, os.PathLike]" = None):
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

    def _on_request(
        self,
        adapter: "HTTPAdapter",
        request: "PreparedRequest",
        **kwargs: "Any",
    ) -> "models.Response":
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

    def stop(self, **kwargs: "Any") -> None:
        super().stop(allow_assert=False)


recorder = Recorder()
record = recorder.record
