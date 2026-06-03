Wrap up
=======

You have walked through both sides of HTTP from the camera:

* **The motivation** -- HTTP is universal. Every platform has a
  client; every cloud service has an HTTP API; every browser
  speaks it natively. Speaking HTTP makes the camera reachable
  by anything else on the network without custom integrations.

* **Client and server roles** -- the client picks the URL,
  initiates the connection, and reads the response; the server
  binds to a port, accepts whatever shows up, and answers each
  request. A single device can play both roles concurrently.

* **The client (requests)** -- :mod:`requests` covers
  :func:`~requests.get` / :func:`~requests.post` /
  :func:`~requests.put` / :func:`~requests.patch` /
  :func:`~requests.delete` / :func:`~requests.head`, with
  optional ``json=``, ``data=``, ``files=``, ``headers=``, and
  ``auth=``. The response is a small :class:`~requests.Response`
  with ``status_code``, ``reason``, ``headers``, ``content``, and
  ``json()``. HTTPS works out of the box (encryption only by
  default; see :doc:`/openmvcam/tutorial/production/tls/index`
  for verified HTTPS). The module is synchronous and reaches for
  :mod:`socket` underneath.

* **The server (microdot)** -- one :class:`~microdot.Microdot`
  instance, route decorators, :class:`~microdot.Request` and
  :class:`~microdot.Response` objects, and an
  :mod:`asyncio`-driven event loop. ``app.run()`` for a
  standalone server; ``app.start_server()`` to share the loop
  with other tasks (a capture loop, an aioble peripheral, a
  background uploader).

* **Routing** -- ``@app.get`` / ``@app.post`` / ``@app.put`` /
  ``@app.patch`` / ``@app.delete``, dynamic path segments
  (``<int:id>``, ``<path:rest>``), before / after / error hooks,
  ``mount()`` for splitting an app across modules.

* **Request and Response** -- handlers read query strings
  (``request.args``), JSON (``request.json``), forms
  (``request.form``), uploaded files (``request.files`` via
  :func:`microdot.multipart.with_form_data`), and cookies
  (``request.cookies``). They return strings, dicts (JSON),
  tuples ``(body, status, headers)``,
  :class:`~microdot.Response` objects (custom cookies / headers),
  or :meth:`Response.send_file <microdot.Response.send_file>` for
  files.

* **Serving frames** -- the ``AsyncCSI`` wrapper from
  :doc:`/openmvcam/tutorial/asyncio/capstone/snapshot-loop` plus
  :meth:`image.Image.compress` plus a class-based async iterator
  (``__aiter__`` / ``__anext__`` -- MicroPython's asyncio cannot
  use async-generator functions) build an MJPEG live feed in
  about twenty lines. A shared capture-loop / per-client-stream
  pattern fans the same frames out to several connected viewers
  without duplicating sensor work.

* **Push channels** -- :mod:`microdot.sse` for server-to-client
  streams (sensor readings, detections, status); :mod:`microdot.websocket`
  for full-duplex (commands, chat-style protocols). Both
  integrate with asyncio and have one-line browser-side APIs
  (``EventSource``, ``WebSocket``).

* **Authentication** -- :class:`microdot.auth.BasicAuth` for the
  browser-prompt flow on closed networks;
  :class:`microdot.auth.TokenAuth` for API bearer tokens (often
  JWTs from :mod:`jwt`); :mod:`microdot.session` /
  :mod:`microdot.login` for a cookie-backed login flow with
  optional "remember me". Each route gates with a decorator;
  ``request.g.current_user`` holds the authenticated user inside
  the handler.

* **Security layers** -- :mod:`ssl` wraps the server in HTTPS the
  same way it wraps a client socket; :class:`microdot.cors.CORS`
  controls which browser origins may call the API;
  :class:`microdot.csrf.CSRF` rejects cross-site state-changing
  requests. The recommended baseline for a browser-facing app
  is HTTPS + Session + CORS + CSRF -- four lines of setup, one
  per concern.

That is enough to write camera applications that publish a live
preview to a phone, expose JSON APIs to companion devices, upload
images and telemetry to cloud services, sign requests with bearer
tokens, run a multi-user dashboard with login / logout, and run
all of it concurrently with the rest of the camera's work.

Using this reference later
--------------------------

Treat the web-server chapters as reference material; coming back
for the exact shape of a route decorator, the names of the
``Session`` constructor arguments, or the MJPEG iterator-class
pattern is the intended use. The :doc:`/library/microdot`,
:doc:`/library/microdot.auth`, :doc:`/library/microdot.cors`,
:doc:`/library/microdot.csrf`, :doc:`/library/microdot.login`,
:doc:`/library/microdot.multipart`,
:doc:`/library/microdot.session`, :doc:`/library/microdot.sse`,
:doc:`/library/microdot.websocket`, :doc:`/library/jwt`, and
:doc:`/library/omv.requests` reference pages list every method,
flag, and constant in one place when the question is just "what
is the exact name of this call".
