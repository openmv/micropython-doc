Streaming frames
================

A counter is the simplest possible channel. The next step up -- and
the most common real use -- is streaming image frames from the cam
to a host program at the cam's frame rate. The mechanics are the
same as the counter: a backend with ``size``, ``read``, and now
``poll``. The interesting parts are how the cam keeps the data
fresh and how the protocol library transparently handles
fragments larger than the cam's max payload.

The cam side
------------

A frame channel exposes a JPEG of the latest snapshot::

   import csi
   import protocol

   csi0 = csi.CSI()
   csi0.reset()
   csi0.pixformat(csi.RGB565)
   csi0.framesize(csi.QVGA)

   latest_jpeg = None

   class FrameChannel:
       def poll(self):
           return latest_jpeg is not None
       def size(self):
           return len(latest_jpeg) if latest_jpeg else 0
       def read(self, offset, size):
           return latest_jpeg[offset:offset + size]

   ch = protocol.register(name='frame', backend=FrameChannel())

   while True:
       img = csi0.snapshot()
       latest_jpeg = bytes(img.compress(quality=85).bytearray())
       ch.send_event(0x01)   # notify host that a new frame is ready

A few differences from the counter:

* ``poll`` is present. The host polls each channel before reading;
  the polling reply is a single byte so it costs almost nothing.
  When ``poll`` returns :data:`False` the host skips the round trip
  entirely.
* ``size`` returns the current JPEG length, not regenerated on
  demand. The application separately *captures* into ``latest_jpeg``
  on its own schedule. The host reads whatever happens to be there
  at the moment of the request.
* ``send_event(0x01)`` notifies the host immediately when a new
  frame is ready, without the host having to poll. The event ID
  ``0x01`` is application-defined ("frame ready" in this case);
  use a different small integer for each kind of notification.
* The ``bytes(...)`` wrap around the JPEG is *load-bearing*: the
  next ``csi0.snapshot()`` reuses the camera's image buffer in
  place, and ``latest_jpeg`` has to outlive that. The same defensive
  copy showed up in the webservers chapter for the same reason.

Fragmentation
-------------

QVGA RGB565 at JPEG quality 85 compresses to roughly 10-25 KB,
depending on the scene. The maximum payload on a Cam H7 is 4082
bytes (see the table in :func:`protocol.init`). One JPEG read won't
fit in one packet -- and that's fine, because the protocol library
fragments it transparently.

When the host asks for ``channel_read('frame', 12000)``:

1. The library issues a ``CHANNEL_READ`` packet for the first
   ~4 KB chunk. The cam runs ``read(0, 4082)`` and replies.
2. The library issues a second ``CHANNEL_READ`` for the next
   chunk. The cam runs ``read(4082, 4082)`` and replies.
3. The third call completes the read. The library glues the three
   chunks together and returns 12000 bytes to the host caller.

Each fragment has its own header and CRCs and goes through the
reliability layer independently. If one chunk fails its CRC the
library retransmits just that chunk; the application code on
either side never sees the failure.

On the cam side, the application's ``read`` method is called once
per fragment with the right offset. The backend doesn't need to
know about fragments at all -- as long as ``read`` returns the
requested range of bytes, the library handles the rest.

The host side
-------------

The host pulls frames in a tight loop::

   import io
   from PIL import Image
   from openmv.camera import Camera

   with Camera('/dev/ttyACM0', baudrate=921600) as cam:
       cam.update_channels()

       while True:
           if not cam.channel_size('frame'):
               continue
           size = cam.channel_size('frame')
           data = cam.channel_read('frame', size)
           img = Image.open(io.BytesIO(data))
           img.show()                  # or feed to a GUI

The :meth:`~openmv.camera.Camera.channel_size` call doubles as a
"is anything ready" check -- zero means the cam hasn't captured
yet -- so the loop skips read attempts on an empty buffer. For
GUI applications that already poll on a timer, this is the natural
pattern.

Pillow's ``Image.open`` decodes the JPEG; the cam already
JPEG-compressed it so the host doesn't have to redo expensive
bit-packing on RGB565. The host script could just as easily save
the bytes to disk, hand them to OpenCV, or push them through a web
view.

Throughput thinking
-------------------

Three things bound the achievable frame rate over USB:

* The cam's frame rate. QVGA RGB565 at low gain runs ~60 fps on a
  Cam H7; the cam can't deliver faster than it captures.
* The max payload. Bigger payloads mean fewer fragments and less
  framing overhead per packet, so the larger cams (N6, AE3) at 8
  KB max payload move bytes faster than the H7 at 4 KB.
* CRC and ACK overhead. Each packet costs 14 bytes of framing plus
  one ACK round-trip. For long fragments the per-payload overhead
  is small; for tiny payloads it dominates.

For most cam-to-laptop GUI work the limiting factor is the cam's
capture and JPEG compression time, not the protocol stack. Where
the protocol does become the bottleneck -- streaming uncompressed
raw frames at 30+ fps, for example -- the levers are turning off
ACKs (``protocol.init(ack=False)``), choosing a larger pixel
buffer if the cam supports it, or moving the cam to a TCP
transport where the host has more buffer space than USB.

This is one half of streaming -- the cam pushing data to the
host. The other half is the host pushing data to the cam: a
control loop where the operator's slider or button on the laptop
changes the cam's behaviour at runtime.
