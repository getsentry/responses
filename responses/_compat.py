# "responses" was initially made for Requests
# since the former is in feature freeze, indefinitely
# alternative started to emerge, like Niquests, which is
# meant to be a "drop-in" compatible solution.
# This file is meant to simplify the import logic, whatever the
# alternative project is.

from os import environ

try:
    if environ.get("RESPONSES_USE_REQUESTS") is not None:
        raise ImportError

    import niquests as requests
    from niquests import PreparedRequest
    from niquests import models
    from niquests.adapters import HTTPAdapter
    from niquests.adapters import MaxRetryError
    from niquests.exceptions import ChunkedEncodingError
    from niquests.exceptions import ConnectionError
    from niquests.exceptions import HTTPError
    from niquests.exceptions import RetryError

    MOCKED_LIBRARY = "niquests"
except ImportError:
    import requests  # noqa: F401
    from requests import PreparedRequest  # noqa: F401
    from requests import models  # noqa: F401
    from requests.adapters import HTTPAdapter  # noqa: F401
    from requests.adapters import MaxRetryError  # noqa: F401
    from requests.exceptions import ChunkedEncodingError  # noqa: F401
    from requests.exceptions import ConnectionError  # noqa: F401
    from requests.exceptions import HTTPError  # noqa: F401
    from requests.exceptions import RetryError  # noqa: F401

    MOCKED_LIBRARY = "requests"
