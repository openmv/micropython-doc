Bidirectional flow
==================

Channels are not one-way. A backend that implements ``write`` lets
the host push bytes *to* the cam, and the cam reacts. That's the
pattern behind every real interactive tool: the operator turns a
knob on the host GUI, the host writes the new value to a config
channel, the cam reads it the next time it captures.

A config channel
----------------

Adding to the streaming cam-side script, expose a second channel for
the JPEG quality::

   class ConfigChannel:
       def __init__(self):
           self.quality = 85

       def size(self):
           return 0

       def read(self, offset, size):
           # Not used for "host writes to cam" -- but the library
           # still needs the method present.
           return b''

       def write(self, offset, data):
           # data is a bytearray view into the protocol buffer.
           # Copy out the contents before doing anything with it.
           new_q = int(bytes(data))
           if 1 <= new_q <= 100:
               self.quality = new_q
           return len(data)

   config = ConfigChannel()
   protocol.register(name='config', backend=config)

The capture loop reads from ``config.quality`` whenever it
compresses a frame::

   while True:
       img = csi0.snapshot()
       latest_jpeg = bytes(
           img.compress(quality=config.quality).bytearray()
       )
       ch.send_event(0x01)

The host now has a knob. Set it to 50 and the next frame is
smaller (and uglier); set it to 95 and the next frame is bigger
(and sharper). The cam keeps capturing without restarting; the host
doesn't have to push a new script.

The write call from the host
----------------------------

On the host side, :meth:`~openmv.camera.Camera.channel_write`
sends bytes to a named channel::

   cam.channel_write('config', b'50')

The host SDK encodes the bytes as a single (or fragmented)
``CHANNEL_WRITE`` packet, the protocol layer delivers it to the
cam, the cam's ``write(offset=0, data=...)`` runs, and the cam's
side acknowledges. By the time the call returns the cam has
received and accepted the new value.

The write is atomic from the cam's point of view -- the protocol
library guarantees the backend's ``write`` runs to completion before
any other operation on that channel proceeds. Application code can
read ``config.quality`` from inside the capture loop without
worrying about the host stomping mid-snapshot.

When ``size`` and ``read`` are vestigial
----------------------------------------

A pure write channel still needs ``size`` and ``read`` defined,
even if they're stubs returning 0 and ``b''``. The library uses
the *presence* of methods to derive the channel's capability flags;
a backend that's missing ``read`` won't get ``CHANNEL_FLAG_READ``
set and the host will refuse a read attempt.

In practice the bytes returned from ``read`` on a write-only
channel are useful for a different purpose: echoing back the
current value so a host that just attached can ask the cam "what's
the current setting?" rather than starting from a default.
Returning the same JSON-encoded snapshot in ``read`` that ``write``
parses makes the channel a true round-trip configuration store::

   class ConfigChannel:
       def __init__(self):
           self.quality = 85
           self._buf = b''
       def size(self):
           import json
           self._buf = json.dumps({'quality': self.quality}).encode()
           return len(self._buf)
       def read(self, offset, size):
           return self._buf[offset:offset + size]
       def write(self, offset, data):
           import json
           new = json.loads(bytes(data))
           if 'quality' in new:
               self.quality = int(new['quality'])
           return len(data)

Now the host can ``channel_read('config')`` to see the current
value at any time. The cam serialises a fresh JSON dump on every
read so the host always sees the latest state.

A complete loop
---------------

With a frame channel for cam → host data, a config channel for
host → cam control, and a small amount of glue, the application is
an interactive tool:

* The host opens the cam, starts pulling frames, and displays
  them in a window.
* When the operator drags a slider, the host writes the new value
  on ``config``.
* The cam's capture loop picks the value up on the next frame.
* The new frames flow through the same ``frame`` channel.

That's the entire model. Two channels, two callbacks each, a
capture loop on the cam, a read-and-write loop on the host. No
framing logic visible, no error handling visible -- the protocol
library makes the reliable byte movement disappear.

For typed values -- sliders with min/max/step, toggles,
multiple-choice selects -- a JSON-encoded config dict starts to
feel verbose. The :class:`protocol.CBORChannel` helper does the
same round-trip with typed widget metadata baked in, which is the
foundation for the host-side GUI patterns the openmv-projects tools
use.
