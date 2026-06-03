Routing
=======

A *route* is a (URL pattern, HTTP method, handler) triple. Microdot
keeps a list of every registered route on the application and, when
a request arrives, picks the first one whose pattern matches the
path and whose method list includes the request's method. Picking
routes is the application designer's main concern after the
minimal app.

The decorator family
--------------------

The :meth:`~microdot.Microdot.route` decorator registers a route
under one or more HTTP methods::

    @app.route('/items')
    async def list_items(request):
        return items

    @app.route('/items', methods=['POST'])
    async def create_item(request):
        items.append(request.json)
        return '', 201

Five thin wrappers register single-method routes:

* ``@app.get('/items')`` -- ``GET`` only.
* ``@app.post('/items')`` -- ``POST`` only.
* ``@app.put('/items/<int:id>')`` -- ``PUT`` only.
* ``@app.patch('/items/<int:id>')`` -- ``PATCH`` only.
* ``@app.delete('/items/<int:id>')`` -- ``DELETE`` only.

These read better and are the recommended form when only one method
applies. Use :meth:`~microdot.Microdot.route` with an explicit
``methods=`` list when a single handler should serve multiple
methods (or when the method list is computed).

URL patterns
------------

A pattern is a path with optional placeholders enclosed in
``<`` / ``>``. Three placeholder types come built in:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Pattern
     - Captures
     - Notes
   * - ``<name>``
     - One path segment, no ``/``
     - Default type. Passed to the handler as a string.
   * - ``<int:name>``
     - One path segment, integer
     - Parsed to ``int``. Non-numeric paths do not match.
   * - ``<path:rest>``
     - The remainder of the path, ``/`` included
     - Useful for catch-all handlers and static-file serving.
   * - ``<re:[regex]:name>``
     - Whatever the regex matches
     - Falls through to a regex group when one of the standard
       types is too loose.

Example::

    @app.get('/users/<int:user_id>/posts/<post_slug>')
    async def get_post(request, user_id, post_slug):
        # user_id is an int, post_slug is a str
        return {'user': user_id, 'post': post_slug}

Captured groups are passed to the handler as keyword arguments with
the placeholder name as the key. The request object stays the first
positional argument.

The handler always receives the request as the first positional
argument; the captured groups follow as keyword arguments
matching the placeholder names.

For a catch-all, the ``path`` type captures slashes::

    @app.get('/static/<path:filename>')
    async def static(request, filename):
        return Response.send_file('/static/' + filename)

Registering a new placeholder type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom types extend the four built-ins via
:meth:`~microdot.URLPattern.register_type`. The example registers a
``<uuid:...>`` type that matches any 36-character UUID::

    from microdot import URLPattern

    URLPattern.register_type('uuid', '[0-9a-f-]{36}')

    @app.get('/sessions/<uuid:sid>')
    async def show_session(request, sid):
        return get_session(sid)

The optional second argument to
:meth:`~microdot.URLPattern.register_type` is a callable that
converts the matched string before the handler sees it -- useful
when the captured value should reach the handler in a different
type::

    URLPattern.register_type('bigint', '[0-9]+', int)

Route order matters
-------------------

When two routes could match the same path, the handler wins which
was registered **first**. A common gotcha::

    @app.get('/items/<path:rest>')
    async def static(request, rest):
        # ...

    @app.get('/items/new')
    async def new_item(request):
        # never reached -- the path catch-all already matched

Order the specific route before the catch-all, or use a more
restrictive type::

    @app.get('/items/new')              # ← specific first
    async def new_item(request):
        # ...

    @app.get('/items/<path:rest>')      # ← catch-all last
    async def static(request, rest):
        # ...

Before / after / error hooks
----------------------------

Routes are not the only callbacks the application registers. Four
hook decorators wrap the routing pipeline:

* ``@app.before_request`` -- runs before every request. Useful for
  logging, request-level setup, or returning a response early to
  short-circuit the handler::

      @app.before_request
      async def reject_old_clients(request):
          if request.headers.get('User-Agent', '').startswith('OldApp/'):
              return 'Please update', 426     # short-circuit

* ``@app.after_request`` -- runs after every successful request. The
  handler returns ``(request, response)``; the return value
  replaces the response. Use it for response-side header injection
  (CSP, logging headers, ETags)::

      @app.after_request
      async def add_security_headers(request, response):
          response.headers['X-Content-Type-Options'] = 'nosniff'
          return response

* ``@app.after_error_request`` -- runs after Microdot generates an
  error response (404, 500, or a handler-raised exception). Same
  signature as ``after_request``; useful for shaping error pages.

* ``@app.errorhandler(code_or_exception)`` -- replaces the default
  error response for one specific status code or Python exception
  class::

      @app.errorhandler(404)
      async def not_found(request):
          return Response.send_file('/static/404.html'), 404

      @app.errorhandler(ValueError)
      async def bad_input(request, exc):
          return {'error': str(exc)}, 400

Aborting from inside a handler
------------------------------

To bail out of a handler with a specific status code, raise via
:func:`microdot.abort`::

    from microdot import abort

    @app.get('/users/<int:id>')
    async def get_user(request, id):
        user = lookup(id)
        if user is None:
            abort(404)
        return user.to_dict()

The ``abort`` call raises :exc:`microdot.HTTPException`, which
microdot catches and turns into the corresponding error response
(running ``errorhandler`` if one is registered).

Splitting an app into pieces
----------------------------

A larger app keeps related routes in their own module and uses
:meth:`~microdot.Microdot.mount` to attach them under a prefix::

    # api.py
    from microdot import Microdot

    api = Microdot()

    @api.get('/status')
    async def status(request):
        return {'ok': True}

    # main.py
    from microdot import Microdot
    from api import api

    app = Microdot()
    app.mount(api, url_prefix='/api')

    @app.get('/')
    async def index(request):
        return 'Hello'

    app.run()

The sub-app's routes appear under ``/api/status`` on the parent.
Hooks on the sub-app are merged with the parent by default; pass
``local=True`` to scope them to only the sub-app's routes.

The next page covers the :class:`~microdot.Request` and
:class:`~microdot.Response` objects in detail -- what handlers
read from one and write to the other.
