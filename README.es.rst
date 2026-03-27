Responses
=========

.. image:: https://img.shields.io/pypi/v/responses.svg
    :target: https://pypi.python.org/pypi/responses/

.. image:: https://img.shields.io/pypi/pyversions/responses.svg
    :target: https://pypi.org/project/responses/

.. image:: https://img.shields.io/pypi/dm/responses
   :target: https://pypi.python.org/pypi/responses/

.. image:: https://codecov.io/gh/getsentry/responses/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/getsentry/responses/

Una biblioteca utilitaria para simular (*mock*) la biblioteca Python ``requests``.

..  note::

    Responses requiere Python 3.8 o superior, y requests >= 2.30.0


Tabla de Contenidos
-------------------

.. contents::


Instalación
-----------

``pip install responses``


Deprecaciones y Ruta de Migración
----------------------------------

Aquí encontrarás una lista de funcionalidades deprecadas y la ruta de migración para cada una.
Asegúrate de actualizar tu código según las indicaciones.

.. list-table:: Deprecaciones y Migración
   :widths: 50 25 50
   :header-rows: 1

   * - Funcionalidad Deprecada
     - Deprecada en Versión
     - Ruta de Migración
   * - ``responses.json_params_matcher``
     - 0.14.0
     - ``responses.matchers.json_params_matcher``
   * - ``responses.urlencoded_params_matcher``
     - 0.14.0
     - ``responses.matchers.urlencoded_params_matcher``
   * - argumento ``stream`` en ``Response`` y ``CallbackResponse``
     - 0.15.0
     - Usa el argumento ``stream`` directamente en la solicitud.
   * - argumento ``match_querystring`` en ``Response`` y ``CallbackResponse``.
     - 0.17.0
     - Usa ``responses.matchers.query_param_matcher`` o ``responses.matchers.query_string_matcher``
   * - ``responses.assert_all_requests_are_fired``, ``responses.passthru_prefixes``, ``responses.target``
     - 0.20.0
     - Usa ``responses.mock.assert_all_requests_are_fired``,
       ``responses.mock.passthru_prefixes``, ``responses.mock.target`` en su lugar.

Conceptos Básicos
-----------------

El núcleo de ``responses`` consiste en registrar respuestas simuladas y envolver la función de
prueba con el decorador ``responses.activate``. ``responses`` ofrece una interfaz similar a
``requests``.

Interfaz Principal
^^^^^^^^^^^^^^^^^^

* responses.add(``Response`` o argumentos de ``Response``) — permite registrar un objeto
  ``Response`` o proporcionar directamente los argumentos del objeto ``Response``.
  Ver `Parámetros de Response`_

.. code-block:: python

    import responses
    import requests


    @responses.activate
    def test_simple():
        # Registro mediante objeto 'Response'
        rsp1 = responses.Response(
            method="PUT",
            url="http://example.com",
        )
        responses.add(rsp1)
        # Registro mediante argumentos directos
        responses.add(
            responses.GET,
            "http://twitter.com/api/1/foobar",
            json={"error": "not found"},
            status=404,
        )

        resp = requests.get("http://twitter.com/api/1/foobar")
        resp2 = requests.put("http://example.com")

        assert resp.json() == {"error": "not found"}
        assert resp.status_code == 404

        assert resp2.status_code == 200
        assert resp2.request.method == "PUT"


Si intentas acceder a una URL que no coincide con ninguna registrada, ``responses``
lanzará un ``ConnectionError``:

.. code-block:: python

    import responses
    import requests

    from requests.exceptions import ConnectionError


    @responses.activate
    def test_simple():
        with pytest.raises(ConnectionError):
            requests.get("http://twitter.com/api/1/foobar")


Atajos
^^^^^^

Los atajos ofrecen una versión abreviada de ``responses.add()`` donde el argumento del
método ya viene predefinido.

* responses.delete(``argumentos de Response``) — registra una respuesta DELETE
* responses.get(``argumentos de Response``) — registra una respuesta GET
* responses.head(``argumentos de Response``) — registra una respuesta HEAD
* responses.options(``argumentos de Response``) — registra una respuesta OPTIONS
* responses.patch(``argumentos de Response``) — registra una respuesta PATCH
* responses.post(``argumentos de Response``) — registra una respuesta POST
* responses.put(``argumentos de Response``) — registra una respuesta PUT

.. code-block:: python

    import responses
    import requests


    @responses.activate
    def test_simple():
        responses.get(
            "http://twitter.com/api/1/foobar",
            json={"type": "get"},
        )

        responses.post(
            "http://twitter.com/api/1/foobar",
            json={"type": "post"},
        )

        responses.patch(
            "http://twitter.com/api/1/foobar",
            json={"type": "patch"},
        )

        resp_get = requests.get("http://twitter.com/api/1/foobar")
        resp_post = requests.post("http://twitter.com/api/1/foobar")
        resp_patch = requests.patch("http://twitter.com/api/1/foobar")

        assert resp_get.json() == {"type": "get"}
        assert resp_post.json() == {"type": "post"}
        assert resp_patch.json() == {"type": "patch"}

Responses como context manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

En lugar de envolver toda la función con un decorador, puedes usar un context manager.

.. code-block:: python

    import responses
    import requests


    def test_my_api():
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://twitter.com/api/1/foobar",
                body="{}",
                status=200,
                content_type="application/json",
            )
            resp = requests.get("http://twitter.com/api/1/foobar")

            assert resp.status_code == 200

        # fuera del context manager, las solicitudes llegan al servidor real
        resp = requests.get("http://twitter.com/api/1/foobar")
        resp.status_code == 404


Parámetros de Response
-----------------------

Los siguientes atributos pueden pasarse a un mock de Response:

method (``str``)
    El método HTTP (GET, POST, etc.).

url (``str`` o ``expresión regular compilada``)
    La URL completa del recurso.

match_querystring (``bool``)
    DEPRECADO: Usa ``responses.matchers.query_param_matcher`` o
    ``responses.matchers.query_string_matcher``

    Incluye la cadena de consulta (*query string*) al comparar solicitudes.
    Activado por defecto si la URL de respuesta contiene una cadena de consulta;
    desactivado si no la contiene o si la URL es una expresión regular.

body (``str`` o ``BufferedReader`` o ``Exception``)
    El cuerpo de la respuesta. Lee más en `Excepción como cuerpo de Response`_

json
    Un objeto Python que representa el cuerpo de la respuesta en formato JSON.
    Configura automáticamente el ``Content-Type`` apropiado.

status (``int``)
    El código de estado HTTP.

content_type (``content_type``)
    Por defecto es ``text/plain``.

headers (``dict``)
    Cabeceras de la respuesta.

stream (``bool``)
    DEPRECADO: usa el argumento ``stream`` directamente en la solicitud.

auto_calculate_content_length (``bool``)
    Desactivado por defecto. Calcula automáticamente la longitud de un cuerpo de tipo
    cadena o JSON.

match (``tuple``)
    Un iterable (se recomienda ``tuple``) de callbacks para comparar solicitudes en
    función de sus atributos.
    El módulo proporciona múltiples comparadores que puedes utilizar para verificar:

    * contenido del cuerpo en formato JSON
    * contenido del cuerpo en formato URL-encoded
    * parámetros de consulta de la solicitud
    * cadena de consulta de la solicitud (similar a los parámetros de consulta, pero acepta una cadena como entrada)
    * kwargs proporcionados a la solicitud, por ejemplo ``stream``, ``verify``
    * contenido y cabeceras de tipo ``multipart/form-data`` en la solicitud
    * cabeceras de la solicitud
    * identificador de fragmento de la solicitud

    El usuario también puede crear un comparador personalizado.
    Lee más en `Comparación de Solicitudes`_


Excepción como cuerpo de Response
-----------------------------------

Puedes pasar una ``Exception`` como cuerpo para provocar un error en la solicitud:

.. code-block:: python

    import responses
    import requests


    @responses.activate
    def test_simple():
        responses.get("http://twitter.com/api/1/foobar", body=Exception("..."))
        with pytest.raises(Exception):
            requests.get("http://twitter.com/api/1/foobar")


Comparación de Solicitudes
---------------------------

Comparación del Contenido del Cuerpo de la Solicitud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Al agregar respuestas para endpoints que reciben datos en la solicitud, puedes añadir
comparadores para asegurarte de que tu código envía los parámetros correctos y para
ofrecer respuestas diferentes según el contenido del cuerpo. ``responses`` ofrece
comparadores para cuerpos de solicitud en formato JSON y URL-encoded.

Datos URL-encoded
"""""""""""""""""

.. code-block:: python

    import responses
    import requests
    from responses import matchers


    @responses.activate
    def test_calc_api():
        responses.post(
            url="http://calc.com/sum",
            body="4",
            match=[matchers.urlencoded_params_matcher({"left": "1", "right": "3"})],
        )
        requests.post("http://calc.com/sum", data={"left": 1, "right": 3})


Datos JSON
""""""""""

La comparación de datos codificados en JSON se realiza con ``matchers.json_params_matcher()``.

.. code-block:: python

    import responses
    import requests
    from responses import matchers


    @responses.activate
    def test_calc_api():
        responses.post(
            url="http://example.com/",
            body="one",
            match=[
                matchers.json_params_matcher({"page": {"name": "first", "type": "json"}})
            ],
        )
        resp = requests.request(
            "POST",
            "http://example.com/",
            headers={"Content-Type": "application/json"},
            json={"page": {"name": "first", "type": "json"}},
        )


Comparador de Parámetros de Consulta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Parámetros de Consulta como Diccionario
""""""""""""""""""""""""""""""""""""""""

Puedes usar la función ``matchers.query_param_matcher`` para comparar contra el
parámetro ``params`` de la solicitud. Utiliza el mismo diccionario que usarías en el
argumento ``params`` de ``request``.

Nota: no incluyas los parámetros de consulta como parte de la URL. Evita usar el
argumento deprecado ``match_querystring``.

.. code-block:: python

    import responses
    import requests
    from responses import matchers


    @responses.activate
    def test_calc_api():
        url = "http://example.com/test"
        params = {"hello": "world", "I am": "a big test"}
        responses.get(
            url=url,
            body="test",
            match=[matchers.query_param_matcher(params)],
        )

        resp = requests.get(url, params=params)

        constructed_url = r"http://example.com/test?I+am=a+big+test&hello=world"
        assert resp.url == constructed_url
        assert resp.request.url == constructed_url
        assert resp.request.params == params

Por defecto, el comparador valida que todos los parámetros coincidan estrictamente.
Para validar que solo los parámetros especificados en el comparador estén presentes en
la solicitud original, usa ``strict_match=False``.

Parámetros de Consulta como Cadena
""""""""""""""""""""""""""""""""""""

Como alternativa, puedes usar el valor de la cadena de consulta en
``matchers.query_string_matcher`` para comparar los parámetros de consulta de tu
solicitud.

.. code-block:: python

    import requests
    import responses
    from responses import matchers


    @responses.activate
    def my_func():
        responses.get(
            "https://httpbin.org/get",
            match=[matchers.query_string_matcher("didi=pro&test=1")],
        )
        resp = requests.get("https://httpbin.org/get", params={"test": 1, "didi": "pro"})


    my_func()


Comparador de Argumentos de la Solicitud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Para validar los argumentos de la solicitud, usa la función
``matchers.request_kwargs_matcher`` para comparar contra los kwargs de la solicitud.

Solo se admiten los siguientes argumentos: ``timeout``, ``verify``, ``proxies``, ``stream``, ``cert``.

Nota: solo se validarán los argumentos proporcionados a ``matchers.request_kwargs_matcher``.

.. code-block:: python

    import responses
    import requests
    from responses import matchers

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        req_kwargs = {
            "stream": True,
            "verify": False,
        }
        rsps.add(
            "GET",
            "http://111.com",
            match=[matchers.request_kwargs_matcher(req_kwargs)],
        )

        requests.get("http://111.com", stream=True)

        # >>>  Los argumentos no coinciden: {stream: True, verify: True} no coinciden con {stream: True, verify: False}


Validación de Datos ``multipart/form-data``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Para validar el cuerpo y las cabeceras de una solicitud con datos ``multipart/form-data``,
puedes usar ``matchers.multipart_matcher``. Los parámetros ``data`` y ``files``
proporcionados se compararán con la solicitud:

.. code-block:: python

    import requests
    import responses
    from responses.matchers import multipart_matcher


    @responses.activate
    def my_func():
        req_data = {"some": "other", "data": "fields"}
        req_files = {"file_name": b"Old World!"}
        responses.post(
            url="http://httpbin.org/post",
            match=[multipart_matcher(req_files, data=req_data)],
        )
        resp = requests.post("http://httpbin.org/post", files={"file_name": b"New World!"})


    my_func()
    # >>> genera ConnectionError: multipart/form-data no coincide. El cuerpo (body) del request es diferente

Validación del Identificador de Fragmento de la Solicitud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Para validar el identificador de fragmento de la URL de la solicitud, puedes usar
``matchers.fragment_identifier_matcher``. El comparador toma como entrada la cadena
de fragmento (todo lo que aparece después del signo ``#``):

.. code-block:: python

    import requests
    import responses
    from responses.matchers import fragment_identifier_matcher


    @responses.activate
    def run():
        url = "http://example.com?ab=xy&zed=qwe#test=1&foo=bar"
        responses.get(
            url,
            match=[fragment_identifier_matcher("test=1&foo=bar")],
            body=b"test",
        )

        # dos solicitudes para verificar el orden inverso del identificador de fragmento
        resp = requests.get("http://example.com?ab=xy&zed=qwe#test=1&foo=bar")
        resp = requests.get("http://example.com?zed=qwe&ab=xy#foo=bar&test=1")


    run()

Validación de Cabeceras de la Solicitud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Al agregar respuestas puedes especificar comparadores para asegurarte de que tu código
envía las cabeceras correctas y para ofrecer respuestas diferentes según las cabeceras
de la solicitud.

.. code-block:: python

    import responses
    import requests
    from responses import matchers


    @responses.activate
    def test_content_type():
        responses.get(
            url="http://example.com/",
            body="hello world",
            match=[matchers.header_matcher({"Accept": "text/plain"})],
        )

        responses.get(
            url="http://example.com/",
            json={"content": "hello world"},
            match=[matchers.header_matcher({"Accept": "application/json"})],
        )

        # ¡solicitudes en orden inverso al que fueron agregadas!
        resp = requests.get("http://example.com/", headers={"Accept": "application/json"})
        assert resp.json() == {"content": "hello world"}

        resp = requests.get("http://example.com/", headers={"Accept": "text/plain"})
        assert resp.text == "hello world"

Dado que ``requests`` enviará varias cabeceras estándar además de las especificadas por
tu código, las cabeceras adicionales a las pasadas al comparador se ignoran por defecto.
Puedes cambiar este comportamiento pasando ``strict_match=True`` al comparador para
asegurarte de que solo se envíen exactamente las cabeceras esperadas. Ten en cuenta que
probablemente necesitarás usar un ``PreparedRequest`` en tu código para evitar que
``requests`` incluya cabeceras adicionales.

.. code-block:: python

    import responses
    import requests
    from responses import matchers


    @responses.activate
    def test_content_type():
        responses.get(
            url="http://example.com/",
            body="hello world",
            match=[matchers.header_matcher({"Accept": "text/plain"}, strict_match=True)],
        )

        # esto fallará porque requests agrega sus propias cabeceras
        with pytest.raises(ConnectionError):
            requests.get("http://example.com/", headers={"Accept": "text/plain"})

        # una solicitud preparada donde se sobreescriben las cabeceras antes del envío sí funcionará
        session = requests.Session()
        prepped = session.prepare_request(
            requests.Request(
                method="GET",
                url="http://example.com/",
            )
        )
        prepped.headers = {"Accept": "text/plain"}

        resp = session.send(prepped)
        assert resp.text == "hello world"


Creación de un Comparador Personalizado
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Si tu aplicación requiere otras codificaciones o una validación de datos diferente,
puedes crear tu propio comparador que devuelva ``Tuple[matches: bool, reason: str]``.
El booleano indica ``True`` o ``False`` según si los parámetros de la solicitud
coinciden, y la cadena contiene la razón en caso de fallo. Tu comparador puede esperar
recibir un parámetro ``PreparedRequest`` proporcionado por ``responses``.

Nota: ``PreparedRequest`` está personalizado y tiene atributos adicionales ``params`` y ``req_kwargs``.

Registro de Responses
----------------------

Registro por Defecto
^^^^^^^^^^^^^^^^^^^^^

Por defecto, ``responses`` buscará entre todos los objetos ``Response`` registrados y
devolverá la primera coincidencia. Si solo hay un ``Response`` registrado, el registro
permanece sin cambios. Sin embargo, si se encuentran múltiples coincidencias para la
misma solicitud, se devuelve la primera coincidencia y se elimina del registro.

Registro Ordenado
^^^^^^^^^^^^^^^^^

En algunos escenarios es importante preservar el orden de las solicitudes y respuestas.
Puedes usar ``registries.OrderedRegistry`` para forzar que todos los objetos ``Response``
dependan del orden de inserción y del índice de invocación.
En el siguiente ejemplo se agregan múltiples objetos ``Response`` que apuntan a la misma
URL. Sin embargo, verás que el código de estado depende del orden de invocación.

.. code-block:: python

    import requests

    import responses
    from responses.registries import OrderedRegistry


    @responses.activate(registry=OrderedRegistry)
    def test_invocation_index():
        responses.get(
            "http://twitter.com/api/1/foobar",
            json={"msg": "not found"},
            status=404,
        )
        responses.get(
            "http://twitter.com/api/1/foobar",
            json={"msg": "OK"},
            status=200,
        )
        responses.get(
            "http://twitter.com/api/1/foobar",
            json={"msg": "OK"},
            status=200,
        )
        responses.get(
            "http://twitter.com/api/1/foobar",
            json={"msg": "not found"},
            status=404,
        )

        resp = requests.get("http://twitter.com/api/1/foobar")
        assert resp.status_code == 404
        resp = requests.get("http://twitter.com/api/1/foobar")
        assert resp.status_code == 200
        resp = requests.get("http://twitter.com/api/1/foobar")
        assert resp.status_code == 200
        resp = requests.get("http://twitter.com/api/1/foobar")
        assert resp.status_code == 404


Registro Personalizado
^^^^^^^^^^^^^^^^^^^^^^^

Los ``registries`` incluidos son adecuados para la mayoría de los casos de uso, pero para
manejar condiciones especiales puedes implementar un registro personalizado que siga la
interfaz de ``registries.FirstMatchRegistry``. Redefinir el método ``find`` te permitirá
crear una lógica de búsqueda personalizada y devolver el ``Response`` apropiado.

Ejemplo que muestra cómo establecer un registro personalizado:

.. code-block:: python

    import responses
    from responses import registries


    class CustomRegistry(registries.FirstMatchRegistry):
        pass


    print("Before tests:", responses.mock.get_registry())
    """ Before tests: <responses.registries.FirstMatchRegistry object> """


    # usando decorador de función
    @responses.activate(registry=CustomRegistry)
    def run():
        print("Within test:", responses.mock.get_registry())
        """ Within test: <__main__.CustomRegistry object> """


    run()

    print("After test:", responses.mock.get_registry())
    """ After test: <responses.registries.FirstMatchRegistry object> """

    # usando context manager
    with responses.RequestsMock(registry=CustomRegistry) as rsps:
        print("In context manager:", rsps.get_registry())
        """ In context manager: <__main__.CustomRegistry object> """

    print("After exit from context manager:", responses.mock.get_registry())
    """
    After exit from context manager: <responses.registries.FirstMatchRegistry object>
    """

Respuestas Dinámicas
---------------------

Puedes usar callbacks para proporcionar respuestas dinámicas. El callback debe devolver
una tupla de (``status``, ``headers``, ``body``).

.. code-block:: python

    import json

    import responses
    import requests


    @responses.activate
    def test_calc_api():
        def request_callback(request):
            payload = json.loads(request.body)
            resp_body = {"value": sum(payload["numbers"])}
            headers = {"request-id": "728d329e-0e86-11e4-a748-0c84dc037c13"}
            return (200, headers, json.dumps(resp_body))

        responses.add_callback(
            responses.POST,
            "http://calc.com/sum",
            callback=request_callback,
            content_type="application/json",
        )

        resp = requests.post(
            "http://calc.com/sum",
            json.dumps({"numbers": [1, 2, 3]}),
            headers={"content-type": "application/json"},
        )

        assert resp.json() == {"value": 6}

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "http://calc.com/sum"
        assert responses.calls[0].response.text == '{"value": 6}'
        assert (
            responses.calls[0].response.headers["request-id"]
            == "728d329e-0e86-11e4-a748-0c84dc037c13"
        )

También puedes pasar una expresión regular compilada a ``add_callback`` para que
coincida con múltiples URLs:

.. code-block:: python

    import re, json

    from functools import reduce

    import responses
    import requests

    operators = {
        "sum": lambda x, y: x + y,
        "prod": lambda x, y: x * y,
        "pow": lambda x, y: x**y,
    }


    @responses.activate
    def test_regex_url():
        def request_callback(request):
            payload = json.loads(request.body)
            operator_name = request.path_url[1:]

            operator = operators[operator_name]

            resp_body = {"value": reduce(operator, payload["numbers"])}
            headers = {"request-id": "728d329e-0e86-11e4-a748-0c84dc037c13"}
            return (200, headers, json.dumps(resp_body))

        responses.add_callback(
            responses.POST,
            re.compile("http://calc.com/(sum|prod|pow|unsupported)"),
            callback=request_callback,
            content_type="application/json",
        )

        resp = requests.post(
            "http://calc.com/prod",
            json.dumps({"numbers": [2, 3, 4]}),
            headers={"content-type": "application/json"},
        )
        assert resp.json() == {"value": 24}


    test_regex_url()


Si quieres pasar argumentos adicionales al callback, por ejemplo para reutilizar una
función callback con un resultado ligeramente diferente, puedes usar ``functools.partial``:

.. code-block:: python

    from functools import partial


    def request_callback(request, id=None):
        payload = json.loads(request.body)
        resp_body = {"value": sum(payload["numbers"])}
        headers = {"request-id": id}
        return (200, headers, json.dumps(resp_body))


    responses.add_callback(
        responses.POST,
        "http://calc.com/sum",
        callback=partial(request_callback, id="728d329e-0e86-11e4-a748-0c84dc037c13"),
        content_type="application/json",
    )


Integración con Frameworks de Pruebas Unitarias
------------------------------------------------

Responses como fixture de ``pytest``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Usa el paquete pytest-responses para exportar ``responses`` como una fixture de pytest.

``pip install pytest-responses``

Luego puedes acceder a ella en un script de pytest de la siguiente manera:

.. code-block:: python

    import pytest_responses


    def test_api(responses):
        responses.get(
            "http://twitter.com/api/1/foobar",
            body="{}",
            status=200,
            content_type="application/json",
        )
        resp = requests.get("http://twitter.com/api/1/foobar")
        assert resp.status_code == 200

Agregar respuestas por defecto para cada prueba
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Al ejecutar con pruebas de ``unittest``, responses puede usarse para definir respuestas
genéricas a nivel de clase que cada prueba puede complementar. Se puede aplicar una
interfaz similar en el framework ``pytest``.

.. code-block:: python

    class TestMyApi(unittest.TestCase):
        def setUp(self):
            responses.get("https://example.com", body="within setup")
            # aquí van otros self.responses.add(...)

        @responses.activate
        def test_my_func(self):
            responses.get(
                "https://httpbin.org/get",
                match=[matchers.query_param_matcher({"test": "1", "didi": "pro"})],
                body="within test",
            )
            resp = requests.get("https://example.com")
            resp2 = requests.get(
                "https://httpbin.org/get", params={"test": "1", "didi": "pro"}
            )
            print(resp.text)
            # >>> within setup
            print(resp2.text)
            # >>> within test


Métodos de RequestMock: start, stop, reset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``responses`` tiene los métodos ``start``, ``stop``, ``reset``, muy análogos a
`unittest.mock.patch <https://docs.python.org/3/library/unittest.mock.html#patch-methods-start-and-stop>`_.
Esto simplifica el uso de mocks de solicitudes en métodos ``setup`` o cuando se quieren
aplicar múltiples parches sin anidar decoradores ni sentencias ``with``.

.. code-block:: python

    class TestUnitTestPatchSetup:
        def setup(self):
            """Crea una instancia de ``RequestsMock`` y la inicia."""
            self.r_mock = responses.RequestsMock(assert_all_requests_are_fired=True)
            self.r_mock.start()

            # opcionalmente se pueden registrar algunas respuestas por defecto
            self.r_mock.get("https://example.com", status=505)
            self.r_mock.put("https://example.com", status=506)

        def teardown(self):
            """Detiene y reinicia la instancia de RequestsMock.

            Si ``assert_all_requests_are_fired`` está en ``True``, se lanzará un error
            si algunas solicitudes no fueron procesadas.
            """
            self.r_mock.stop()
            self.r_mock.reset()

        def test_function(self):
            resp = requests.get("https://example.com")
            assert resp.status_code == 505

            resp = requests.put("https://example.com")
            assert resp.status_code == 506


Aserciones sobre Responses Declaradas
---------------------------------------

Cuando se usa como context manager, Responses lanzará por defecto un error de
aserción si una URL fue registrada pero no fue accedida. Esto puede desactivarse
pasando el valor ``assert_all_requests_are_fired``:

.. code-block:: python

    import responses
    import requests


    def test_my_api():
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            rsps.add(
                responses.GET,
                "http://twitter.com/api/1/foobar",
                body="{}",
                status=200,
                content_type="application/json",
            )

Cuando ``assert_all_requests_are_fired=True`` y ocurre una excepción dentro del gestor
de contexto, las aserciones sobre las solicitudes no ejecutadas se lanzarán igualmente.
Esto proporciona contexto valioso sobre qué solicitudes simuladas fueron o no invocadas
al depurar fallos en las pruebas.

.. code-block:: python

    import responses
    import requests


    def test_with_exception():
        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            rsps.add(responses.GET, "http://example.com/users", body="test")
            rsps.add(responses.GET, "http://example.com/profile", body="test")
            requests.get("http://example.com/users")
            raise ValueError("Something went wrong")

        # Salida:
        # ValueError: Something went wrong
        #
        # During handling of the above exception, another exception occurred:
        #
        # AssertionError: Not all requests have been executed [('GET', 'http://example.com/profile')]

Verificar el Número de Llamadas a una Solicitud
-------------------------------------------------

Aserción basada en el objeto ``Response``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Cada objeto ``Response`` tiene el atributo ``call_count`` que puede inspeccionarse
para comprobar cuántas veces fue invocada cada solicitud.

.. code-block:: python

    @responses.activate
    def test_call_count_with_matcher():
        rsp = responses.get(
            "http://www.example.com",
            match=(matchers.query_param_matcher({}),),
        )
        rsp2 = responses.get(
            "http://www.example.com",
            match=(matchers.query_param_matcher({"hello": "world"}),),
            status=777,
        )
        requests.get("http://www.example.com")
        resp1 = requests.get("http://www.example.com")
        requests.get("http://www.example.com?hello=world")
        resp2 = requests.get("http://www.example.com?hello=world")

        assert resp1.status_code == 200
        assert resp2.status_code == 777

        assert rsp.call_count == 2
        assert rsp2.call_count == 2

Aserción basada en la URL exacta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Verifica que la solicitud fue invocada exactamente n veces.

.. code-block:: python

    import responses
    import requests


    @responses.activate
    def test_assert_call_count():
        responses.get("http://example.com")

        requests.get("http://example.com")
        assert responses.assert_call_count("http://example.com", 1) is True

        requests.get("http://example.com")
        with pytest.raises(AssertionError) as excinfo:
            responses.assert_call_count("http://example.com", 1)
        assert (
            "Expected URL 'http://example.com' to be called 1 times. Called 2 times."
            in str(excinfo.value)
        )


    @responses.activate
    def test_assert_call_count_always_match_qs():
        responses.get("http://www.example.com")
        requests.get("http://www.example.com")
        requests.get("http://www.example.com?hello=world")

        # Una llamada por cada URL; la cadena de consulta se compara por defecto
        responses.assert_call_count("http://www.example.com", 1) is True
        responses.assert_call_count("http://www.example.com?hello=world", 1) is True


Verificar los Datos de las Llamadas a Solicitudes
--------------------------------------------------

El objeto ``Request`` tiene una lista ``calls`` cuyos elementos corresponden a objetos
``Call`` en la lista global del ``Registry``. Esto puede ser útil cuando el orden de
las solicitudes no está garantizado pero necesitas verificar su corrección, por ejemplo
en aplicaciones multihilo.

.. code-block:: python

    import concurrent.futures
    import responses
    import requests


    @responses.activate
    def test_assert_calls_on_resp():
        rsp1 = responses.patch("http://www.foo.bar/1/", status=200)
        rsp2 = responses.patch("http://www.foo.bar/2/", status=400)
        rsp3 = responses.patch("http://www.foo.bar/3/", status=200)

        def update_user(uid, is_active):
            url = f"http://www.foo.bar/{uid}/"
            response = requests.patch(url, json={"is_active": is_active})
            return response

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_uid = {
                executor.submit(update_user, uid, is_active): uid
                for (uid, is_active) in [("3", True), ("2", True), ("1", False)]
            }
            for future in concurrent.futures.as_completed(future_to_uid):
                uid = future_to_uid[future]
                response = future.result()
                print(f"{uid} updated with {response.status_code} status code")

        assert len(responses.calls) == 3  # total de llamadas

        assert rsp1.call_count == 1
        assert rsp1.calls[0] in responses.calls
        assert rsp1.calls[0].response.status_code == 200
        assert json.loads(rsp1.calls[0].request.body) == {"is_active": False}

        assert rsp2.call_count == 1
        assert rsp2.calls[0] in responses.calls
        assert rsp2.calls[0].response.status_code == 400
        assert json.loads(rsp2.calls[0].request.body) == {"is_active": True}

        assert rsp3.call_count == 1
        assert rsp3.calls[0] in responses.calls
        assert rsp3.calls[0].response.status_code == 200
        assert json.loads(rsp3.calls[0].request.body) == {"is_active": True}

Múltiples Responses
--------------------

También puedes agregar múltiples respuestas para la misma URL:

.. code-block:: python

    import responses
    import requests


    @responses.activate
    def test_my_api():
        responses.get("http://twitter.com/api/1/foobar", status=500)
        responses.get(
            "http://twitter.com/api/1/foobar",
            body="{}",
            status=200,
            content_type="application/json",
        )

        resp = requests.get("http://twitter.com/api/1/foobar")
        assert resp.status_code == 500
        resp = requests.get("http://twitter.com/api/1/foobar")
        assert resp.status_code == 200


Redirección de URL
-------------------

En el siguiente ejemplo puedes ver cómo crear una cadena de redirección y agregar una
excepción personalizada que se lanzará durante la ejecución y contendrá el historial
de redirecciones.

..  code-block::

    A -> 301 redirect -> B
    B -> 301 redirect -> C
    C -> connection issue

.. code-block:: python

    import pytest
    import requests

    import responses


    @responses.activate
    def test_redirect():
        # crea múltiples objetos Response donde los dos primeros contienen cabeceras de redirección
        rsp1 = responses.Response(
            responses.GET,
            "http://example.com/1",
            status=301,
            headers={"Location": "http://example.com/2"},
        )
        rsp2 = responses.Response(
            responses.GET,
            "http://example.com/2",
            status=301,
            headers={"Location": "http://example.com/3"},
        )
        rsp3 = responses.Response(responses.GET, "http://example.com/3", status=200)

        # registra los objetos Response generados en el módulo ``responses``
        responses.add(rsp1)
        responses.add(rsp2)
        responses.add(rsp3)

        # realiza la primera solicitud para generar una respuesta genuina de ``requests``
        # este objeto contendrá atributos reales de la respuesta, como ``history``
        rsp = requests.get("http://example.com/1")
        responses.calls.reset()

        # personaliza la excepción con el atributo ``response``
        my_error = requests.ConnectionError("custom error")
        my_error.response = rsp

        # actualiza el cuerpo de la 3ª respuesta con una excepción; esta se lanzará durante la ejecución
        rsp3.body = my_error

        with pytest.raises(requests.ConnectionError) as exc_info:
            requests.get("http://example.com/1")

        assert exc_info.value.args[0] == "custom error"
        assert rsp1.url in exc_info.value.response.history[0].url
        assert rsp2.url in exc_info.value.response.history[1].url


Validar el Mecanismo de ``Retry``
----------------------------------

Si usas las características de ``Retry`` de ``urllib3`` y quieres cubrir escenarios que
pongan a prueba tus límites de reintentos, también puedes hacerlo con ``responses``.
El mejor enfoque es usar un `Registro Ordenado`_.

.. code-block:: python

    import requests

    import responses
    from responses import registries
    from urllib3.util import Retry


    @responses.activate(registry=registries.OrderedRegistry)
    def test_max_retries():
        url = "https://example.com"
        rsp1 = responses.get(url, body="Error", status=500)
        rsp2 = responses.get(url, body="Error", status=500)
        rsp3 = responses.get(url, body="Error", status=500)
        rsp4 = responses.get(url, body="OK", status=200)

        session = requests.Session()

        adapter = requests.adapters.HTTPAdapter(
            max_retries=Retry(
                total=4,
                backoff_factor=0.1,
                status_forcelist=[500],
                method_whitelist=["GET", "POST", "PATCH"],
            )
        )
        session.mount("https://", adapter)

        resp = session.get(url)

        assert resp.status_code == 200
        assert rsp1.call_count == 1
        assert rsp2.call_count == 1
        assert rsp3.call_count == 1
        assert rsp4.call_count == 1


Usar un Callback para Modificar la Respuesta
---------------------------------------------

Si usas procesamiento personalizado en ``requests`` mediante subclases o mixins, o si
tienes herramientas que interactúan con ``requests`` a bajo nivel, puede
que necesites agregar procesamiento extendido al objeto Response simulado para simular
completamente el entorno de tus pruebas. Se puede usar un ``response_callback``, que
será envuelto antes de devolverse al invocador. El callback acepta
una ``response`` como único argumento y se espera que devuelva un único objeto
``response``.

.. code-block:: python

    import responses
    import requests


    def response_callback(resp):
        resp.callback_processed = True
        return resp


    with responses.RequestsMock(response_callback=response_callback) as m:
        m.add(responses.GET, "http://example.com", body=b"test")
        resp = requests.get("http://example.com")
        assert resp.text == "test"
        assert hasattr(resp, "callback_processed")
        assert resp.callback_processed is True


Permitir el Paso de Solicitudes Reales
---------------------------------------

En algunos casos puede ser necesario permitir que ciertas solicitudes pasen a través de
responses y lleguen a un servidor real. Esto se puede hacer con los métodos
``add_passthru``:

.. code-block:: python

    import responses


    @responses.activate
    def test_my_api():
        responses.add_passthru("https://percy.io")

Esto permitirá que cualquier solicitud que coincida con ese prefijo, y que no esté
registrada como respuesta simulada, pase usando el comportamiento estándar.

Los endpoints de paso pueden configurarse con patrones de expresión regular si necesitas
permitir que todo un dominio o subárbol de ruta envíe solicitudes:

.. code-block:: python

    responses.add_passthru(re.compile("https://percy.io/\\w+"))


Por último, puedes usar el argumento ``passthrough`` del objeto ``Response`` para forzar
que una respuesta se comporte como paso directo.

.. code-block:: python

    # Habilitar passthrough para una sola respuesta
    response = Response(
        responses.GET,
        "http://example.com",
        body="not used",
        passthrough=True,
    )
    responses.add(response)

    # Usar PassthroughResponse
    response = PassthroughResponse(responses.GET, "http://example.com")
    responses.add(response)

Ver/Modificar Responses Registradas
-------------------------------------

Las responses registradas están disponibles como método público de la instancia
RequestMock. A veces es útil para depuración ver la pila de responses registradas,
a la que se puede acceder mediante ``responses.registered()``.

La función ``replace`` permite modificar una ``response`` previamente registrada.
La firma del método es idéntica a ``add``. Las ``response`` s se identifican por
``method`` y ``url``. Solo se reemplaza la primera ``response`` que coincide.

.. code-block:: python

    import responses
    import requests


    @responses.activate
    def test_replace():
        responses.get("http://example.org", json={"data": 1})
        responses.replace(responses.GET, "http://example.org", json={"data": 2})

        resp = requests.get("http://example.org")

        assert resp.json() == {"data": 2}


La función ``upsert`` permite modificar una ``response`` previamente registrada al igual
que ``replace``. Si la response no está registrada, la función ``upsert`` la registrará
como ``add``.

``remove`` acepta un argumento ``method`` y ``url`` y eliminará **todas** las responses
coincidentes de la lista de registradas.

Por último, ``reset`` reiniciará todas las responses registradas.

Corrutinas y Multihilo
-----------------------

``responses`` admite tanto corrutinas como multihilo de forma nativa.
Ten en cuenta que ``responses`` bloquea el hilo en el objeto ``RequestMock``,
permitiendo que solo un hilo acceda a él a la vez.

.. code-block:: python

    async def test_async_calls():
        @responses.activate
        async def run():
            responses.get(
                "http://twitter.com/api/1/foobar",
                json={"error": "not found"},
                status=404,
            )

            resp = requests.get("http://twitter.com/api/1/foobar")
            assert resp.json() == {"error": "not found"}
            assert responses.calls[0].request.url == "http://twitter.com/api/1/foobar"

        await run()

Funcionalidades BETA
---------------------

A continuación encontrarás una lista de funcionalidades BETA. Aunque intentaremos
mantener la compatibilidad con versiones anteriores de la API con la versión publicada, nos
reservamos el derecho de cambiar estas APIs antes de que sean consideradas estables.
Comparte tu opinión a través de
`GitHub Issues <https://github.com/getsentry/responses/issues>`_.

Grabar Responses en Archivos
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Puedes realizar solicitudes reales al servidor y ``responses`` grabará automáticamente
la salida en un archivo. Los datos grabados se almacenan en formato
`YAML <https://yaml.org>`_.

Aplica el decorador ``@responses._recorder.record(file_path="out.yaml")`` a cualquier
función donde realices solicitudes para grabar las responses en el archivo ``out.yaml``.

El siguiente código:

.. code-block:: python

    import requests
    from responses import _recorder


    def another():
        rsp = requests.get("https://httpstat.us/500")
        rsp = requests.get("https://httpstat.us/202")


    @_recorder.record(file_path="out.yaml")
    def test_recorder():
        rsp = requests.get("https://httpstat.us/404")
        rsp = requests.get("https://httpbin.org/status/wrong")
        another()

producirá la siguiente salida:

.. code-block:: yaml

    responses:
    - response:
        auto_calculate_content_length: false
        body: 404 Not Found
        content_type: text/plain
        method: GET
        status: 404
        url: https://httpstat.us/404
    - response:
        auto_calculate_content_length: false
        body: Invalid status code
        content_type: text/plain
        method: GET
        status: 400
        url: https://httpbin.org/status/wrong
    - response:
        auto_calculate_content_length: false
        body: 500 Internal Server Error
        content_type: text/plain
        method: GET
        status: 500
        url: https://httpstat.us/500
    - response:
        auto_calculate_content_length: false
        body: 202 Accepted
        content_type: text/plain
        method: GET
        status: 202
        url: https://httpstat.us/202

Si estás en el REPL, también puedes activar el grabador para todas las responses
siguientes:

.. code-block:: python

    import requests
    from responses import _recorder

    _recorder.recorder.start()

    requests.get("https://httpstat.us/500")

    _recorder.recorder.dump_to_file("out.yaml")

    # puedes detener o reiniciar el grabador
    _recorder.recorder.stop()
    _recorder.recorder.reset()

Reproducir Responses (poblar el registro) desde Archivos
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Puedes poblar tu registro activo desde un archivo ``yaml`` con responses grabadas.
(Consulta `Grabar Responses en Archivos`_ para entender cómo obtener el archivo.)
Para ello necesitas ejecutar ``responses._add_from_file(file_path="out.yaml")`` dentro
de un decorador activado o un context manager.

El siguiente ejemplo registra una respuesta ``patch``, luego todas las responses
presentes en el archivo ``out.yaml`` y finalmente una respuesta ``post``.

.. code-block:: python

    import responses


    @responses.activate
    def run():
        responses.patch("http://httpbin.org")
        responses._add_from_file(file_path="out.yaml")
        responses.post("http://httpbin.org/form")


    run()


Contribuir
-----------

Configuración del Entorno
^^^^^^^^^^^^^^^^^^^^^^^^^^

Responses usa varias utilidades de linting y autoformateo, por lo que es importante
que al enviar parches utilices la cadena de herramientas adecuada:

Clona el repositorio:

.. code-block:: shell

    git clone https://github.com/getsentry/responses.git

Crea un entorno (por ejemplo con ``virtualenv``):

.. code-block:: shell

    virtualenv .env && source .env/bin/activate

Configura los requisitos de desarrollo:

.. code-block:: shell

    make develop


Pruebas y Validación de Calidad del Código
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

La forma más sencilla de validar tu código es ejecutar las pruebas mediante ``tox``.
La configuración actual de ``tox`` ejecuta las mismas verificaciones que se usan en
el pipeline de CI/CD de GitHub Actions.

Ejecuta el siguiente comando desde la raíz del proyecto para validar tu código:

* Pruebas unitarias en todas las versiones de Python admitidas por este proyecto
* Validación de tipos mediante ``mypy``
* Todos los hooks de ``pre-commit``

.. code-block:: shell

    tox

También puedes ejecutar una sola prueba en cualquier momento. Consulta la documentación
a continuación.

Pruebas Unitarias
"""""""""""""""""

Responses usa `Pytest <https://docs.pytest.org/en/latest/>`_ para las pruebas.
Puedes ejecutar todas las pruebas con:

.. code-block:: shell

    tox -e py37
    tox -e py310

O activando manualmente la versión de Python requerida y ejecutando:

.. code-block:: shell

    pytest

Y ejecutar una sola prueba con:

.. code-block:: shell

    pytest -k '<test_function_name>'

Validación de Tipos
""""""""""""""""""""

Para verificar el cumplimiento de ``type``, ejecuta el linter
`mypy <https://github.com/python/mypy>`_:

.. code-block:: shell

    tox -e mypy

O bien:

.. code-block:: shell

    mypy --config-file=./mypy.ini -p responses

Calidad y Estilo del Código
"""""""""""""""""""""""""""""

Para verificar y reformatear el estilo del código, ejecuta:

.. code-block:: shell

    tox -e precom

O bien:

.. code-block:: shell

    pre-commit run --all-files
