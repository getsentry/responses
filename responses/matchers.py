import json as json_module
from urllib.parse import parse_qsl

from responses import JSONDecodeError


def urlencoded_params_matcher(params):
    def match(request_body):
        return (
            params is None
            if request_body is None
            else sorted(params.items()) == sorted(parse_qsl(request_body))
        )

    return match


def json_params_matcher(params):
    def match(request_body):
        try:
            if isinstance(request_body, bytes):
                request_body = request_body.decode("utf-8")
            return (
                params is None
                if request_body is None
                else params == json_module.loads(request_body)
            )
        except JSONDecodeError:
            return False

    return match
