Hello world -- the cam side
===========================

The smallest useful protocol application is a cam-side script that
exposes one channel and a host-side script that reads from it. The
cam half is below; the host half is its companion page in the same
hello-world group.

The script
----------

Run this in the IDE on the cam::

   import protocol
   import time

   class CounterChannel:
       def __init__(self):
           self.value = 0
           self.buf = b''

       def size(self):
           # Called by the host before every read.
           self.value += 1
           self.buf = str(self.value).encode()
           return len(self.buf)

       def read(self, offset, size):
           return self.buf[offset:offset + size]

   protocol.register(name='counter', backend=CounterChannel())

   while True:
       time.sleep_ms(100)

That's the entire cam-side application. Twenty lines.

Walking through it
------------------

``import protocol`` brings the OpenMV protocol module into scope.
The cam boots with a default USB-CDC protocol stack already running,
so the application doesn't need to call :func:`protocol.init` --
the channels are added to the existing stack.

``CounterChannel`` is the backend class. The protocol library will
introspect this instance, find a ``size`` method and a ``read``
method, and wire them to host-side ``channel_size`` and
``channel_read`` calls. The absence of a ``write`` method tells the
library this channel is read-only; the host will refuse a write
attempt without ever asking the backend.

The body of ``size`` advances the counter and stores the encoded
value before returning the length. The host always calls
:meth:`~openmv.camera.Camera.channel_size` before
:meth:`~openmv.camera.Camera.channel_read`, so updating state inside
``size`` is the right place to put "regenerate the data when the
host asks."

``read`` returns a slice of the cached buffer. The protocol library
may call it more than once for a single host read if the value is
bigger than the negotiated max payload -- the ``offset`` argument
walks through the buffer. For small payloads like this one the
library calls ``read`` exactly once with ``offset=0``.

``protocol.register(name='counter', backend=CounterChannel())``
hands the instance over. The library assigns it the next free
channel ID, emits a ``CHANNEL_REGISTERED`` event for any connected
host, and adds it to the channel list. The return value is a
:class:`~protocol.ProtocolChannel` handle; this minimal script
doesn't need it, but applications that want to emit channel events
later store it.

The trailing ``while True: time.sleep_ms(100)`` is there because
the application needs to keep running. The protocol stack runs on
its own (interrupt-driven on USB, polled on UART), so the main
script's only job after registering channels is to stay alive and
do whatever the application does. A real application would be
capturing frames, reading sensors, or running ML inference; this
one just yields the CPU so the protocol layer can do its work
without contention.

Running it
----------

Hit Run in the IDE. The IDE itself uses the protocol stack to
display ``stdout`` from the cam, so nothing visible changes -- the
``counter`` channel is registered but no one is reading from it.
The cam is now waiting for any host that connects to enumerate
the channels and start reading.

What can go wrong
-----------------

* **"RuntimeError: failed to register channel."** The cam has run
  out of channel slots (the 32-channel limit). Restart the cam and
  try again, or unregister channels the application no longer
  needs.
* **The host doesn't see the channel.** The host connected before
  the script ran ``protocol.register``. The cam sends a
  ``CHANNEL_REGISTERED`` event the host should listen for, and the
  Python SDK's :meth:`~openmv.camera.Camera.update_channels`
  refreshes the local list. If the host script doesn't call it, it
  won't see new channels.
* **The IDE shows no output.** The script's ``while True`` loop
  doesn't print anything, which is correct. The channel-level
  traffic shows up only on a host that connects to ``counter``;
  the IDE shows ``stdout``.

The cam side is registered and waiting. The host side opens the
USB port and pulls the value.
