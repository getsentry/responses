"""
Copyright 2013 Dropbox, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import (
    absolute_import, print_function, division, unicode_literals
)

import re
import six

if six.PY2:
    try:
        from six import cStringIO as BufferIO
    except ImportError:
        from six import StringIO as BufferIO
else:
    from io import BytesIO as BufferIO

import inspect
from collections import namedtuple, Sequence, Sized
from functools import update_wrapper
from cookies import Cookies
from requests.utils import cookiejar_from_dict
from requests.exceptions import ConnectionError
try:
    from requests.packages.urllib3.response import HTTPResponse
except ImportError:
    from urllib3.response import HTTPResponse
if six.PY2:
    from urlparse import urlparse, parse_qsl
else:
    from urllib.parse import urlparse, parse_qsl


Call = namedtuple('Call', ['request', 'response'])

_wrapper_template = """\
def wrapper%(signature)s:
    with responses:
        return func%(funcargs)s
"""


def get_wrapped(func, wrapper_template, evaldict):
    # Preserve the argspec for the wrapped function so that testing
    # tools such as pytest can continue to use their fixture injection.
    args, a, kw, defaults = inspect.getargspec(func)
    values = args[-len(defaults):] if defaults else None

    signature = inspect.formatargspec(args, a, kw, defaults)
    is_bound_method = hasattr(func, '__self__')
    if is_bound_method:
        args = args[1:]     # Omit 'self'
    callargs = inspect.formatargspec(args, a, kw, values,
                                     formatvalue=lambda v: '=' + v)

    ctx = {'signature': signature, 'funcargs': callargs}
    six.exec_(wrapper_template % ctx, evaldict)

    wrapper = evaldict['wrapper']

    update_wrapper(wrapper, func)
    if is_bound_method:
        wrapper = wrapper.__get__(func.__self__, type(func.__self__))
    return wrapper


class CallList(Sequence, Sized):
    def __init__(self):
        self._calls = []

    def __iter__(self):
        return iter(self._calls)

    def __len__(self):
        return len(self._calls)

    def __getitem__(self, idx):
        return self._calls[idx]

    def add(self, request, response):
        self._calls.append(Call(request, response))

    def reset(self):
        self._calls = []


class RequestsMock(object):
    DELETE = 'DELETE'
    GET = 'GET'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    POST = 'POST'
    PUT = 'PUT'

    def __init__(self):
        self._calls = CallList()
        self.reset()

    def reset(self):
        self._urls = []
        self._calls.reset()

    def add(self, method, url, body='', match_querystring=False,
            status=200, adding_headers=None, stream=False,
            content_type='text/plain'):

        # ensure the url has a default path set if the url is a string
        if self._is_string(url) and url.count('/') == 2:
            url = url.replace('?', '/?', 1) if match_querystring \
                else url + '/'

        # body must be bytes
        if isinstance(body, six.text_type):
            body = body.encode('utf-8')

        self._urls.append({
            'url': url,
            'method': method,
            'body': body,
            'content_type': content_type,
            'match_querystring': match_querystring,
            'status': status,
            'adding_headers': adding_headers,
            'stream': stream,
        })

    def add_callback(self, method, url, callback, match_querystring=False,
                     content_type='text/plain'):

        self._urls.append({
            'url': url,
            'method': method,
            'callback': callback,
            'content_type': content_type,
            'match_querystring': match_querystring,
        })

    @property
    def calls(self):
        return self._calls

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.stop()
        self.reset()

    def activate(self, func):
        evaldict = {'responses': self, 'func': func}
        return get_wrapped(func, _wrapper_template, evaldict)

    def _find_match(self, request):
        for match in self._urls:
            if request.method != match['method']:
                continue

            if not self._has_url_match(match, request.url):
                continue

            return match

        return None

    def _has_url_match(self, match, request_url):
        url = match['url']

        if self._is_string(url):
            if match['match_querystring']:
                return self._has_strict_url_match(url, request_url)
            else:
                url_without_qs = request_url.split('?', 1)[0]
                return url == url_without_qs
        elif isinstance(url, re._pattern_type) and url.match(request_url):
            return True
        else:
            return False

    def _has_strict_url_match(self, url, other):
        url_parsed = urlparse(url)
        other_parsed = urlparse(other)

        if url_parsed[:3] != other_parsed[:3]:
            return False

        url_qsl = sorted(parse_qsl(url_parsed.query))
        other_qsl = sorted(parse_qsl(other_parsed.query))
        return url_qsl == other_qsl

    def _is_string(self, s):
        return isinstance(s, (six.string_types, six.text_type))

    def _on_request(self, session, request, **kwargs):
        match = self._find_match(request)

        # TODO(dcramer): find the correct class for this
        if match is None:
            error_msg = 'Connection refused: {0}'.format(request.url)
            response = ConnectionError(error_msg)

            self._calls.add(request, response)
            raise response

        if 'body' in match and isinstance(match['body'], Exception):
            self._calls.add(request, match['body'])
            raise match['body']

        headers = {
            'Content-Type': match['content_type'],
        }

        if 'callback' in match:  # use callback
            status, r_headers, body = match['callback'](request)
            if isinstance(body, six.text_type):
                body = body.encode('utf-8')
            body = BufferIO(body)
            headers.update(r_headers)

        elif 'body' in match:
            if match['adding_headers']:
                headers.update(match['adding_headers'])
            status = match['status']
            body = BufferIO(match['body'])

        response = HTTPResponse(
            status=status,
            body=body,
            headers=headers,
            preload_content=False,
        )

        adapter = session.get_adapter(request.url)

        response = adapter.build_response(request, response)
        if not match.get('stream'):
            response.content  # NOQA

        try:
            resp_cookies = Cookies.from_request(response.headers['set-cookie'])
            response.cookies = cookiejar_from_dict(dict(
                (v.name, v.value)
                for _, v
                in resp_cookies.items()
            ))
            session.cookies = response.cookies
        except (KeyError, TypeError):
            pass

        self._calls.add(request, response)

        return response

    def start(self):
        import mock

        def unbound_on_send(session, requests, *a, **kwargs):
            return self._on_request(session, requests, *a, **kwargs)
        self._patcher = mock.patch('requests.Session.send', unbound_on_send)
        self._patcher.start()

    def stop(self):
        self._patcher.stop()


# expose default mock namespace
mock = _default_mock = RequestsMock()
__all__ = []
for __attr in (a for a in dir(_default_mock) if not a.startswith('_')):
    __all__.append(__attr)
    globals()[__attr] = getattr(_default_mock, __attr)
