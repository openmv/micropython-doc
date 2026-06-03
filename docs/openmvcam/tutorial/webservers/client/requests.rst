The requests module
===================

The camera's HTTP client is the :mod:`requests` module -- a small,
synchronous library modelled on the CPython ``requests`` package. It
covers the everyday cases: ``GET`` and ``POST`` to an HTTP or HTTPS
URL, JSON in and out, file uploads, custom headers, basic
authentication. Each call returns a small :class:`Response` object
the application reads from.

The two ways to call
--------------------

Every call boils down to one of two forms.

The convenience helpers -- :func:`requests.get`,
:func:`requests.post`, :func:`requests.put`, :func:`requests.patch`,
:func:`requests.delete`, :func:`requests.head` -- match the HTTP
method to the function name::

    import requests

    r = requests.get("https://httpbin.org/get")
    print(r.status_code, r.reason)

The generic :func:`requests.request` lets the application pass the
method as a string -- useful when the method is data, not code::

    method = decide_method(...)
    r = requests.request(method, "https://httpbin.org/anything")

Both forms share the same keyword arguments: ``data``, ``json``,
``files``, ``headers``, ``auth``, ``stream``. The helpers are the
common path; the rest of this page uses them.

What you get back
-----------------

Every call returns a :class:`requests.Response` with four useful
attributes::

    r = requests.get("https://api.example.com/sensors/12")

    r.status_code              # int  -- 200, 404, 500, ...
    r.reason                   # str  -- "OK", "Not Found", ...
    r.headers                  # str  -- raw response headers
    r.content                  # str  -- response body (decoded utf-8)

For JSON responses, :meth:`requests.Response.json` parses the body
into a Python object in one call::

    payload = r.json()
    print(payload["sensor_id"], payload["value"])

The status-code check is the application's responsibility -- a 404
or 500 still returns normally. The convention is to branch on the
class of the status:

* ``2xx`` -- success.
* ``3xx`` -- redirect. The MicroPython port does **not** follow
  redirects automatically -- a 3xx response just comes back as-is.
* ``4xx`` -- client error (bad URL, missing auth, bad payload).
* ``5xx`` -- server error.

A robust client checks the code before doing anything with the
body::

    r = requests.get(url)
    if r.status_code != 200:
        print("server said", r.status_code, r.reason)
        return
    process(r.json())

The four common patterns
------------------------

Most camera-as-client code is one of these four shapes.

**GET a JSON resource.**

::

    r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                     headers={"X-API-Key": API_KEY})
    if r.status_code == 200:
        data = r.json()
        print("temperature:", data["main"]["temp"])

The query string can be appended to the URL directly, or the
application can build it once and reuse it.

**POST JSON.**

::

    payload = {
        "device_id": "kitchen-cam",
        "reading_c": read_temperature(),
        "ts": time.time(),
    }

    r = requests.post("https://api.example.com/telemetry", json=payload)
    if r.status_code >= 400:
        print("upload failed:", r.status_code, r.reason)

``json=`` serializes the Python object as JSON and sets
``Content-Type: application/json`` automatically. To send a body
that is already encoded -- raw bytes, a pre-formatted string -- use
``data=`` instead and supply the ``Content-Type`` header yourself.

**Upload a file.**

The ``files`` argument takes a dict mapping field name to
``(filename, fileobj)`` and posts the request as
``multipart/form-data``::

    img = csi0.snapshot()
    img.save("/tmp/snap.jpg")

    with open("/tmp/snap.jpg", "rb") as f:
        r = requests.post(
            "https://api.example.com/uploads",
            files={"image": ("snap.jpg", f)},
            headers={"X-Camera": "kitchen-cam"},
        )

    print("upload status:", r.status_code)

For images from the camera, write the JPEG bytes to a file first
(or wrap them in :class:`io.BytesIO` if the platform supports it),
since the file object is read with ``read()``.

**Authenticated GET.**

The ``auth=(username, password)`` argument adds an HTTP Basic
``Authorization`` header::

    r = requests.get("https://camera-gateway.local/admin/status",
                     auth=("admin", load_password()))

For bearer-token APIs (the more common case for modern services),
set the header explicitly::

    r = requests.get("https://api.example.com/me",
                     headers={"Authorization": "Bearer " + token})

JSON in, JSON out
-----------------

JSON is the default body format for modern HTTP APIs. The camera-side
shape:

* **Sending**: pass a Python object to ``json=`` and let the library
  serialize it.
* **Receiving**: call :meth:`requests.Response.json` on the response
  to parse the body.

A round-trip in one snippet::

    payload = {"event": "motion", "ts": time.time()}
    r = requests.post("https://api.example.com/events", json=payload)
    confirmation = r.json()                # the server's response, parsed
    print("server acknowledged id", confirmation["id"])

Both ends use ``application/json`` as the ``Content-Type``. If the
server returns something other than JSON (an HTML error page on a
5xx, say), :meth:`requests.Response.json` raises ``ValueError`` --
guard the call when the success case is not guaranteed.

HTTPS works out of the box
--------------------------

The module dispatches on the URL scheme. ``http://`` opens a plain
TCP socket to port 80; ``https://`` wraps the same socket in TLS
and uses port 443. No additional setup needed::

    r = requests.get("https://api.example.com/things")

The TLS layer is the same one covered in
:doc:`/openmvcam/tutorial/networking/encrypted-sockets`. The camera
ships with no certificate authority store by default, so the
connection is encrypted but the server's certificate is *not*
verified -- a man-in-the-middle could substitute their own
certificate and the connection would still succeed.
For production deployments that must verify the server, see
:doc:`/openmvcam/tutorial/production/tls/operations`.

Timeouts and failure modes
--------------------------

The underlying socket has a fixed 5-second timeout. A request that
takes longer raises :exc:`OSError`. The other things that raise:

* The host is unresolvable (no network, DNS failure) -- ``OSError``.
* The host refuses the connection (server down, firewall) --
  ``OSError``.
* The TLS handshake fails (wrong port, certificate problem, server
  rejected the client) -- ``OSError``.

Wrap the call in ``try`` / ``except`` for anything that should
survive a network glitch::

    try:
        r = requests.get(url)
    except OSError as exc:
        print("request failed:", exc)
        return None
    return r.json()

The library does **not** retry on transient errors -- the application
loops if it wants to.

What the module does not do
---------------------------

For features the MicroPython port intentionally omits, fall back to
the :mod:`socket` API or pre-process the data before calling:

* **Redirect following.** A 3xx response is returned as-is; the
  ``Location`` header is in ``r.headers`` if the application wants to
  re-request manually.
* **Chunked transfer encoding (response).** A server that streams a
  chunked body raises ``ValueError("Unsupported Transfer-Encoding:
  chunked")``. Switch to plain ``Content-Length`` responses on the
  server, or read the socket directly.
* **Session reuse / connection pooling.** Every request opens a new
  socket. For high-rate clients, this is the bottleneck -- consider
  batching, or reach for the lower-level :mod:`socket` API and reuse
  one connection.
* **Streaming response bodies.** The ``stream=`` argument is
  accepted for API parity but the response body is fully read into
  memory before :class:`Response` is returned. For large downloads,
  drop to the :mod:`socket` layer.

For everything inside that envelope -- the everyday GET/POST work --
the :mod:`requests` API matches CPython's closely enough that
examples from the wider Python ecosystem translate directly.
