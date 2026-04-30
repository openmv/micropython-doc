:mod:`uping` --- Ping another computer
======================================

.. module:: uping
   :synopsis: Ping another computer

Functions
---------

.. function:: ping(host: str, count: int = 4, timeout: int = 5000, interval: int = 10, quiet: bool = False, size: int = 64) -> tuple[int, int]

    Sends ICMP echo request packets to ``host`` and returns a tuple
    ``(n_trans, n_recv)`` of the number of packets transmitted and received.

    Arguments:

    - ``host`` -- hostname or IP address to ping.
    - ``count`` -- number of echo request packets to send.
    - ``timeout`` -- overall timeout in milliseconds to wait for replies.
    - ``interval`` -- delay in milliseconds between successive packets.
    - ``quiet`` -- if ``True``, suppress per-packet and summary ``print`` output.
    - ``size`` -- packet size in bytes (must be ``>= 16``).

.. function:: checksum(data: bytes) -> int

    Computes the 16-bit Internet checksum of ``data`` as defined by RFC 1071.
    Used internally to populate the ICMP header checksum field.
