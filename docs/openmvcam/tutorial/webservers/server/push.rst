Push channels -- SSE and WebSockets
===================================

The MJPEG stream from :doc:`serving-frames` is one shape of "the
server keeps pushing": one connection, one infinite response,
binary frames separated by a boundary. For *other* data the camera
wants to push to a connected client -- sensor readings, detection
events, log lines, status updates -- there are two cleaner options
in microdot: **Server-Sent Events (SSE)** and **WebSockets**.

The two patterns at a glance
----------------------------

* **SSE** is server-to-client only. The client opens an HTTP
  request to ``Content-Type: text/event-stream``; the server keeps
  the connection open and writes formatted text events as they
  happen. The browser exposes the stream as a JavaScript
  ``EventSource``. Auto-reconnect, last-event-id replay, and the
  framing format are part of the spec -- the camera just calls
  ``await sse.send(...)``.

* **WebSockets** are full duplex. After an HTTP upgrade handshake,
  the same TCP connection carries arbitrary framed messages in
  both directions. The camera sends and receives on the same
  socket; the client sees a JavaScript ``WebSocket`` with
  ``onmessage`` / ``send()``.

The trade-off:

* If the client only listens, use **SSE**. Simpler protocol, no
  upgrade dance, automatic reconnect, plays nicely with HTTP
  proxies.
* If the client also needs to send asynchronous messages back
  (typing into a chat, sending commands), use **WebSockets**.

Server-Sent Events
------------------

A handler decorated with :func:`microdot.sse.with_sse` receives
the request and an :class:`microdot.sse.SSE` object. Each
``await sse.send(...)`` pushes one event::

    from microdot import Microdot
    from microdot.sse import with_sse
    import asyncio

    app = Microdot()

    @app.get('/events')
    @with_sse
    async def events(request, sse):
        while True:
            reading = read_sensor()
            await sse.send({'temperature': reading}, event='reading')
            await asyncio.sleep(1)

    app.run(host='0.0.0.0', port=80)

The browser side is two lines of JavaScript:

.. code-block:: javascript

    const stream = new EventSource('/events');
    stream.addEventListener('reading', e => {
        const data = JSON.parse(e.data);
        document.getElementById('temp').textContent = data.temperature;
    });

What the camera sends per :meth:`sse.send <microdot.sse.SSE.send>`:

* *data* -- the payload. ``str`` / ``bytes`` pass through;
  ``dict`` and ``list`` are JSON-encoded; anything else is
  ``str()``-ified.
* *event* -- optional event name. The browser dispatches to
  listeners registered for that name; without an event name the
  message arrives on the default ``message`` event.
* *event_id* -- optional id. The browser sends it back as
  ``Last-Event-ID`` after a reconnect so the server can resume.
* *retry* -- optional reconnect delay (seconds) the browser
  should use if the connection drops.
* *comment=True* -- send the payload as an SSE comment line
  (ignored by the browser). Useful as a keep-alive heartbeat to
  stop NAT timeouts from closing an idle stream.

The handler's lifetime equals the stream's lifetime. A client
disconnect raises :exc:`asyncio.CancelledError`, which microdot
catches; clean-up code goes in a ``try``/``finally`` block::

    @app.get('/events')
    @with_sse
    async def events(request, sse):
        subscribe()
        try:
            while True:
                event = await wait_for_event()
                await sse.send(event)
        finally:
            unsubscribe()

For SSE that should require auth, wrap the handler the way you
would any other route -- the SSE decorator composes with auth
decorators::

    @app.get('/events')
    @token_auth
    @with_sse
    async def events(request, sse):
        # only reached after token_auth approved the request
        ...

WebSockets
----------

A handler decorated with :func:`microdot.websocket.with_websocket`
receives the request and a :class:`~microdot.websocket.WebSocket`.
Use :meth:`~microdot.websocket.WebSocket.receive` to read,
:meth:`~microdot.websocket.WebSocket.send` to write -- both
``await``::

    from microdot import Microdot
    from microdot.websocket import with_websocket, WebSocketError

    app = Microdot()

    @app.get('/echo')
    @with_websocket
    async def echo(request, ws):
        while True:
            try:
                msg = await ws.receive()
            except WebSocketError:
                break                          # client closed
            await ws.send(msg)

The browser side, again two lines of JavaScript:

.. code-block:: javascript

    const ws = new WebSocket('ws://kitchen-cam.local/echo');
    ws.onmessage = e => console.log('got:', e.data);
    ws.send('hello');

Messages can be strings or bytes. Microdot picks the right
WebSocket opcode (``TEXT`` for strings, ``BINARY`` for bytes) based
on the type of the argument; pass an explicit ``opcode=`` to
override.

Closing happens three ways:

* The handler returns or raises -- microdot sends a clean close
  frame.
* The client closes -- :meth:`~WebSocket.receive` raises
  :exc:`~microdot.websocket.WebSocketError`. Catch it to break out
  of the loop cleanly.
* The TCP connection drops outright -- :meth:`~WebSocket.receive`
  raises :exc:`OSError`.

A bidirectional chat / command-and-control loop::

    @app.get('/control')
    @with_websocket
    async def control(request, ws):
        try:
            while True:
                cmd = await ws.receive()
                result = execute_command(cmd)
                await ws.send({'result': result})
        except (WebSocketError, OSError):
            pass

For conditional upgrades (authenticate first, then upgrade), use
:func:`microdot.websocket.websocket_upgrade` directly::

    from microdot import Response, abort
    from microdot.websocket import websocket_upgrade

    @app.get('/private')
    async def private(request):
        if not authenticate(request):
            abort(401)
        ws = await websocket_upgrade(request)
        # ... use ws.receive() / ws.send() ...
        return Response.already_handled

Returning :attr:`Response.already_handled
<microdot.Response.already_handled>` tells microdot the socket has
been taken over already and there is nothing more to send.

Memory and message size
-----------------------

Both SSE and WebSockets buffer the in-flight message before
writing. The default per-message limit on WebSockets is
:attr:`Request.max_body_length <microdot.Request.max_body_length>`
(16 KB). Raise it on the class for larger messages::

    from microdot.websocket import WebSocket
    WebSocket.max_message_length = 64 * 1024        # 64 KB

Larger again -- live video, bulk file transfer -- belongs in a
multipart MJPEG stream (:doc:`serving-frames`) or a custom binary
protocol over a raw TCP socket from the networking section.

Both push channels share the asyncio cooperation contract -- a
handler that wants to push events at high rates needs to
``await`` periodically (``asyncio.sleep_ms(0)``) so other tasks
(the capture loop, other clients) get scheduling slots. The
asyncio chapter (:doc:`/openmvcam/tutorial/asyncio/index`) covers
the cooperation model in detail.

With routing, request/response, frame serving, and push channels
in hand, the next chapter covers who is allowed to do all this --
authentication, sessions, and the login flow.
