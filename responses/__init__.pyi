from collections import Sequence, Sized
from typing import (
    Any,
    Callable,
    Iterator,
    Mapping,
    Optional,
    Pattern,
    NamedTuple,
    Protocol,
    TypeVar,
)
from io import BufferedReader, BytesIO
from re import Pattern
from requests.adapters import HTTPResponse, PreparedRequest
from requests.cookies import RequestsCookieJar
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from typing_extensions import Literal
from unittest import mock as std_mock
from urllib.parse import quote as quote
from urllib3.response import HTTPHeaderDict

JSONDecodeError = ValueError

def _clean_unicode(url: str) -> str: ...
def _cookies_from_headers(headers: Dict[str, str]) -> RequestsCookieJar: ...
def _ensure_str(s: str) -> str: ...
def _ensure_url_default_path(
    url: Union[Pattern[str], str]
) -> Union[Pattern[str], str]: ...
def _handle_body(
    body: Optional[Union[bytes, BufferedReader, str]]
) -> Union[BufferedReader, BytesIO]: ...
def _has_unicode(s: str) -> bool: ...
def _is_string(s: Union[Pattern[str], str]) -> bool: ...
def get_wrapped(
    func: Callable[..., Any], responses: RequestsMock
) -> Callable[..., Any]: ...
def json_params_matcher(
    params: Optional[Dict[str, Any]]
) -> Callable[..., Any]: ...
def urlencoded_params_matcher(
    params: Optional[Dict[str, str]]
) -> Callable[..., Any]: ...

class Call(NamedTuple):
    request: PreparedRequest
    response: Any

_Body = Union[str, BaseException, "Response", BufferedReader, bytes]

class CallList(Sequence[Call], Sized):
    def __init__(self) -> None: ...
    def __iter__(self) -> Iterator[Call]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, idx: int) -> Call: ...  # type: ignore [override]
    def add(self, request: PreparedRequest, response: _Body) -> None: ...
    def reset(self) -> None: ...

class BaseResponse:
    content_type: Optional[str] = ...
    headers: Optional[Mapping[str, str]] = ...
    stream: bool = ...
    method: Any = ...
    url: Any = ...
    match_querystring: Any = ...
    match: List[Any] = ...
    call_count: int = ...
    def __init__(
        self,
        method: str,
        url: Union[Pattern[str], str],
        match_querystring: Union[bool, object] = ...,
        match: List[Callable[..., Any]] = ...,
    ) -> None: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...
    def _body_matches(
        self, match: List[Callable[..., Any]], request_body: Optional[Union[bytes, str]]
    ) -> bool: ...
    def _should_match_querystring(
        self, match_querystring_argument: Union[bool, object]
    ) -> bool: ...
    def _url_matches(
        self, url: Union[Pattern[str], str], other: str, match_querystring: bool = ...
    ) -> bool: ...
    def _url_matches_strict(self, url: str, other: str) -> bool: ...
    def get_headers(self) -> HTTPHeaderDict: ...  # type: ignore [no-any-unimported]
    def get_response(self, request: PreparedRequest) -> None: ...
    def matches(self, request: PreparedRequest) -> Tuple[bool, str]: ...

class Response(BaseResponse):
    body: _Body = ...
    status: int = ...
    headers: Optional[Mapping[str, str]] = ...
    stream: bool = ...
    content_type: Optional[str] = ...
    def __init__(
        self,
        method: str,
        url: Union[Pattern[str], str],
        body: _Body = ...,
        json: Optional[Any] = ...,
        status: int = ...,
        headers: Optional[Mapping[str, str]] = ...,
        stream: bool = ...,
        content_type: Optional[str] = ...,
        match_querystring: bool = ...,
        match: List[Any] = ...,
    ) -> None: ...
    def get_response(  # type: ignore [override]
        self, request: PreparedRequest
    ) -> HTTPResponse: ...

class CallbackResponse(BaseResponse):
    callback: Callable[[Any], Any] = ...
    stream: bool = ...
    content_type: Optional[str] = ...
    def __init__(
        self,
        method: str,
        url: Union[Pattern[str], str],
        callback: Callable[[Any], Any],
        stream: bool = ...,
        content_type: Optional[str] = ...,
        match_querystring: bool = ...,
        match: List[Any] = ...,
    ) -> None: ...
    def get_response(  # type: ignore [override]
        self, request: PreparedRequest
    ) -> HTTPResponse: ...

class OriginalResponseShim:
    msg: Any = ...
    def __init__(  # type: ignore [no-any-unimported]
        self, headers: HTTPHeaderDict
    ) -> None: ...
    def isclosed(self) -> bool: ...

class RequestsMock:
    DELETE: Literal["DELETE"]
    GET: Literal["GET"]
    HEAD: Literal["HEAD"]
    OPTIONS: Literal["OPTIONS"]
    PATCH: Literal["PATCH"]
    POST: Literal["POST"]
    PUT: Literal["PUT"]
    response_callback: Optional[Callable[[Any], Any]] = ...
    assert_all_requests_are_fired: Any = ...
    passthru_prefixes: Tuple[str, ...] = ...
    target: Any = ...
    _matches: List[Any]
    def __init__(
        self,
        assert_all_requests_are_fired: bool = ...,
        response_callback: Optional[Callable[[Any], Any]] = ...,
        passthru_prefixes: Tuple[str, ...] = ...,
        target: str = ...,
    ) -> None: ...
    def reset(self) -> None: ...
    add: _Add
    add_passthru: _AddPassthru
    def remove(
        self,
        method_or_response: Optional[Union[str, Response]] = ...,
        url: Optional[Union[Pattern[str], str]] = ...,
    ) -> None: ...
    replace: _Replace
    add_callback: _AddCallback
    @property
    def calls(self) -> CallList: ...
    def __enter__(self) -> RequestsMock: ...
    def __exit__(self, type: Any, value: Any, traceback: Any) -> bool: ...
    activate: _Activate
    def start(self) -> None: ...
    def stop(self, allow_assert: bool = ...) -> None: ...
    def assert_call_count(self, url: str, count: int) -> bool: ...
    def registered(self) -> List[Any]: ...

_F = TypeVar("_F", bound=Callable[..., Any])

class _Activate(Protocol):
    def __call__(self, func: _F) -> _F: ...

class _Add(Protocol):
    def __call__(
        self,
        method: Optional[Union[str, BaseResponse]] = ...,
        url: Optional[Union[Pattern[str], str]] = ...,
        body: _Body = ...,
        json: Optional[Any] = ...,
        status: int = ...,
        headers: Optional[Mapping[str, str]] = ...,
        stream: bool = ...,
        content_type: Optional[str] = ...,
        adding_headers: Optional[Mapping[str, str]] = ...,
        match_querystring: bool = ...,
        match: List[Any] = ...,
    ) -> None: ...

class _AddCallback(Protocol):
    def __call__(
        self,
        method: str,
        url: Union[Pattern[str], str],
        callback: Callable[[PreparedRequest], Union[Exception, Tuple[int, Mapping[str, str], _Body]]],
        match_querystring: bool = ...,
        content_type: Optional[str] = ...,
    ) -> None: ...

class _AddPassthru(Protocol):
    def __call__(
        self, prefix: Union[Pattern[str], str]
    ) -> None: ...

class _Remove(Protocol):
    def __call__(
        self,
        method_or_response: Optional[Union[str, BaseResponse]] = ...,
        url: Optional[Union[Pattern[str], str]] = ...,
    ) -> None: ...

class _Replace(Protocol):
    def __call__(
        self,
        method_or_response: Optional[Union[str, BaseResponse]] = ...,
        url: Optional[Union[Pattern[str], str]] = ...,
        body: _Body = ...,
        json: Optional[Any] = ...,
        status: int = ...,
        headers: Optional[Mapping[str, str]] = ...,
        stream: bool = ...,
        content_type: Optional[str] = ...,
        adding_headers: Optional[Mapping[str, str]] = ...,
        match_querystring: bool = ...,
        match: List[Any] = ...,
    ) -> None: ...

class _Upsert(Protocol):
    def __call__(
        self,
        method: Optional[Union[str, BaseResponse]] = ...,
        url: Optional[Union[Pattern[str], str]] = ...,
        body: _Body = ...,
        json: Optional[Any] = ...,
        status: int = ...,
        headers: Optional[Mapping[str, str]] = ...,
        stream: bool = ...,
        content_type: Optional[str] = ...,
        adding_headers: Optional[Mapping[str, str]] = ...,
        match_querystring: bool = ...,
        match: List[Any] = ...,
    ) -> None: ...

class _Registered(Protocol):
    def __call__(self) -> List[Response]: ...


activate: _Activate
add: _Add
add_callback: _AddCallback
add_passthru: _AddPassthru
assert_all_requests_are_fired: bool
assert_call_count: Callable[[str, int], bool]
calls: CallList
DELETE: Literal["DELETE"]
GET: Literal["GET"]
HEAD: Literal["HEAD"]
mock: RequestsMock
_default_mock: RequestsMock
OPTIONS: Literal["OPTIONS"]
passthru_prefixes: Tuple[str, ...]
PATCH: Literal["PATCH"]
POST: Literal["POST"]
PUT: Literal["PUT"]
registered: _Registered
remove: _Remove
replace: _Replace
reset: Callable[[], None]
response_callback: Callable[[Any], Any]
start: Callable[[], None]
stop: Callable[..., None]
target: Any
upsert: _Upsert

__all__ = [
    "CallbackResponse",
    "Response",
    "RequestsMock",
    # Exposed by the RequestsMock class:
    "activate",
    "add",
    "add_callback",
    "add_passthru",
    "assert_all_requests_are_fired",
    "assert_call_count",
    "calls",
    "DELETE",
    "GET",
    "HEAD",
    "OPTIONS",
    "passthru_prefixes",
    "PATCH",
    "POST",
    "PUT",
    "registered",
    "remove",
    "replace",
    "reset",
    "response_callback",
    "start",
    "stop",
    "target",
    "upsert"
]
