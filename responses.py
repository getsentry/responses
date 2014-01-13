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

from collections import namedtuple, Sequence, Sized
from functools import wraps
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError
from requests.packages.urllib3.response import HTTPResponse

Call = namedtuple('Call', ['request', 'response'])


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
        # ensure the url has a default path set
        if url.count('/') == 2:
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

    @property
    def calls(self):
        return self._calls

    def activate(self, func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            self._start()
            try:
                return func(*args, **kwargs)
            finally:
                self._stop()
                self.reset()
        return wrapped

    def _find_match(self, request):
        url = request.url
        url_without_qs = url.split('?', 1)[0]

        for match in self._urls:
            if request.method != match['method']:
                continue

            # TODO(dcramer): we could simplify this by compiling a single
            # regexp on register
            if match['match_querystring']:
                if not re.match(re.escape(match['url']), url):
                    continue
            else:
                if match['url'] != url_without_qs:
                    continue

            return match

        return None

    def _on_request(self, request, **kwargs):
        match = self._find_match(request)

        # TODO(dcramer): find the correct class for this
        if match is None:
            error_msg = 'Connection refused: {0}'.format(request.url)
            response = ConnectionError(error_msg)

            self._calls.add(request, response)
            raise response

        headers = {
            'Content-Type': match['content_type'],
        }
        if match['adding_headers']:
            headers.update(match['adding_headers'])

        response = HTTPResponse(
            status=match['status'],
            body=BufferIO(match['body']),
            headers=headers,
            preload_content=False,
        )

        adapter = HTTPAdapter()

        response = adapter.build_response(request, response)
        if not match['stream']:
            response.content  # NOQA

        self._calls.add(request, response)

        return response

    def _start(self):
        import mock
        self._patcher = mock.patch('requests.Session.send', self._on_request)
        self._patcher.start()

    def _stop(self):
        self._patcher.stop()


# expose default mock namespace
_default_mock = RequestsMock()
__all__ = []
for __attr in (a for a in dir(_default_mock) if not a.startswith('_')):
    __all__.append(__attr)
    globals()[__attr] = getattr(_default_mock, __attr)
