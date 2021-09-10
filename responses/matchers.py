import six
import json as json_module

if six.PY2:
    from urlparse import parse_qsl
else:
    from urllib.parse import parse_qsl

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


def urlencoded_params_matcher(params):
    """
    Matches URL encoded data
    :param params: (dict) data provided to 'data' arg of request
    :return: (func) matcher
    """

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
    """
    Matches JSON encoded data
    :param params: (dict) JSON data provided to 'json' arg of request
    :return: (func) matcher
    """

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
            return False, "JSONDecodeError: Cannot parse request.body"

    return match


def query_param_matcher(params):
    """
    Matcher to match 'params' argument in request
    :param params: (dict), same as provided to request
    :return: (func) matcher
    """

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
