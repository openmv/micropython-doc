Hello world -- the host side
============================

The host side is a small Python script that opens the cam's USB
port, finds the ``counter`` channel registered by the cam-side
script, and reads from it.

Installing the package
----------------------

The host SDK ships as the ``openmv`` package on PyPI::

   pip install openmv

The package depends on ``pyserial`` for the transport and a few
standard libraries for protocol decoding. It works on CPython 3.9
or newer.

The script
----------

Run this on the host PC, with the cam plugged in over USB::

   from openmv.camera import Camera
   import time

   with Camera('/dev/ttyACM0', baudrate=921600) as cam:
       cam.update_channels()
       if not cam.has_channel('counter'):
           print('counter channel not registered on the cam')
           raise SystemExit

       for _ in range(5):
           size = cam.channel_size('counter')
           data = cam.channel_read('counter', size)
           print('cam says:', data.decode())
           time.sleep(0.5)

Five reads, half a second apart. Each one calls
:meth:`~openmv.camera.Camera.channel_size` to make the cam advance
its counter and emit the new buffer length, then
:meth:`~openmv.camera.Camera.channel_read` to fetch the bytes.
Output::

   cam says: 1
   cam says: 2
   cam says: 3
   cam says: 4
   cam says: 5

The serial port name is ``/dev/ttyACM0`` on Linux and macOS; on
Windows it's ``COM3``, ``COM4``, or whichever number Device Manager
shows for the OpenMV cam. The baud rate is the protocol's magic
value -- ``921600`` -- which the cam's USB-CDC driver recognises as
"client wants the protocol, not the REPL."

What the context manager does
-----------------------------

The ``with Camera(...) as cam`` block does three things at setup:

1. Opens the USB port via ``pyserial``.
2. Sends a ``PROTO_SYNC`` packet and waits for the cam's reply.
3. Exchanges capabilities with the cam (defaults: CRC on, ACK on,
   max payload sized for the connected board).

On block exit it closes the connection cleanly and releases the
port.

If the cam isn't responding -- not powered, USB cable not data-
capable, another program holding the port -- the call to
``Camera(...)`` raises :exc:`OSError` from the underlying serial
open or a :exc:`TimeoutError` from the protocol sync. The retry
mechanic the library exposes via
:meth:`~openmv.camera.Camera.connect` handles the "wait for the
cam to boot" case; the example script doesn't bother because by
the time the user runs it the cam is already up.

Updating the channel list
-------------------------

The cam side registered the ``counter`` channel after boot. The host
needs to learn about it. Two ways:

* :meth:`~openmv.camera.Camera.update_channels` re-issues
  ``CHANNEL_LIST`` and rebuilds the local map. The script above
  calls this once at startup.
* The protocol library emits a ``CHANNEL_REGISTERED`` event when a
  new channel comes online. A long-running host script that uses
  :meth:`~openmv.camera.Camera.poll_events` automatically picks
  them up.

Either pattern works. The explicit call is shorter for
script-style code; the event-driven version is better for a host
GUI that runs for a long time and wants to see the cam re-register
channels after a reboot.

Reading round-trips
-------------------

Each :meth:`~openmv.camera.Camera.channel_size` / ``channel_read``
pair is two round-trips:

1. Host sends ``CHANNEL_SIZE`` packet, cam runs ``size()``, cam
   replies with the size.
2. Host sends ``CHANNEL_READ`` packet, cam runs ``read(offset,
   size)``, cam replies with the bytes.

Over a USB-CDC link both round-trips take a millisecond or two
combined. Over UART or TCP they take longer. Applications that
read in a tight loop should call :meth:`channel_size` only when
they actually need to know the current size; for fixed-size data
the size can be cached from the first call.

What can go wrong
-----------------

* **"counter channel not registered on the cam."** The cam-side
  script hasn't started yet, or it crashed before reaching
  ``protocol.register``. Check the IDE for tracebacks.
* **"Permission denied" on /dev/ttyACM0** -- on Linux, the user
  isn't in the ``dialout`` (or ``uucp``) group. Add the user and
  log out / in, or run the host script with ``sudo`` for a quick
  check.
* **The script hangs at ``channel_read``** -- the cam's ``read``
  method raised an exception or returned the wrong type. The cam
  side IDE shows the traceback; fix it and rerun.

The two scripts together are a complete protocol application. Cam
registers a channel; host opens the port and reads from it. The
patterns shown in :doc:`/openmvcam/tutorial/webservers/index` for
HTTP clients are the same form: connect, request, parse, repeat.
The protocol library is what makes the request/response wire
format reliable and structured instead of a raw byte stream.
