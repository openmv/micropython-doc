:mod:`uftpd` --- FTP server
===========================

.. module:: uftpd
   :synopsis: Small background FTP server.

The ``uftpd`` module implements a small FTP server that runs in the
background using socket callbacks. The server accepts passive and
active mode connections and exposes the device file system over FTP.

Importing the module automatically calls :func:`start` to launch the
server on port 21 on every active ``network.WLAN`` interface.

Example usage::

    import uftpd
    uftpd.stop()
    uftpd.start(port=21, verbose=1)
    # ...
    uftpd.stop()


Functions
---------

.. function:: start(port: int = 21, verbose: int = 0, splash: bool = True) -> None

   Start the FTP server.

   Binds a listening socket on the given ``port`` for every active
   ``network.AP_IF`` and ``network.STA_IF`` interface, and creates the
   shared passive-mode data socket on port 13333.

   Arguments:

   - ``port`` -- TCP port to listen on for FTP control connections.
     Defaults to ``21``.
   - ``verbose`` -- Verbosity level for log messages. ``0`` is silent,
     ``1`` prints connection and command messages, ``2`` is reserved
     for additional detail.
   - ``splash`` -- If ``True``, print a banner with the listening
     address and port for each interface.

.. function:: stop() -> None

   Stop the FTP server.

   Closes all active client command connections, the listening
   sockets on each interface, and the passive-mode data socket.

.. function:: restart(port: int = 21, verbose: int = 0, splash: bool = True) -> None

   Stop and then restart the FTP server.

   Equivalent to calling :func:`stop`, waiting briefly, then calling
   :func:`start` with the same arguments.

   Arguments:

   - ``port`` -- TCP port to listen on for FTP control connections.
   - ``verbose`` -- Verbosity level for log messages.
   - ``splash`` -- If ``True``, print a banner for each interface.


Module variables
----------------

.. data:: ftpsockets
   :type: list

   List of currently bound listening sockets, one per active network
   interface. Populated by :func:`start` and cleared by :func:`stop`.

.. data:: datasocket
   :type: socket | None

   The shared passive-mode data socket, or ``None`` when the server is
   stopped.

.. data:: client_list
   :type: list

   List of currently connected ``FTP_client`` instances.

.. data:: verbose_l
   :type: int

   Current verbosity level, set by the ``verbose`` argument of
   :func:`start`.

.. data:: client_busy
   :type: bool

   ``True`` while a command from one client is being processed; used
   to reject overlapping commands from other clients.
