Inside a handler -- requests and responses
==========================================

The request object that microdot passes into every handler is the
parsed shape of the incoming HTTP message. The return value is the
shape of the response that microdot sends back. Everything a
handler does fits between these two ends.

Reading the request
-------------------

The handler's first positional argument is a
:class:`~microdot.Request`. The attributes worth knowing:

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Attribute
     - What it carries
   * - ``request.method``
     - ``"GET"``, ``"POST"``, ...
   * - ``request.path``
     - The path portion, with the URL prefix stripped if mounted
       (``/api/status``).
   * - ``request.args``
     - Parsed query string as a :class:`microdot.MultiDict`
       (``?tag=a&tag=b`` → ``args.getlist('tag') == ['a', 'b']``).
   * - ``request.headers``
     - Case-insensitive dict of request headers.
   * - ``request.cookies``
     - Parsed ``Cookie`` header as a plain dict.
   * - ``request.json``
     - The body parsed as JSON, or ``None`` if the content type is
       wrong. Lazy -- not evaluated until you touch it.
   * - ``request.form``
     - URL-encoded form fields as a :class:`microdot.MultiDict`, or
       ``None`` if the content type is not
       ``application/x-www-form-urlencoded``.
   * - ``request.body``
     - The raw bytes of the body. Empty when the body was too large
       to buffer; use ``request.stream`` in that case.
   * - ``request.stream``
     - An async stream over the body bytes. Use for large uploads.
   * - ``request.g``
     - A free-form container. Hooks and the handler can attach
       per-request state (``request.g.user = ...``) and read it
       later in the same request.

Three common reads:

**Query string parameters.**

::

    @app.get('/search')
    async def search(request):
        q = request.args.get('q', '')
        limit = request.args.get('limit', '20', type=int)
        return search_index(q, limit=limit)

The ``type=`` argument tells :class:`~microdot.MultiDict` to convert
the value -- ``int``, ``float``, anything callable. A conversion
failure returns the default.

**JSON body.**

::

    @app.post('/events')
    async def add_event(request):
        payload = request.json
        if payload is None or 'type' not in payload:
            abort(400, 'bad event')
        record(payload)
        return '', 201

``request.json`` returns ``None`` (rather than raising) when the
client did not set ``Content-Type: application/json``. Test for
``None`` before reaching into the dict.

**Form data.**

::

    @app.post('/login')
    async def login(request):
        username = request.form.get('username')
        password = request.form.get('password')
        # ...

For ``multipart/form-data`` requests (the encoding used by
``<input type="file">``), decorate the route with
:func:`microdot.multipart.with_form_data`; see the
:doc:`serving-frames` page for an upload example.

Building the response
---------------------

The return value of a handler is converted to a
:class:`~microdot.Response` by microdot. Five short forms cover
most cases.

* **A string** -- the body, sent as ``text/plain; charset=UTF-8``
  with a 200 status::

      return 'Hello, world!'

* **A dict or list** -- serialized as JSON with
  ``Content-Type: application/json``::

      return {'temperature': 23.5, 'unit': 'C'}

* **A tuple** -- ``(body, status_code)`` or
  ``(body, status_code, headers)``::

      return {'ok': False, 'why': 'invalid'}, 400
      return 'created', 201, {'Location': '/items/' + str(item.id)}

* **A** :class:`~microdot.Response` **directly** -- when you need
  custom headers, status codes, or cookies::

      from microdot import Response

      response = Response(body, status_code=200,
                          headers={'X-Cache': 'HIT'})
      response.set_cookie('session', token, http_only=True, secure=True)
      return response

* **A file** -- :meth:`Response.send_file
  <microdot.Response.send_file>` streams a file from the
  filesystem::

      return Response.send_file('/sdcard/snapshot.jpg')

  The ``Content-Type`` is inferred from the filename's extension.
  Pass ``max_age=`` for a ``Cache-Control: max-age`` header,
  ``compressed=True`` for an already-gzipped file.

Redirects
~~~~~~~~~

:meth:`Response.redirect <microdot.Response.redirect>` is the
shortcut for a 3xx response::

    from microdot import Response

    @app.post('/items')
    async def create(request):
        item = save(request.json)
        return Response.redirect('/items/' + str(item.id))

The default status is 302. Pass ``status_code=301`` for a
permanent redirect, ``303`` to force the next request to ``GET``.

Cookies
~~~~~~~

Set a cookie on the response::

    response = Response('logged in')
    response.set_cookie('session', token,
                        path='/', http_only=True, secure=True,
                        max_age=86400)
    return response

Delete a cookie by name::

    response.delete_cookie('session')

The :doc:`auth-and-sessions` page covers signed session cookies
where the signature stops a client from forging a session by
hand.

Status codes
~~~~~~~~~~~~

Returning a tuple is the lightest-weight way to set a non-200
status::

    return 'created', 201
    return 'not found', 404
    return '', 204

For more elaborate cases (a status code plus a structured JSON
body), construct a :class:`~microdot.Response` directly. To bail
out of a handler with an error response, raise via
:func:`microdot.abort` (covered on the :doc:`routing` page).

Streaming response bodies
-------------------------

When the body is too large to buffer -- a long log file, a
generated report, a continuous stream of frames -- pass an async
generator (or any object with ``__aiter__`` / ``__anext__``) as
the body. Microdot reads from it as the client reads from the
socket, with no intermediate buffering. The
:doc:`serving-frames` page uses this for live MJPEG.

Per-request after-handlers
--------------------------

A handler that needs to do clean-up *after* the response is
written -- closing a resource, logging the actual status code --
can register an after-handler scoped to one request::

    @app.get('/items/<int:id>')
    async def show_item(request, id):
        item = open_item(id)

        @request.after_request
        async def cleanup(req, resp):
            item.close()
            return resp

        return item.to_dict()

Per-request after-handlers run after the application-level
``after_request`` handlers and only on the success path. They are
skipped if the handler raises an exception (the application-level
``after_error_request`` runs in that case).

The next page steps off the framework's general behavior into the
camera-specific case: serving frames over HTTP.
