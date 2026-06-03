Wrap up
=======

A cam plugged into a USB cable that runs an interactive GUI on a
laptop -- with bidirectional data flow, retransmits hidden, multiple
logical streams sharing one port, and typed widgets that render
themselves -- comes out of about forty lines of cam-side code and a
DearPyGui script the same size. The protocol library turns a byte
pipe into a programmable channel surface and keeps everything below
the application invisible.

What the chapter built
----------------------

* A four-layer mental model of the stack: transport, framing,
  reliability, channels. Each layer solves one problem and ignores
  everything above.
* The on-the-wire packet format -- 10-byte header with CRC,
  variable payload, trailing CRC. Small enough to walk through
  byte by byte.
* The handshake the cam and host run when a transport connects:
  PROTO_SYNC, capability exchange, channel discovery.
* The reliability machinery on top: sequence numbers, ACKs, NAKs,
  retransmits with exponential backoff, the ten status codes.
* The channel model: up to 32 named logical streams on one wire,
  with built-in ``stdin`` / ``stdout`` / ``stream`` / ``profile``
  and application channels registered by Python class.
* The backend interface -- ``size``, ``read``, ``write``, ``poll``,
  ``lock`` / ``unlock``, ``shape``, ``ioctl``, ``flush``,
  ``is_active`` -- and how the protocol library uses the methods
  present on a backend to decide what the channel supports.
* Two complete hello-world scripts, cam and host, that exchange a
  counter over USB.
* A frame-streaming pattern and a bidirectional config pattern
  that together form the foundation for every interactive cam tool.
* The CBORChannel helper for typed widgets, and a DearPyGui host
  script that turns those widgets into a real GUI without writing
  any serialisation code.

Reference roadmap
-----------------

The library reference pages are the lookup destinations when one of
these features comes up in real code:

* :doc:`/library/omv.protocol` -- the :mod:`protocol` module,
  :func:`protocol.init`, :func:`protocol.register`,
  :class:`~protocol.ProtocolChannel`,
  :class:`~protocol.CBORChannel`, channel flag constants, and the
  per-cam max-payload table.
* The host SDK -- ``pip install openmv``,
  :class:`openmv.camera.Camera`. Methods touched in this chapter:
  :meth:`~openmv.camera.Camera.update_channels`,
  :meth:`~openmv.camera.Camera.has_channel`,
  :meth:`~openmv.camera.Camera.channel_size`,
  :meth:`~openmv.camera.Camera.channel_read`,
  :meth:`~openmv.camera.Camera.channel_write`,
  :meth:`~openmv.camera.Camera.poll_events`,
  :meth:`~openmv.camera.Camera.read_frame`,
  :meth:`~openmv.camera.Camera.exec`, and
  :meth:`~openmv.camera.Camera.stop`.
* The OpenMV-projects repository -- real tools built on the
  protocol library. ``openmv-projects/tools/`` includes
  ``thermal-overlay-calibration`` (RGB + thermal alignment GUI),
  ``ccm-tuning`` (colour-correction matrix tuner),
  ``genx320-event-streaming`` and
  ``genx320-overlay-calibration`` (event-camera tooling). Each
  one uses the patterns from this chapter end to end.

Where to take it next
---------------------

A few directions cam projects move from here:

* **Building a calibration tool.** Two CBOR channels (controls +
  preview), a frame channel, and a few hundred lines of DearPyGui.
  The thermal-overlay-calibration tool is the worked example.
* **Telemetry GUI for a fleet.** A host script connects to several
  cams over TCP (one Camera object per cam), pulls health and
  status from a single channel on each, and displays them in a
  single window.
* **Remote tuning over UART.** The same channel callbacks; the
  application calls ``protocol.init`` to switch from USB to a UART
  transport. The cam keeps running headless and a Python script on
  a Raspberry Pi or laptop talks to it over a serial line for
  field tuning.

The wire format, the reliability layer, and the channel abstraction
don't change. Picking the transport that fits the deployment and
adding a channel for each thing the host needs to see or set is the
entire engineering job from here on.
