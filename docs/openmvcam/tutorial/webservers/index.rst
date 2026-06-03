Web Servers
===========

The networking chapters got the camera onto the network and gave it
sockets to talk through. *Web servers* is the first protocol that
builds on top of those sockets that the section covers in depth. HTTP
is the lingua franca of devices that talk to phones, dashboards,
cloud services, and other cameras -- the one protocol every browser,
every scripting language, and every embedded MCU agrees on.

This section covers both sides of HTTP from the camera:

* As a **client**, the camera reaches out to other HTTP services --
  uploading sensor readings to a cloud API, polling a weather service,
  posting captured images to a private gateway. The
  :mod:`requests` module is the camera's client.
* As a **server**, the camera answers HTTP requests from other
  devices -- exposing a control panel for a phone, serving a live
  MJPEG stream to a browser, accepting commands from a companion
  app. The :mod:`microdot` framework is the camera's server.

Both sit on top of :mod:`asyncio` for concurrency and on
:mod:`socket` / :mod:`ssl` for the transport. Encryption,
authentication, and access control all reuse the building blocks the
networking section introduced.

.. toctree::
   :caption: Concepts
   :maxdepth: 1

   basics/why-http.rst
   basics/http-roles.rst

.. toctree::
   :caption: As a client
   :maxdepth: 1

   client/requests.rst

.. toctree::
   :caption: As a server
   :maxdepth: 1

   server/minimal-app.rst
   server/routing.rst
   server/handlers.rst
   server/serving-frames.rst
   server/push.rst
   server/auth-and-sessions.rst
   server/security.rst

.. toctree::
   :caption: Wrap up
   :maxdepth: 1

   wrap-up.rst
