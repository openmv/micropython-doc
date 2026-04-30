:mod:`utelnet` --- Telnet server
================================

.. module:: utelnet
   :synopsis: Small background Telnet server with REPL duplication.

The ``utelnet`` module implements a small Telnet server that runs in
the background using socket callbacks. When a client connects, its
socket is attached to the MicroPython REPL via ``os.dupterm`` so the
remote end can interact with the interactive prompt over Telnet.

Only a single concurrent client is supported; connecting a new client
disconnects the previous one. Incoming Telnet IAC control sequences
and embedded null bytes are stripped from the input stream.

Example usage::

    import utelnet
    utelnet.start()
    # ...
    utelnet.stop()


Functions
---------

.. function:: start(port: int = 23) -> None

   Start the Telnet server.

   Calls :func:`stop` first to tear down any previous server, then
   binds a listening socket on the given ``port`` and registers an
   accept callback that attaches new clients to the REPL via
   ``os.dupterm``. On accept, Telnet option negotiation bytes are sent
   to disable line mode and remote echo. A banner with the listening
   address and port is printed for each active ``network.AP_IF`` and
   ``network.STA_IF`` interface.

   Arguments:

   - ``port`` -- TCP port to listen on for Telnet connections.
     Defaults to ``23``.

.. function:: stop() -> None

   Stop the Telnet server.

   Detaches the REPL by calling ``os.dupterm(None)`` and closes both
   the listening server socket and the currently connected client
   socket, if any.

.. function:: accept_telnet_connect(telnet_server: socket) -> None

   Accept callback installed on the listening socket.

   Accepts the next pending connection on ``telnet_server``, closes
   any previously connected client, sets the new client socket
   non-blocking, sends the Telnet IAC sequences to disable line mode
   and local echo, and attaches the client to the REPL by passing a
   :class:`TelnetWrapper` to ``os.dupterm``.

   Arguments:

   - ``telnet_server`` -- The listening server socket on which to
     ``accept()`` the incoming connection.


Classes
-------

.. class:: TelnetWrapper(socket: socket)

   ``IOBase`` adapter that wraps a Telnet client socket so it can be
   used as a ``dupterm`` stream.

   The wrapper transparently strips Telnet IAC (``0xFF``) command
   sequences and null bytes from the input stream, and writes data
   back to the socket while tolerating ``EAGAIN`` on the non-blocking
   socket.

   Arguments:

   - ``socket`` -- The connected client socket to wrap. Must be set
     to non-blocking mode before reads.

   .. method:: readinto(b: bytearray) -> int | None

      Read available bytes into the buffer ``b``, discarding Telnet
      control characters and null bytes. Returns the number of bytes
      written into ``b``, or ``None`` if no data is currently
      available.

   .. method:: write(data: bytes) -> None

      Write all of ``data`` to the underlying socket, retrying on
      ``EAGAIN`` until the entire buffer has been sent.

   .. method:: close() -> None

      Close the underlying client socket.


Module variables
----------------

.. data:: server_socket
   :type: socket | None

   The listening server socket, or ``None`` when the server is
   stopped. Set by :func:`start` and cleared by :func:`stop`.

.. data:: last_client_socket
   :type: socket | None

   The most recently accepted client socket, or ``None`` if no client
   is currently connected. Used by :func:`stop` and
   :func:`accept_telnet_connect` to close a previous client before a
   new one is attached.
