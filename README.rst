Responses
=========

.. image:: https://travis-ci.org/getsentry/responses.svg?branch=master
	:target: https://travis-ci.org/getsentry/responses

A utility library for mocking out the `requests` Python library.

.. note:: Responses requires Python 2.7 or newer, and requests >= 2.0

Basics
------

The core of ``responses`` comes from registering mock responses:

.. code-block:: python

    import responses

    @responses.activate
    def test_simple():
        responses.add(responses.GET, 'http://twitter.com/api/1/foobar',
                      json={'error': 'not found'}, status=404)

        resp = requests.get('http://twitter.com/api/1/foobar')

        assert resp.json() == {"error": "not found"}

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == 'http://twitter.com/api/1/foobar'
        assert responses.calls[0].response.text == '{"error": "not found"}'

If you attempt to fetch a url which doesn't hit a match, ``responses`` will raise
a ``ConnectionError``:

.. code-block:: python

    import responses

    from requests.exceptions import ConnectionError

    @responses.activate
    def test_simple():
        with pytest.raises(ConnectionError):
            requests.get('http://twitter.com/api/1/foobar')

Lastly, you can pass an ``Exception`` as the body to trigger an error on the request:

.. code-block:: python

    import responses

    @responses.activate
    def test_simple():
        responses.add(responses.GET, 'http://twitter.com/api/1/foobar',
                      body=Exception('...'))
        with pytest.raises(Exception):
            requests.get('http://twitter.com/api/1/foobar')

Response Parameters
-------------------

Responses are automatically registered via params on ``add``, but can also be
passed directly:

.. code-block:: python

    import responses

    responses.add(
        responses.Response(
            method='GET',
            url='http://example.com',
        ),
    )

The following attributes can be passed to a Response mock:

method (``str``)
  The HTTP method (GET, POST, etc).

url (``str`` or compiled regular expression)
  The full resource URL.

match_querystring (``bool``)
  Disabled by default. Include the query string when matching requests.

body (``str`` or ``BufferedReader``)
  The response body.

json
  A python object representing the JSON response body. Automatically configures
  the appropriate Content-Type.

status (``int``)
  The HTTP status code.

content_type (``content_type``)
  Defaults to ``text/plain``.

headers (``dict``)
  Response headers.

stream (``bool``)
  Disabled by default. Indicates the response should use the streaming API.




Dynamic Responses
-----------------

You can utilize callbacks to provide dynamic responses. The callback must return
a tuple of (``status``, ``headers``, ``body``).

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
            responses.POST, 'http://calc.com/sum',
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
        assert responses.calls[0].response.text == '{"value": 6}'
        assert (
            responses.calls[0].response.headers['request-id'] ==
            '728d329e-0e86-11e4-a748-0c84dc037c13'
        )


Responses as a context manager
------------------------------

.. code-block:: python

    import responses
    import requests


    def test_my_api():
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, 'http://twitter.com/api/1/foobar',
                     body='{}', status=200,
                     content_type='application/json')
            resp = requests.get('http://twitter.com/api/1/foobar')

            assert resp.status_code == 200

        # outside the context manager requests will hit the remote server
        resp = requests.get('http://twitter.com/api/1/foobar')
        resp.status_code == 404


Assertions on declared responses
--------------------------------

When used as a context manager, Responses will, by default, raise an assertion
error if a url was registered but not accessed. This can be disabled by passing
the ``assert_all_requests_are_fired`` value:

.. code-block:: python

    import responses
    import requests


    def test_my_api():
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            rsps.add(responses.GET, 'http://twitter.com/api/1/foobar',
                     body='{}', status=200,
                     content_type='application/json')

Multiple Responses
------------------
You can also add multiple responses for the same url:

.. code-block:: python

    import responses
    import requests

    @responses.activate
    def test_my_api():
        responses.add(responses.GET, 'http://twitter.com/api/1/foobar', status=500)
        responses.add(responses.GET, 'http://twitter.com/api/1/foobar',
                      body='{}', status=200,
                      content_type='application/json')

        resp = requests.get('http://twitter.com/api/1/foobar')
        assert resp.status_code == 500
        resp = requests.get('http://twitter.com/api/1/foobar')
        assert resp.status_code == 200

Using a callback to modify the response
---------------------------------------

If you use customized processing in `requests` via subclassing/mixins, or if you
have library tools that interact with `requests` at a low level, you may need
to add extended processing to the mocked Response object to fully simlulate the
environment for your tests.  A `response_callback` can be used, which will be
wrapped by the library before being returned to the caller.  The callback
accepts a `response` as it's single argument, and is expected to return a
single `response` object.


.. code-block:: python

    import responses
    import requests

	def response_callback(resp):
		resp.callback_processed = True
		return resp

	with responses.RequestsMock(response_callback=response_callback) as m:
		m.add(responses.GET, 'http://example.com', body=b'test')
		resp = requests.get('http://example.com')
		assert resp.text == "test"
		assert hasattr(resp, 'callback_processed')
		assert resp.callback_processed is True
