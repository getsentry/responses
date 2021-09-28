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


def _create_key_val_str(input_dict):
    """
    Returns string of format {'key': val, 'key2': val2}
    Function is called recursively for nested dictionaries
    :param input_dict: dictionary to transform
    :return: (str) reformatted string
    """

    def list_to_str(input_list):
        """
        Covert all list items to string.
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
