Responses
=========

.. image:: https://travis-ci.org/dropbox/responses.png?branch=master
	:target: https://travis-ci.org/dropbox/responses

A utility library for mocking out the `requests` Python library.

Response body as string
-----------------------

.. code-block:: python

    import responses
    import requests

    @responses.activate
    def test_my_api():
        responses.add(responses.GET, 'http://twitter.com/api/1/foobar',
                      body='{"error": "not found"}', status=404,
                      content_type='application/json')

        resp = requests.get('http://twitter.com/api/1/foobar')

        assert resp.json() == {"error": "not found"}

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == 'http://twitter.com/api/1/foobar'
        assert responses.calls[0].response.content == '{"error": "not found"}'


Request callback
----------------

.. code-block:: python

    import json

    import responses
    import requests

    @responses.activate
    def test_calc_api():

        def request_callback(request):
            payload = json.loads(request.body)
            resp_body = {'value': sum(payload['numbers'])}
            headers = {'request-id': '728d329e-0e86-11e4-a748-0c84dc037c13'}
            return (200, headers, json.dumps(resp_body))

        responses.add_callback(
            responses.GET, 'http://calc.com/sum',
            callback=request_callback,
            content_type='application/json',
        )

        resp = requests.post(
            'http://calc.com/sum',
            json.dumps({'numbers': [1, 2, 3]}),
            headers={'content-type': 'application/json'},
        )

        assert resp.json() == {'value': 6}

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == 'http://calc.com/sum'
        assert responses.calls[0].response.content == '{"value": 6}'
        assert (
            responses.calls[0].response.headers['request-id'] ==
            '728d329e-0e86-11e4-a748-0c84dc037c13'
        )


.. note:: Responses requires Requests >= 1.0


License
=======

::

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
