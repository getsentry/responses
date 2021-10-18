import six
import json as json_module

from requests import PreparedRequest

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


def multipart_matcher(data, files, encoding="utf-8"):
    """
    Matcher to match 'params' argument in request
    :param params: (dict), same as provided to request
    :return: (func) matcher
    """
    if not files:
        raise TypeError("files argument cannot be empty")

    prepared = PreparedRequest()
    prepared.headers = {"Content-Type": ""}
    prepared.prepare_body(data=data, files=files)

    def get_boundary(content_type):
        if "boundary=" not in content_type:
            return ""

        boundary = content_type.split("boundary=")[1]
        return boundary

    def match(request):
        if "Content-Type" not in request.headers:
            return False, "Request misses 'Content-Type' in headers"

        request_boundary = get_boundary(request.headers["Content-Type"])
        prepared_boundary = get_boundary(prepared.headers["Content-Type"])

        request_content_type = request.headers["Content-Type"]
        prepared_content_type = prepared.headers["Content-Type"].replace(
            prepared_boundary, request_boundary
        )

        request_body = request.body
        prepared_body = prepared.body.replace(
            bytes(prepared_boundary, encoding), bytes(request_boundary, encoding)
        )

        body_valid = prepared_body == request_body

        if not body_valid:
            return False, "Request body is different. {} not equal {}".format(
                request_body, prepared_body
            )
        else:
            headers_valid = prepared_content_type == request_content_type

            if not headers_valid:
                return (
                    False,
                    "Request headers['Content-Type'] is different. {} not equal {}".format(
                        request_content_type, prepared_content_type
                    ),
                )

        valid = body_valid and headers_valid
        return valid, ""

    return match
