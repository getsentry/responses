from typing import (
    Any,
    Callable,
    Optional,
    Dict,
)

JSONDecodeError = ValueError


def json_params_matcher(
    params: Optional[Dict[str, Any]]
) -> Callable[..., Any]: ...

def urlencoded_params_matcher(
    params: Optional[Dict[str, str]]
) -> Callable[..., Any]: ...

def query_param_matcher(
    params: Optional[Dict[str, str]]
) -> Callable[..., Any]: ...
