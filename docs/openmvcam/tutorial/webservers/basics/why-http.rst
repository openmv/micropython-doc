Why HTTP
========

The networking section ended with a camera that could open sockets,
send and receive bytes, look up names, and wrap any connection in
TLS. Two devices that share a private network and the same
application binary can use those primitives directly -- pick a port,
agree on a wire format, exchange bytes. Two devices that *do not*
share a binary -- a camera and a phone, a camera and an arbitrary
web browser, a camera and any third-party cloud service -- need a
protocol the other side already knows about. That protocol is
almost always **HTTP**.

What HTTP gives both sides
--------------------------

HTTP is universal in three useful ways:

* **Every platform has a client.** Browsers, ``curl``, every scripting
  language, every embedded toolkit, every cloud SDK. If the camera
  speaks HTTP, anything else on the network can talk to it without a
  custom integration.
* **The data model is dirt-simple.** A request is a method (``GET``,
  ``POST``, ...), a path (``/api/status``), some headers, and an
  optional body. A response is a status code, some headers, and a
  body. Both directions stop at "a few headers plus an opaque body";
  the body itself can be JSON, an image, a file, a stream of bytes
  -- whatever the application wants.
* **All the production scaffolding is free.** HTTPS is just HTTP
  wrapped in :doc:`/openmvcam/tutorial/networking/encrypted-sockets`.
  Authentication has standard headers (``Authorization: Basic …`` /
  ``Authorization: Bearer …``). Browsers and reverse proxies enforce
  CORS and HTTPS. Logs and metrics tools already parse HTTP. None of
  that has to be re-invented.

The two camera-side cases
-------------------------

* **The camera as a client.** A timed loop reads a sensor and POSTs
  the value to a cloud endpoint; a captured image is uploaded to a
  private API; a status check polls an internal dashboard. The
  camera initiates; the other side responds. The
  :mod:`requests` module is the camera's HTTP client.

* **The camera as a server.** A phone in the same room opens
  ``http://kitchen-cam.local/`` and sees a live MJPEG preview; a
  dashboard polls ``/api/status`` for the latest detection count; a
  control panel POSTs to ``/api/relay`` to toggle a switch. The
  camera listens; other devices initiate. The :mod:`microdot`
  framework is the camera's HTTP server.

Either side is small to set up -- one ``import`` and a handful of
lines. The :doc:`http-roles` page covers the vocabulary the rest of
this section uses, and the per-side chapters that follow build out
both ends.

When not to use HTTP
--------------------

HTTP is the right answer for **request-response** workloads. The
client asks, the server answers, the connection closes (or stays
open as a keep-alive for the next request). The wrong cases:

* **Continuous bidirectional streams.** Real-time control loops
  where both sides push asynchronously -- a robot teleop link, a
  game. HTTP layers WebSockets on top to support this, but a plain
  TCP socket from the networking chapter may be the simpler
  primitive.
* **Sub-millisecond timing.** HTTP carries headers on every request.
  When the per-message overhead dominates the payload, a raw socket
  from the networking chapter is leaner.
* **Connectionless broadcast.** Telemetry that should reach any
  listener on the LAN without setup. UDP multicast is the right
  tool, not HTTP.

For the much more common case -- a request, a response, occasionally
a long-running stream -- HTTP is the default and the rest of this
section assumes it.
