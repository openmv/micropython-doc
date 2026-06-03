Security: HTTPS, CORS, CSRF
===========================

Three operational layers sit between an authenticated handler and
a hostile network. HTTPS encrypts and authenticates the connection;
CORS controls which origins a browser will let touch the API;
CSRF protection rejects state-changing requests that come from
sites the user did not intend to interact with.

HTTPS
-----

The encryption layer the networking section already covered
(:doc:`/openmvcam/tutorial/networking/encrypted-sockets`) is the
same one microdot uses. Pass an :class:`ssl.SSLContext` to
:meth:`Microdot.run <microdot.Microdot.run>` or
:meth:`~microdot.Microdot.start_server`; every accepted connection
gets the TLS wrap before the framework reads from it::

    import ssl
    from microdot import Microdot

    app = Microdot()

    # ... routes ...

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain('/flash/cert.der', '/flash/key.der')

    app.run(host='0.0.0.0', port=443, ssl=ctx)

For the certificate workflow -- generating a self-signed pair for
development, getting CA-signed certificates for production, the
DER format the camera accepts, the per-device key constraints --
see :doc:`/openmvcam/tutorial/production/tls/index`.

A few practical notes for HTTPS on a server:

* Port 443 needs root on a desktop, but the camera has no concept
  of an unprivileged user. Pick port 443 (the browser default for
  HTTPS), or a high port that the firewall maps to 443 externally.
* Browsers warn loudly on self-signed certs. For an internal-only
  service this is tolerable; for anything end-users touch, get a
  proper CA-issued cert.
* Mixed HTTP/HTTPS is a footgun -- if any page uses ``http://``
  the cookies are exposed in transit. Either serve everything
  HTTPS, or only HTTP (on a closed network).

Setting the ``secure`` flag on session cookies (covered on
:doc:`auth-and-sessions`) tells the browser to send them only
over HTTPS. Always set it on HTTPS deployments.

CORS
----

By default, JavaScript running on ``https://app.example.com``
cannot read responses from ``http://kitchen-cam.local/api``. This
is the **same-origin policy** -- the browser refuses to let a page
mix data from one origin with the JavaScript of another, to stop
malicious sites from quietly hitting your camera's API on behalf
of the logged-in user. CORS is the opt-in: the camera tells the
browser which origins are allowed.

The :class:`microdot.cors.CORS` class installs itself onto the
app::

    from microdot import Microdot
    from microdot.cors import CORS

    app = Microdot()
    CORS(app,
         allowed_origins=['https://dashboard.example.com'],
         allow_credentials=True,
         max_age=86400)

    @app.get('/api/status')
    async def status(request):
        return {'ok': True}

What the arguments do:

* ``allowed_origins`` -- a list of origin URLs, or the literal
  ``'*'`` for "any origin". Origins that do not match get no
  CORS headers, and the browser treats the response as a
  security failure.
* ``allow_credentials`` -- send cookies and auth headers with
  cross-origin requests. Cannot be combined with
  ``allowed_origins='*'`` for credential-bearing requests (the
  browser rejects that combination).
* ``allowed_methods`` -- restrict which HTTP methods are
  allowed cross-origin. ``None`` means any.
* ``allowed_headers`` -- restrict which request headers may be
  sent. ``None`` echoes whatever the preflight asked for.
* ``max_age`` -- seconds the browser may cache the preflight
  result. Skipping it means a preflight on every request,
  which can dominate the API's latency profile.

CORS only constrains *browser* JavaScript. A request from
``curl``, a Python script, or the camera's own
:mod:`requests` module bypasses CORS entirely -- the browser
is what enforces the policy, and other clients have no
browser. CORS is not an authentication mechanism; it is a
*defense for end-users* against malicious websites probing
APIs the user happens to be authenticated to.

CSRF
----

Cross-Site Request Forgery is the attack CORS does not stop: a
malicious page ``https://evil.example.com`` makes the user's
browser submit a state-changing request (a ``POST`` form, an
``<img src="http://kitchen-cam.local/relay?on=1">``) to the
camera, and the camera does it because the browser dutifully sent
the user's session cookie along.

Modern browsers include a ``Sec-Fetch-Site`` header on every
request that lets the server tell same-site requests from
cross-site ones. The :class:`microdot.csrf.CSRF` class wires a
``before_request`` hook that rejects any non-safe method
(``POST``, ``PUT``, ``PATCH``, ``DELETE``) whose
``Sec-Fetch-Site`` indicates a cross-site request::

    from microdot import Microdot
    from microdot.cors import CORS
    from microdot.csrf import CSRF

    app = Microdot()
    cors = CORS(app, allowed_origins=['https://app.example.com'])
    csrf = CSRF(app, cors=cors)

    @app.post('/api/save')
    async def save(request):
        # automatically CSRF-protected -- cross-site POSTs are rejected
        return {'ok': True}

The ``cors`` argument is the fallback for browsers that do not
send ``Sec-Fetch-Site``: the CSRF check then validates the
``Origin`` header against the CORS allow-list.

Two decorators on the :class:`~microdot.csrf.CSRF` instance let
the application override the default protection:

* ``@csrf.exempt`` -- opts a route out of CSRF protection. Useful
  for webhook endpoints that legitimately accept cross-site
  ``POST``\ s (e.g. a Stripe webhook with its own signing).
* ``@csrf.protect`` -- opts a route in even when it would
  normally be exempt (a ``GET`` that has side effects, say).

Setting ``protect_all=False`` on the constructor flips the
default -- no routes are protected unless explicitly opted in
via ``@csrf.protect``. The default ``protect_all=True`` is the
safer choice for browser-facing apps.

A standard "secure-by-default" stack
------------------------------------

For a browser-facing app on the camera the recommended baseline
is the four-line stack::

    from microdot import Microdot
    from microdot.cors import CORS
    from microdot.csrf import CSRF
    from microdot.session import Session

    app = Microdot()
    Session(app, secret_key=load_secret(),
            cookie_options={'http_only': True, 'secure': True})
    cors = CORS(app, allowed_origins=['https://app.example.com'],
                allow_credentials=True)
    CSRF(app, cors=cors)

    # ... routes, login, etc. ...

    app.run(host='0.0.0.0', port=443, ssl=load_ssl_context())

This wires up signed-cookie sessions over HTTPS, with the browser
restricted to one allowed origin and CSRF protection on every
state-changing route. Anything stricter is application-specific
(rate limits, signed webhooks, IP allow-lists); anything looser
is a deliberate choice the application designer makes.
