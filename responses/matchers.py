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


def _create_key_val_str(input_dict):
    """
    Returns string of format {'key': val, 'key2': val2}
    Function is called recursively for nested dictionaries

    :param input_dict: dictionary to transform
    :return: (str) reformatted string
    """

    def list_to_str(input_list):
        """
        Convert all list items to string.
        Function is called recursively for nested lists
        """
        converted_list = []
        for item in sorted(input_list, key=lambda x: str(x)):
            if isinstance(item, dict):
                item = _create_key_val_str(item)
            elif isinstance(item, list):
                item = list_to_str(item)

            converted_list.append(str(item))
        list_str = ", ".join(converted_list)
        return "[" + list_str + "]"

    items_list = []
    for key in sorted(input_dict.keys(), key=lambda x: str(x)):
        val = input_dict[key]
        if isinstance(val, dict):
            val = _create_key_val_str(val)
        elif isinstance(val, list):
            val = list_to_str(input_list=val)

        items_list.append("{}: {}".format(key, val))

    key_val_str = "{{{}}}".format(", ".join(items_list))
    return key_val_str


def urlencoded_params_matcher(params):
    """
    Matches URL encoded data

    :param params: (dict) data provided to 'data' arg of request
    :return: (func) matcher
    """

    def match(request):
        reason = ""
        request_body = request.body
        qsl_body = dict(parse_qsl(request_body)) if request_body else {}
        params_dict = params or {}
        valid = params is None if request_body is None else params_dict == qsl_body
        if not valid:
            reason = "request.body doesn't match: {} doesn't match {}".format(
                _create_key_val_str(qsl_body), _create_key_val_str(params_dict)
            )

        return valid, reason

    return match


def json_params_matcher(params):
    """
    Matches JSON encoded data

    :param params: (dict) JSON data provided to 'json' arg of request
    :return: (func) matcher
    """

    def match(request):
        reason = ""
        request_body = request.body
        params_dict = params or {}
        try:
            if isinstance(request_body, bytes):
                request_body = request_body.decode("utf-8")
            json_body = json_module.loads(request_body) if request_body else {}

            valid = params is None if request_body is None else params_dict == json_body

            if not valid:
                reason = "request.body doesn't match: {} doesn't match {}".format(
                    _create_key_val_str(json_body), _create_key_val_str(params_dict)
                )

        except JSONDecodeError:
            valid = False
            reason = (
                "request.body doesn't match: JSONDecodeError: Cannot parse request.body"
            )

        return valid, reason

    return match


def query_param_matcher(params):
    """
    Matcher to match 'params' argument in request

    :param params: (dict), same as provided to request
    :return: (func) matcher
    """

    def match(request):
        reason = ""
        request_params = request.params
        request_params_dict = request_params or {}
        params_dict = params or {}
        valid = (
            params is None
            if request_params is None
            else params_dict == request_params_dict
        )

        if not valid:
            reason = "Parameters do not match. {} doesn't match {}".format(
                _create_key_val_str(request_params_dict),
                _create_key_val_str(params_dict),
            )

        return valid, reason

    return match


def request_kwargs_matcher(kwargs):
    """
    Matcher to match keyword arguments provided to request

    :param kwargs: (dict), keyword arguments, same as provided to request
    :return: (func) matcher
    """

    def match(request):
        reason = ""
        kwargs_dict = kwargs or {}
        # validate only kwargs that were requested for comparison, skip defaults
        request_kwargs = {
            k: v for k, v in request.req_kwargs.items() if k in kwargs_dict
        }

        valid = (
            not kwargs_dict
            if not request_kwargs
            else sorted(kwargs.items()) == sorted(request_kwargs.items())
        )

        if not valid:
            reason = "Arguments don't match: {} doesn't match {}".format(
                _create_key_val_str(request_kwargs), _create_key_val_str(kwargs_dict)
            )

        return valid, reason

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
