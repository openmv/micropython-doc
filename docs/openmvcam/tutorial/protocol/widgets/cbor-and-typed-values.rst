CBOR and typed values
=====================

A bare ``write`` callback gives application code a single bytes
buffer to interpret however it likes. For a config channel with one
or two integer settings that's fine; for a real GUI -- a slider
with a min and max, a toggle, a multi-choice select, a 2D depth
preview -- the application ends up reinventing a serialisation
format every time. :class:`protocol.CBORChannel` is the OpenMV
answer to that: a backend that already speaks a typed wire format,
so the application can think in *fields* instead of *bytes*.

What it serialises
------------------

The class is shipped as part of the frozen ``protocol`` package
and uses `CBOR <https://cbor.io/>`__ -- the same compact binary
encoding the SenML sensor-data standard uses. Each field is a
small dictionary with integer keys for name (``0``), unit (``1``),
value (``2``), and a few OpenMV-specific extensions for widget
types. The host SDK and the bundled host GUIs decode CBOR
natively, so the host receives a list of typed records instead of
a flat byte stream.

Five widget types are defined:

* ``label`` -- a read-only display: a string or number with an
  optional unit ("Cel", "%RH").
* ``toggle`` -- a boolean. Renders as a checkbox or switch on the
  host.
* ``slider`` -- a numeric value with min, max, step, and an
  optional unit. The host renders as a slider.
* ``select`` -- a choice from a list of strings. The host renders
  as a dropdown.
* ``depth`` -- 2D numeric data (a small image or a depth map)
  rendered as a heatmap on the host. Width, height, and a
  min/max range are part of the field's metadata.

The fields the application *adds* to the channel are also the
fields the host *sees*. Adding a slider with ``add('quality',
type='slider', min=1, max=100, value=85)`` causes the host GUI to
render a slider labelled "quality" with the correct range and
initial position the moment the channel is registered.

The cam side
------------

A complete cam-side script using :class:`CBORChannel`::

   from protocol import CBORChannel
   import csi
   import protocol

   csi0 = csi.CSI()
   csi0.reset()
   csi0.pixformat(csi.RGB565)
   csi0.framesize(csi.QVGA)

   def on_read(ch):
       # Called by the protocol layer before the host serialises.
       # Refresh dynamic values here.
       ch['temp'] = read_temp()        # latest sensor reading
       ch['fps'] = current_fps()

   def on_write(ch, name, value):
       if name == 'mirror':
           csi0.hmirror(value)
       elif name == 'quality':
           global jpeg_quality
           jpeg_quality = value

   ch = CBORChannel(on_read=on_read, on_write=on_write)
   ch.add('temp', type='label', unit='Cel', value=0.0)
   ch.add('fps',  type='label', value=0)
   ch.add('mirror', type='toggle', value=False)
   ch.add('quality', type='slider', min=1, max=100, value=85)

   protocol.register(name='controls', backend=ch)

What the application gains:

* No serialisation code. The channel knows how to encode every
  field. Adding ``ch.add('zoom', type='slider', min=1, max=4)``
  exposes a new slider in one line.
* Typed updates. The ``on_write`` callback gets the *name* of the
  field and the *typed* value (a Python :class:`int`, :class:`bool`,
  or :class:`str` matching the widget type) -- no parsing.
* Round-tripping. ``ch['temp'] = 24.5`` updates the in-memory
  field; the next host read sees the new value.

The slider's ``(min, max, value)`` tuple
----------------------------------------

Setting a slider value via ``ch['quality'] = 90`` updates just the
value. Setting it via ``ch['quality'] = (10, 90, 50)`` updates the
min, max, and value all at once. That comes up in calibration
flows where the cam computes the dynamic range of a measurement and
tells the host "the slider should now span this new interval."

Depth fields
------------

``depth`` is for 2D numeric data the host should render as a
heatmap. The field carries width, height, a min, and a max in its
metadata; the *value* is a bytes buffer of ``width * height``
items, each one a 16-bit integer (typically). On the cam side::

   ch.add('thermal', type='depth', width=80, height=60,
          min=20, max=40)
   ch['thermal'] = struct.pack('<%dh' % (80*60), *frame.values())

The host SDK and the bundled GUIs render a colour-mapped image and
update it whenever the cam's CBOR buffer changes.

The protocol round-trip
-----------------------

CBORChannel doesn't change the underlying protocol -- it's still
``size`` / ``read`` / ``write`` callbacks under the hood, with the
same fragmentation and reliability the framing layers provide. The
class is just a convenient backend that happens to serialise its
state to CBOR and parse incoming CBOR back into typed fields.

That means the same channel works with any host that understands
the wire format: the bundled :class:`openmv.camera.Camera` SDK, a
custom Python script using the ``cbor2`` library, or a Rust or C++
host that ships its own CBOR decoder. The fields are documented in
the openmv-projects code; the wire format is the small CBOR
dialect SenML defines.

A typed widget model on the cam side, an automatic-rendering GUI
on the host side, and the same protocol library handling the
delivery in between. With that in place the only thing left is to
wire one to the other and see real pixels move.
