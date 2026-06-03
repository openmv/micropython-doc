Building a GUI
==============

A :class:`protocol.CBORChannel` on the cam plus a host-side GUI
framework is a complete interactive tool. The cam exposes typed
fields; the GUI renders them as widgets; user input flows back as
typed writes the cam reacts to. This page shows the pattern with
`DearPyGui <https://github.com/hoffstadt/DearPyGui>`__, which is
what the OpenMV-provided tools in ``openmv-projects/tools/`` use.

Why DearPyGui
-------------

DearPyGui ships as a single pip-installable package, runs on every
desktop OS, doesn't drag in Qt, and renders fast enough for
live-camera GUIs. The widgets are familiar (sliders, buttons,
plots, images) and the API is Python-only with no signal/slot
ceremony. For a host tool that needs to talk to a cam and present
a few controls and a video feed, it's the lightest option that
still looks like a proper application.

Other frameworks work too -- PySide6 / PyQt, Tkinter, even
``rich``-based TUIs -- but the examples below are DearPyGui because
that's where the existing OpenMV calibration tools live.

The pattern
-----------

A complete host script for the CBOR cam-side example
(:doc:`cbor-and-typed-values`)::

   import dearpygui.dearpygui as dpg
   from openmv.camera import Camera

   cam = Camera('/dev/ttyACM0', baudrate=921600)
   cam.connect()
   cam.update_channels()

   # Read the channel once to learn what fields exist.
   import cbor2
   fields = cbor2.loads(cam.channel_read('controls'))

   dpg.create_context()
   with dpg.window(label='Cam controls', width=400, height=300):
       for f in fields:
           name = f[0]
           typ = f[-30]
           value = f.get(2)

           if typ == 'toggle':
               dpg.add_checkbox(
                   label=name, default_value=value,
                   callback=lambda _s, v, u=name: send(u, v),
               )
           elif typ == 'slider':
               dpg.add_slider_int(
                   label=name,
                   min_value=f[-31], max_value=f[-32],
                   default_value=value,
                   callback=lambda _s, v, u=name: send(u, v),
               )
           elif typ == 'label':
               dpg.add_text(default_value=str(value), tag='lbl_' + name)

   def send(name, value):
       # Send a CBOR update list back to the cam.
       update = [{0: name, 2: value}]
       cam.channel_write('controls', cbor2.dumps(update))

   def refresh():
       # Pull the latest values periodically and update labels.
       data = cam.channel_read('controls')
       for f in cbor2.loads(data):
           tag = 'lbl_' + f[0]
           if dpg.does_item_exist(tag):
               dpg.set_value(tag, str(f.get(2)))

   dpg.create_viewport(title='Cam GUI', width=400, height=320)
   dpg.setup_dearpygui()
   dpg.show_viewport()

   while dpg.is_dearpygui_running():
       refresh()
       dpg.render_dearpygui_frame()

   cam.disconnect()
   dpg.destroy_context()

The script splits into three phases:

* **Setup.** Open the cam, read the channel once, build widgets to
  match each field's type. The integer keys (``0`` for name, ``2``
  for value, ``-30`` for widget type) come from the CBORChannel
  source -- the host script doesn't need to know about them in
  most cases because the openmv-projects tools wrap them in a
  helper class.
* **Run.** The render loop calls ``refresh`` on every frame to
  pull updated values from the cam (labels that change every
  second, ``fps`` counters, sensor readings) and rebuilds those
  widget values in place. User-input callbacks send the new
  values back via :meth:`channel_write`.
* **Teardown.** Disconnect the cam, destroy the GUI context.

For a calibration tool the same script also reads the cam's
``frame`` channel each refresh and shows the bytes in a
:func:`dpg.add_raw_texture` widget -- a live preview embedded in
the GUI window, with the controls right next to it.

Pulling it together
-------------------

The shipped
``openmv-projects/tools/thermal-overlay-calibration/`` is a real
calibration tool that does exactly this: two cam-side channels
(one for the RGB preview, one for the Lepton thermal feed),
several CBORChannel fields for the homography parameters, and a
DearPyGui frontend that shows the two streams side by side with
sliders to tune the warp matrix until the thermal overlay aligns
with the RGB feed.

The pieces are the same as the example above, just scaled up:
two frame channels instead of one, ten CBOR fields instead of
four, and a render loop that decodes both JPEG streams every
frame. With the protocol library handling the wire-level work, the
calibration tool itself is a few hundred lines of straightforward
GUI code -- the cam-to-host link is invisible.

That's the whole point. The protocol library turns "cam + host
program" from a custom serialisation project into a few classes
with named callbacks. The remaining engineering is application
logic, not wire format.
