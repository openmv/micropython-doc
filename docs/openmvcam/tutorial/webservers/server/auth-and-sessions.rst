Authentication and sessions
===========================

By default every route the application registers is reachable by
anyone on the same network. For most real deployments that is
wrong -- the camera's control panel should only be available to
the user who owns it, the upload endpoint should only accept
posts from authenticated devices, the relay-toggle route should
require a password.

Microdot ships three building blocks for this, each suited to a
different kind of client:

* **HTTP Basic auth** -- the browser pops a username / password
  dialog. Suitable for a tiny admin interface on a closed network.
* **Token auth** -- the client sends a bearer token (often a
  JWT) in the ``Authorization`` header. The right answer for
  service-to-service APIs and SPAs that hold a token in memory.
* **Sessions and login** -- a signed cookie carries the user-id;
  routes are gated by a decorator that redirects unauthenticated
  visitors to a login page. The right answer for a multi-page web
  app on the camera.

All three set ``request.g.current_user`` to whatever the
authentication callback returned, so the rest of the handler can
inspect it without re-deriving the user from headers each time.

HTTP Basic auth
---------------

The browser handles the prompt. The camera registers a
:class:`microdot.auth.BasicAuth` instance with a callback that
validates the credentials::

    from microdot import Microdot
    from microdot.auth import BasicAuth

    app = Microdot()
    auth = BasicAuth(realm='Camera control')

    USERS = {'admin': 'open-sesame'}              # never ship this hardcoded

    @auth.authenticate
    async def check(request, username, password):
        if USERS.get(username) == password:
            return username                       # returned to request.g.current_user

    @app.get('/admin')
    @auth
    async def admin(request):
        return 'hello ' + request.g.current_user

    app.run()

The first unauthenticated request to ``/admin`` returns ``401`` with
``WWW-Authenticate: Basic realm="Camera control"``. The browser pops
its credential dialog, retries with ``Authorization: Basic
<base64(user:pass)>``, and the callback approves or rejects.

For routes that should run with or without auth (a public landing
page that shows extra controls when logged in), use
:meth:`~microdot.auth.BaseAuth.optional` instead of the bare
decorator::

    @app.get('/')
    @auth.optional
    async def index(request):
        user = request.g.current_user           # might be None
        return render(user)

Basic auth has two weaknesses worth knowing about:

* The credentials travel as Base64 on every request. **Always pair
  it with HTTPS** (see :doc:`security`); over plain HTTP the
  password is one packet capture away.
* The browser's session is the browser's tab. There is no
  "logout" button -- only closing the browser ends the session.

Token auth
----------

For API clients (a phone app, a companion microcontroller, a
cloud worker), bearer tokens are the standard. The client sends
``Authorization: Bearer <token>`` on every request; the camera
verifies the token and serves the response::

    from microdot import Microdot
    from microdot.auth import TokenAuth
    import jwt

    SECRET = load_secret()                       # e.g. from /flash/secret.bin

    app = Microdot()
    tokens = TokenAuth()

    @tokens.authenticate
    async def check(request, token):
        try:
            claims = jwt.decode(token, SECRET)
        except jwt.exceptions.PyJWTError:
            return None
        return claims['sub']                     # the user id

    @app.get('/api/status')
    @tokens
    async def status(request):
        return {'user': request.g.current_user, 'ok': True}

The ``token`` argument to the callback is whatever followed
``Bearer`` in the header. The callback returns a user object (the
JWT subject, in this example) on success or ``None`` on failure.
The decoded JWT itself is on the application to validate -- the
:mod:`jwt` library checks the signature and the ``exp`` claim, but
issuer, audience, scope, and any custom claims are the
application's responsibility.

To customize the error response (return JSON instead of an empty
401, log the rejection, ...) register an error handler::

    @tokens.errorhandler
    async def on_failure(request):
        return {'error': 'auth required'}, 401

Issuing tokens is a route the camera exposes as well -- typically
``POST /login`` that takes credentials and returns a freshly
minted JWT::

    import time

    @app.post('/login')
    async def login(request):
        creds = request.json
        if creds['user'] not in USERS or creds['pass'] != USERS[creds['user']]:
            return {'error': 'bad credentials'}, 401
        token = jwt.encode({
            'sub': creds['user'],
            'exp': int(time.time()) + 3600,      # 1 hour
        }, SECRET)
        return {'token': token}

The :mod:`jwt` reference page is at :doc:`/library/jwt`.

.. note::

   The camera's clock must be set for ``exp``-based expiry to work
   meaningfully. Call :func:`ntptime.settime` at startup -- see
   :doc:`/openmvcam/tutorial/networking/names/ntp`.

Sessions and login
------------------

For a browser-facing app that wants the "form post, redirect,
authenticated session" flow (rather than an API token), microdot
provides the :mod:`microdot.session` / :mod:`microdot.login` pair.
Sessions are signed cookies (JWTs) the camera trusts because it
signed them; login decorators redirect unauthenticated visitors
to a configurable login URL.

A minimal flow::

    from microdot import Microdot, Response, redirect
    from microdot.session import Session
    from microdot.login import Login

    SECRET = load_secret()

    app = Microdot()
    Session(app, secret_key=SECRET,
            cookie_options={'http_only': True, 'secure': True})

    login = Login()

    USERS = {'admin': {'id': 'admin', 'password_hash': '...'}}

    @login.user_loader
    async def load_user(user_id):
        return USERS.get(user_id)

    @app.get('/login')
    async def login_form(request):
        return Response.send_file('/static/login.html')

    @app.post('/login')
    async def do_login(request):
        user = USERS.get(request.form.get('username'))
        if not user or not check_password(user, request.form.get('password')):
            return redirect('/login?error=1')
        return await login.login_user(request, user, remember=True)

    @app.get('/dashboard')
    @login
    async def dashboard(request):
        return 'welcome ' + request.g.current_user['id']

    @app.post('/logout')
    async def logout(request):
        await login.logout_user(request)
        return redirect('/')

    app.run()

What the pieces do:

* :class:`~microdot.session.Session` installs a ``before_request``
  hook that lazily decodes the ``session`` cookie into a
  :class:`~microdot.session.SessionDict` accessible via
  ``request.app._session.get(request)``. The cookie is signed with
  ``SECRET`` -- tampering invalidates it.
* :class:`~microdot.login.Login` builds on the session. The
  :meth:`~microdot.login.Login.login_user` call stores the user-id
  in the session and returns a redirect.
* The ``@login`` decorator on a route checks the session for a
  logged-in user and redirects unauthenticated visitors to
  ``/login`` with ``?next=<original-url>``.
* :meth:`~microdot.login.Login.logout_user` clears the session
  and any ``_remember`` cookie.

The ``remember=True`` argument on :meth:`~Login.login_user` sets a
long-lived ``_remember`` cookie (default 30 days) that
re-authenticates returning visitors automatically. Mark routes
that should require a fresh login (password change, account
deletion) with :meth:`@login.fresh <microdot.login.Login.fresh>`
instead of the bare ``@login`` decorator -- "remember me" sessions
are rejected on those.

Where the secret lives
----------------------

All three approaches share one practical concern: the secret
material (the user-password table, the JWT signing key, the
session signing key) lives on the camera and is read at startup.
The patterns:

* **Never embed the secret in source.** Read it from a file on
  the FAT filesystem (``/sdcard/secret.bin`` or
  ``/flash/secret.bin``), or bake it into the ROMFS image at
  flash time.
* **Use a different secret per device** when the same firmware
  ships on more than one cam. A leak from one device should not
  let an attacker forge sessions on another.
* **Treat any file on the cam's flash as recoverable** -- USB
  mass-storage, a REPL prompt, or raw flash readout all expose
  them. For deployments where this matters, the camera's
  certificate-based identity (see
  :doc:`/openmvcam/tutorial/production/tls/index`) is the
  better long-term answer; the secret-file pattern is fine for
  closed-network applications where the threat model does not
  include physical access.

The next page covers the operational layer underneath
authentication -- HTTPS for transport, CORS for browser-side
access policy, CSRF for protecting state-changing requests from
hostile origins.
