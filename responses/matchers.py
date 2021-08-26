import json as json_module
from urllib.parse import parse_qsl

from responses import JSONDecodeError


def urlencoded_params_matcher(params):
    def match(request):
        request_body = request.body
        valid = (
            params is None
            if request_body is None
            else sorted(params.items()) == sorted(parse_qsl(request_body))
        )
        if not valid:
            return False, "%s doesn't match %s" % (request_body, params)

        return valid, ""

    return match


def json_params_matcher(params):
    def match(request):
        request_body = request.body
        try:
            if isinstance(request_body, bytes):
                request_body = request_body.decode("utf-8")
            valid = (
                params is None
                if request_body is None
                else params == json_module.loads(request_body)
            )
            if not valid:
                return False, "%s doesn't match %s" % (request_body, params)

            return valid, ""
        except JSONDecodeError:
            return False, ""

    return match


def query_param_matcher(params):
    def match(request):
        request_params = request.params
        valid = (
            params is None
            if request_params is None
            else sorted(params.items()) == sorted(request_params.items())
        )

        if not valid:
            return False, "%s doesn't match %s" % (
                sorted(request_params.items()),
                sorted(params.items()),
            )

        return valid, ""

    return match
