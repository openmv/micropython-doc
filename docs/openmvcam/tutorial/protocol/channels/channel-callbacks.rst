Channel callbacks
=================

A backend object is a Python class. The protocol library inspects
the methods present on the instance you hand to
:func:`protocol.register` and wires each one to the corresponding
host-side operation. A backend with only ``size`` and ``read`` is a
read-only one-shot data channel; a backend with all eight callbacks
is a full bidirectional, lockable, shape-aware, ioctl-able channel.

The full callback set
---------------------

Eight methods make up the backend interface. Implement only the
ones the channel needs.

**Lifecycle.**

* ``init(self) -> object`` -- called once when the channel is
  registered with a connected host. Return any non-:data:`None`
  value on success. Useful for late initialisation that depends on
  the host being present.

**Polling and locking.**

* ``poll(self) -> bool`` -- the host calls this before reading.
  Return :data:`True` if data is available, :data:`False` if not.
  When :data:`False`, the host gets a "no data" reply without the
  backend's ``read`` method running at all.
* ``lock(self) -> bool`` -- acquire exclusive use of the channel
  for a multi-packet operation. Return :data:`True` on success.
  The host calls this around large reads so a snapshot stays
  internally consistent.
* ``unlock(self) -> bool`` -- release the lock. Always matches a
  prior ``lock``.

**Data shape.**

* ``size(self) -> int`` -- return how many bytes are currently
  available to read.
* ``shape(self) -> tuple`` -- return a tuple of up to four integers
  describing the *structure* of the data: image height, image
  width, total byte count. The host reads it through
  :meth:`~openmv.camera.Camera._channel_shape`. Useful when the
  data is fixed-width tensors (an image, a depth map) and the host
  needs to know the dimensions to unpack the buffer.

**I/O.**

* ``read(self, offset, size) -> bytes`` -- return up to ``size``
  bytes starting at ``offset``. The library handles fragmentation:
  if the host wants 50 KB on a board with 4 KB payload max, the
  library calls ``read`` repeatedly with increasing offsets and
  glues the fragments together.
* ``readp(self, offset, size) -> bytes`` -- a zero-copy variant.
  Return a buffer whose memory the protocol layer reads directly.
  The buffer must stay valid for the duration of the transfer.
  Worth using only when the data is genuinely large and lives in a
  pre-allocated region; for small payloads the copy is cheap.
* ``write(self, offset, data) -> int`` -- the host is writing
  ``data`` at ``offset``. Return the number of bytes consumed (or
  ``0`` for "everything's fine, no specific count").
* ``ioctl(self, cmd, length, arg) -> int`` -- arbitrary commands
  outside the read/write model. ``cmd`` is an opcode the
  application defines; ``arg`` is the payload (or :data:`None` for
  zero-length). Return ``0`` for success or a negative integer for
  an error.

**Misc.**

* ``flush(self) -> object`` -- drop any buffered data. Called from
  the host when it wants to reset the channel state.
* ``is_active(self) -> bool`` -- used only on backends that
  represent a physical transport (the built-in USB/UART channels).
  Application channels rarely need this.

Minimum useful backend
----------------------

A read-only data channel is two methods::

   class CounterChannel:
       def __init__(self):
           self.n = 0
           self.buf = b''
       def size(self):
           self.n += 1
           self.buf = ('count: %d' % self.n).encode()
           return len(self.buf)
       def read(self, offset, size):
           return self.buf[offset:offset + size]

   protocol.register(name='counter', backend=CounterChannel())

The host can now call ``cam.channel_size('counter')`` to advance
the counter and ``cam.channel_read('counter', size)`` to fetch the
text. ``size`` is the natural place to update state because the
host always calls it before ``read``.

For a channel where the data is *available* rather than *generated
on demand*, ``poll`` becomes useful::

   class FrameChannel:
       def __init__(self):
           self.frame = None
       def deliver(self, jpeg_bytes):
           self.frame = jpeg_bytes
       def poll(self):
           return self.frame is not None
       def size(self):
           return len(self.frame) if self.frame else 0
       def read(self, offset, size):
           return self.frame[offset:offset + size]

The application elsewhere calls ``deliver(...)`` whenever a new
frame is ready. The host polls and reads whenever it wants the next
frame. The two halves are decoupled.

Adding writes
-------------

A write callback receives a :class:`bytearray` that references the
protocol layer's buffer directly -- no copy. Treat the contents as
read-only inside the callback and copy out whatever you want to
keep::

   class ConfigChannel:
       def __init__(self):
           self.threshold = 12
       def size(self):
           return 0
       def read(self, offset, size):
           return b''
       def write(self, offset, data):
           # data is a bytearray; copy out the value
           self.threshold = int(bytes(data))
           return len(data)

For configuration with one or two fields a bare ``write`` like this
works. For richer typed data, the :class:`protocol.CBORChannel`
helper (covered in the widgets pages) handles encoding and decoding
in CBOR + SenML so the application sees a typed dict.

Events
------

The :meth:`ProtocolChannel.send_event` method sends a small event
notification to the host without changing what's readable on the
channel. The host's poll loop sees the event and can react -- for
example, refreshing a UI widget when the cam reports "new frame
ready" without the host having to poll the size first::

   ch = protocol.register(name='frame', backend=FrameChannel())

   while True:
       img = csi0.snapshot()
       ch.send_event(0x01)  # "new frame available"

Events flow over the same packets but with the ``EVENT`` flag set
in the header; the reliability layer treats them as best-effort
unless ``wait_ack=True`` is passed.

That's the entire backend interface. Eight methods, all optional,
and the protocol library decides what each channel can do based on
which methods are implemented.
