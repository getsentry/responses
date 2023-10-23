import os
import uuid
from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any
    from typing import BinaryIO
    from typing import Callable
    from typing import Dict
    from typing import List
    from typing import Type
    from typing import Union
    from responses import FirstMatchRegistry
    from responses import HTTPAdapter
    from responses import PreparedRequest
    from responses import models
    from responses import _F
    from responses import BaseResponse

    from io import TextIOWrapper

import yaml

from responses import _UNSET
from responses import RequestsMock
from responses import Response
from responses import _real_send
from responses.registries import OrderedRegistry


def _remove_nones(d: "Any") -> "Any":
    if isinstance(d, dict):
        return {k: _remove_nones(v) for k, v in d.items() if v is not None}
    if isinstance(d, list):
        return [_remove_nones(i) for i in d]
    return d


def _dump(
    registered: "List[BaseResponse]",
    config_file: "Union[str, os.PathLike]",
    dumper: "Callable[[Union[Dict[Any, Any], List[Any]], Union[BinaryIO, TextIOWrapper]], Any]",
    dumper_mode: "str" = "w",
):
    data: Dict[str, Any] = {"responses": []}

    # e.g. config_file = 'my/dir/responses.yaml'
    # parent_directory = 'my/dir'
    # binary_directory = 'my/dir/responses'
    fname, fext = os.path.splitext(os.path.basename(config_file))
    parent_directory = os.path.dirname(os.path.abspath(config_file))
    binary_directory = os.path.join(
        parent_directory, fname if fext else f"{fname}_bodies"
    )

    for rsp in registered:
        try:
            content_length = rsp.auto_calculate_content_length  # type: ignore[attr-defined]
            body = rsp.body  # type: ignore[attr-defined]
            if isinstance(body, bytes):
                os.makedirs(binary_directory, exist_ok=True)
                bin_file = os.path.join(binary_directory, f"{uuid.uuid4()}.bin")
                with open(bin_file, "wb") as bf:
                    bf.write(body)

                # make sure the stored binary file path is relative to config file
                # or the config file and binary directory will be hard to move
                body_file = os.path.relpath(bin_file, parent_directory)
                body = None
            else:
                body_file = None
            data["responses"].append(
                {
                    "response": {
                        "method": rsp.method,
                        "url": rsp.url,
                        "body": body,  # type: ignore[attr-defined]
                        "body_file": body_file,
                        "status": rsp.status,  # type: ignore[attr-defined]
                        "headers": rsp.headers,
                        "content_type": rsp.content_type,
                        "auto_calculate_content_length": content_length,
                    }
                }
            )
        except AttributeError as exc:  # pragma: no cover
            raise AttributeError(
                "Cannot dump response object."
                "Probably you use custom Response object that is missing required attributes"
            ) from exc

    with open(config_file, dumper_mode) as cfile:
        dumper(_remove_nones(data), cfile)


class Recorder(RequestsMock):
    def __init__(
        self,
        *,
        target: str = "requests.adapters.HTTPAdapter.send",
        registry: "Type[FirstMatchRegistry]" = OrderedRegistry,
    ) -> None:
        super().__init__(target=target, registry=registry)

    def reset(self) -> None:
        self._registry = OrderedRegistry()

    def record(
        self, *, file_path: "Union[str, bytes, os.PathLike[Any]]" = "response.yaml"
    ) -> "Union[Callable[[_F], _F], _F]":
        def deco_record(function: "_F") -> "Callable[..., Any]":
            @wraps(function)
            def wrapper(*args: "Any", **kwargs: "Any") -> "Any":  # type: ignore[misc]
                with self:
                    ret = function(*args, **kwargs)
                    self.dump_to_file(
                        file_path=file_path, registered=self.get_registry().registered
                    )

                    return ret

            return wrapper

        return deco_record

    def dump_to_file(
        self,
        *,
        file_path: "Union[str, bytes, os.PathLike[Any]]",
        registered: "List[BaseResponse]",
    ) -> None:
        _dump(registered, file_path, yaml.dump)

    def _on_request(
        self,
        adapter: "HTTPAdapter",
        request: "PreparedRequest",
        **kwargs: "Any",
    ) -> "models.Response":
        # add attributes params and req_kwargs to 'request' object for further match comparison
        # original request object does not have these attributes
        request.params = self._parse_request_params(request.path_url)  # type: ignore[attr-defined]
        request.req_kwargs = kwargs  # type: ignore[attr-defined]
        requests_response = _real_send(adapter, request, **kwargs)
        requests_headers = dict(requests_response.headers)
        if "Content-Type" in requests_headers:
            requests_content_type = requests_headers.pop("Content-Type")
        else:
            requests_content_type = _UNSET
        # Content-Encoding should be removed to
        # avoid 'Content-Encoding: gzip' causing the error in requests
        if "Content-Encoding" in requests_headers:
            requests_headers.pop("Content-Encoding")
        responses_response = Response(
            method=str(request.method),
            url=str(requests_response.request.url),
            status=requests_response.status_code,
            headers=requests_headers,
            body=requests_response.content,
            content_type=requests_content_type,
        )
        self._registry.add(responses_response)
        return requests_response

    def stop(self, allow_assert: bool = True) -> None:
        super().stop(allow_assert=False)


recorder = Recorder()
record = recorder.record
