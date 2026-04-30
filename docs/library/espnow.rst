:mod:`espnow` --- support for the ESP-NOW wireless protocol
===========================================================

.. module:: espnow
    :synopsis: ESP-NOW wireless protocol support

This module provides an interface to the `ESP-NOW <https://www.espressif.com/
en/products/software/esp-now/overview>`_ protocol provided by Espressif on
ESP32 and ESP8266 devices (`API docs <https://docs.espressif.com/
projects/esp-idf/en/latest/api-reference/network/esp_now.html>`_).

Table of Contents:
------------------

    - `Introduction`_
    - `Configuration`_
    - `Sending and Receiving Data`_
    - `Peer Management`_
    - `Callback Methods`_
    - `Exceptions`_
    - `Constants`_
    - `Wifi Signal Strength (RSSI) - (ESP32 Only)`_
    - `Supporting asyncio`_
    - `Broadcast and Multicast`_
    - `ESPNow and Wifi Operation`_
    - `ESPNow and Sleep Modes`_

Introduction
------------

ESP-NOW is a connection-less wireless communication protocol supporting:

- Direct communication between up to 20 registered peers:

  - Without the need for a wireless access point (AP),

- Encrypted and unencrypted communication (up to 6 encrypted peers),

- Message sizes up to 250 bytes,

- Can operate alongside Wifi operation (:doc:`network.WLAN<network.WLAN>`) on
  ESP32 and ESP8266 devices.

It is especially useful for small IoT networks, latency sensitive or power
sensitive applications (such as battery operated devices) and for long-range
communication between devices (hundreds of metres).

This module also supports tracking the Wifi signal strength (RSSI) of peer
devices.

A simple example would be:

**Sender:** ::

    import network
    import espnow

    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)  # Or network.WLAN.IF_AP
    sta.active(True)
    sta.disconnect()      # For ESP8266

    e = espnow.ESPNow()
    e.active(True)
    peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'   # MAC address of peer's wifi interface
    e.add_peer(peer)      # Must add_peer() before send()

    e.send(peer, "Starting...")
    for i in range(100):
        e.send(peer, str(i)*20, True)
    e.send(peer, b'end')

**Receiver:** ::

    import network
    import espnow

    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)
    sta.active(True)
    sta.disconnect()   # Because ESP8266 auto-connects to last Access Point

    e = espnow.ESPNow()
    e.active(True)

    while True:
        host, msg = e.recv()
        if msg:             # msg == None if timeout in recv()
            print(host, msg)
            if msg == b'end':
                break

class ESPNow
------------

.. class:: ESPNow()

    Returns the singleton ESPNow object. As this is a singleton, all calls to
    `espnow.ESPNow()` return a reference to the same object.

    .. note::
      Some methods are available only on the ESP32 due to code size
      restrictions on the ESP8266 and differences in the Espressif API.

   .. method:: active(flag: bool | None = None, /) -> bool

      Initialise or de-initialise the ESP-NOW communication protocol depending on
      the value of the ``flag`` optional argument.

      **Arguments:**

        - *flag*: Any python value which can be converted to a boolean type.

          - ``True``: Prepare the software and hardware for use of the ESP-NOW
            communication protocol, including:

            - initialise the ESPNow data structures,
            - allocate the recv data buffer,
            - invoke esp_now_init() and
            - register the send and recv callbacks.

          - ``False``: De-initialise the Espressif ESP-NOW software stack
            (esp_now_deinit()), disable callbacks, deallocate the recv
            data buffer and deregister all peers.

      If *flag* is not provided, return the current status of the ESPNow
      interface.

      **Returns:**

          ``True`` if interface is currently *active*, else ``False``.

   .. method:: config(**kwargs: int) -> None
               config(param: str, /) -> int

      Set or get configuration values of the ESPNow interface. To set values, use
      the keyword syntax, and one or more parameters can be set at a time. To get
      a value the parameter name should be quoted as a string, and just one
      parameter is queried at a time.

      **Note:** *Getting* parameters is not supported on the ESP8266.

      **Options:**

          *rxbuf*: (default=526) Get/set the size in bytes of the internal
          buffer used to store incoming ESPNow packet data. The default size is
          selected to fit two max-sized ESPNow packets (250 bytes) with associated
          mac_address (6 bytes), a message byte count (1 byte) and RSSI data plus
          buffer overhead. Increase this if you expect to receive a lot of large
          packets or expect bursty incoming traffic.

          **Note:** The recv buffer is allocated by `ESPNow.active()`. Changing
          this value will have no effect until the next call of
          `ESPNow.active(True)<ESPNow.active()>`.

          *timeout_ms*: (default=300,000) Default timeout (in milliseconds)
          for receiving ESPNow messages. If *timeout_ms* is less than zero, then
          wait forever. The timeout can also be provided as arg to
          `recv()`/`irecv()`/`recvinto()`.

          *rate*: (ESP32 only) Set the transmission data rate for ESPNow packets.
          The default setting is `espnow.RATE_1M`. It's recommended to use one of
          the other ``espnow.RATE_nnn`` constants to set this, but it's also
          possible to pass an integer corresponding to the `enum wifi_phy_rate_t
          <https://docs.espressif.com/projects/esp-idf/en/v5.5.1/esp32/
          api-reference/network/esp_wifi.html#_CPPv415wifi_phy_rate_t>`_. This
          parameter is actually *write-only* due to ESP-IDF not providing any
          means for querying the radio interface's rate parameter.
          See also `espnow-long-range`. This API currently doesn't work on ESP32-C6.

      **Returns:**

          ``None`` or the value of the parameter being queried.

      **Raises:**

          - ``OSError(num, "ESP_ERR_ESPNOW_NOT_INIT")`` if not initialised.
          - ``ValueError()`` on invalid configuration options or values.

   .. method:: send(mac: bytes | None, msg: str | bytes, sync: bool = True, /) -> bool
               send(msg: str | bytes, /) -> bool

      Send the data contained in ``msg`` to the peer with given network ``mac``
      address. In the second form, ``mac=None`` and ``sync=True``. The peer must
      be registered with `ESPNow.add_peer()<ESPNow.add_peer()>` before the
      message can be sent.

      **Arguments:**

        - *mac*: byte string exactly ``espnow.ADDR_LEN`` (6 bytes) long or
          ``None``. If *mac* is ``None`` (ESP32 only) the message will be sent
          to all registered peers, except any broadcast or multicast MAC
          addresses.

        - *msg*: string or byte-string up to ``espnow.MAX_DATA_LEN`` (250)
          bytes long.

        - *sync*:

          - ``True``: (default) send ``msg`` to the peer(s) and wait for a
            response (or not).

          - ``False`` send ``msg`` and return immediately. Responses from the
            peers will be discarded.

      **Returns:**

        ``True`` if ``sync=False`` or if ``sync=True`` and *all* peers respond,
        else ``False``.

      **Raises:**

        - ``OSError(num, "ESP_ERR_ESPNOW_NOT_INIT")`` if not initialised.
        - ``OSError(num, "ESP_ERR_ESPNOW_NOT_FOUND")`` if peer is not registered.
        - ``OSError(num, "ESP_ERR_ESPNOW_IF")`` the wifi interface is not
          `active()<network.WLAN.active>`.
        - ``OSError(num, "ESP_ERR_ESPNOW_NO_MEM")`` internal ESP-NOW buffers are
          full.
        - ``ValueError()`` on invalid values for the parameters.

      **Note**: A peer will respond with success if its wifi interface is
      `active()<network.WLAN.active>` and set to the same channel as the sender,
      regardless of whether it has initialised it's ESP-NOW system or is
      actively listening for ESP-NOW traffic (see the Espressif ESP-NOW docs).

   .. method:: recv(timeout_ms: int | None = None, /) -> "list[bytes | None]"

      Wait for an incoming message and return the ``mac`` address of the peer and
      the message. **Note**: It is **not** necessary to register a peer (using
      `add_peer()<ESPNow.add_peer()>`) to receive a message from that peer.

      **Arguments:**

          - *timeout_ms*: (Optional): May have the following values.

            - ``0``: No timeout. Return immediately if no data is available;
            - ``> 0``: Specify a timeout value in milliseconds;
            - ``< 0``: Do not timeout, ie. wait forever for new messages; or
            - ``None`` (or not provided): Use the default timeout value set with
              `ESPNow.config()`.

      **Returns:**

        - ``(None, None)`` if timeout is reached before a message is received, or

        - ``[mac, msg]``: where:

          - ``mac`` is a bytestring containing the address of the device which
            sent the message, and
          - ``msg`` is a bytestring containing the message.

      **Raises:**

        - ``OSError(num, "ESP_ERR_ESPNOW_NOT_INIT")`` if not initialised.
        - ``OSError(num, "ESP_ERR_ESPNOW_IF")`` if the wifi interface is not
          `active()<network.WLAN.active>`.
        - ``ValueError()`` on invalid *timeout_ms* values.

      `ESPNow.recv()` will allocate new storage for the returned list and the
      ``peer`` and ``msg`` bytestrings. This can lead to memory fragmentation if
      the data rate is high. See `ESPNow.irecv()` for a memory-friendly
      alternative.


   .. method:: irecv(timeout_ms: int | None = None, /) -> "list[bytes | bytearray | None]"

      Works like `ESPNow.recv()` but will reuse internal bytearrays to store the
      return values: ``[mac, msg]``, so that no new memory is allocated on each
      call.

      **Arguments:**

          *timeout_ms*: (Optional) Timeout in milliseconds (see `ESPNow.recv()`).

      **Returns:**

        - As for `ESPNow.recv()`, except that ``msg`` is a bytearray, instead of
          a bytestring. On the ESP8266, ``mac`` will also be a bytearray.

      **Raises:**

        - See `ESPNow.recv()`.

      **Note:** You may also read messages by iterating over the ESPNow object,
      which will use the `irecv()` method for alloc-free reads, eg: ::

        import espnow
        e = espnow.ESPNow(); e.active(True)
        for mac, msg in e:
            print(mac, msg)
            if mac is None:   # mac, msg will equal (None, None) on timeout
                break

   .. method:: recvinto(data: list, timeout_ms: int | None = None, /) -> int

      Wait for an incoming message and return the length of the message in bytes.
      This is the low-level method used by both `recv()<ESPNow.recv()>` and
      `irecv()` to read messages.

      **Arguments:**

          *data*: A list of at least two elements, ``[peer, msg]``. ``msg`` must
          be a bytearray large enough to hold the message (250 bytes). On the
          ESP8266, ``peer`` should be a bytearray of 6 bytes. The MAC address of
          the sender and the message will be stored in these bytearrays (see Note
          on ESP32 below).

          *timeout_ms*: (Optional) Timeout in milliseconds (see `ESPNow.recv()`).

      **Returns:**

        - Length of message in bytes or 0 if *timeout_ms* is reached before a
          message is received.

      **Raises:**

        - See `ESPNow.recv()`.

      **Note:** On the ESP32:

      - It is unnecessary to provide a bytearray in the first element of the
        ``data`` list because it will be replaced by a reference to a unique
        ``peer`` address in the **peer device table** (see `ESPNow.peers_table`).
      - If the list is at least 4 elements long, the rssi and timestamp values
        will be saved as the 3rd and 4th elements.

   .. method:: any() -> bool

      Check if data is available to be read with `ESPNow.recv()`.

      For more sophisticated querying of available characters use `select.poll()`::

        import select
        import espnow

        e = espnow.ESPNow()
        poll = select.poll()
        poll.register(e, select.POLLIN)
        poll.poll(timeout)

      **Returns:**

         ``True`` if data is available to be read, else ``False``.

   .. method:: stats() -> tuple[int, int, int, int, int]

      **Returns:**

        A 5-tuple containing the number of packets sent/received/lost:

        ``(tx_pkts, tx_responses, tx_failures, rx_packets, rx_dropped_packets)``

      Incoming packets are *dropped* when the recv buffers are full. To reduce
      packet loss, increase the ``rxbuf`` config parameters and ensure you are
      reading messages as quickly as possible.

      **Note**: Dropped packets will still be acknowledged to the sender as
      received.

   .. method:: set_pmk(pmk: bytes | bytearray | str) -> None

      Set the Primary Master Key (PMK) which is used to encrypt the Local Master
      Keys (LMK) for encrypting messages. If this is not set, a default PMK is
      used by the underlying Espressif ESP-NOW software stack.

      **Note:** messages will only be encrypted if *lmk* is also set in
      `ESPNow.add_peer()` (see `Security
      <https://docs.espressif.com/projects/esp-idf/en/latest/
      esp32/api-reference/network/esp_now.html#security>`_ in the Espressif API
      docs).

      **Arguments:**

        *pmk*: Must be a byte string, bytearray or string of length
        `espnow.KEY_LEN` (16 bytes).

      **Returns:**

        ``None``

      **Raises:**

        ``ValueError()`` on invalid *pmk* values.

   .. method:: add_peer(mac: bytes, lmk: bytes | str | None = None, channel: int | None = None, ifidx: int | None = None, encrypt: bool | None = None, /) -> None
               add_peer(mac: bytes, **kwargs) -> None

      Add/register the provided *mac* address as a peer. Additional parameters may
      also be specified as positional or keyword arguments (any parameter set to
      ``None`` will be set to it's default value):

      **Arguments:**

          - *mac*: The MAC address of the peer (as a 6-byte byte-string).

          - *lmk*: The Local Master Key (LMK) key used to encrypt data
            transfers with this peer (unless the *encrypt* parameter is set to
            ``False``). Must be:

            - a byte-string or bytearray or string of length ``espnow.KEY_LEN``
              (16 bytes), or

            - any non ``True`` python value (default= ``b''``), signifying an
              *empty* key which will disable encryption.

          - *channel*: The wifi channel (2.4GHz) to communicate with this peer.
            Must be an integer from 0 to 14. If channel is set to 0 the current
            channel of the wifi device will be used, if channel is set to another
            value then this must match the channel currently configured on the
            interface (see :func:`WLAN.config`). (default=0)

          - *ifidx*: (ESP32 only) Index of the wifi interface which will be
            used to send data to this peer. Must be an integer set to
            ``network.WLAN.IF_STA`` (=0) or ``network.WLAN.IF_AP`` (=1).
            (default=0/``network.WLAN.IF_STA``). See `ESPNow and Wifi Operation`_
            below for more information.

          - *encrypt*: (ESP32 only) If set to ``True`` data exchanged with
            this peer will be encrypted with the PMK and LMK. (default =
            ``True`` if *lmk* is set to a valid key, else ``False``)

          **ESP8266**: Keyword args may not be used on the ESP8266.

          **Note:** The maximum number of peers which may be registered is 20
          (`espnow.MAX_TOTAL_PEER_NUM`), with a maximum of 6
          (`espnow.MAX_ENCRYPT_PEER_NUM`) of those peers with encryption enabled
          (see `ESP_NOW_MAX_ENCRYPT_PEER_NUM <https://docs.espressif.com/
          projects/esp-idf/en/latest/esp32/api-reference/network/
          esp_now.html#c.ESP_NOW_MAX_ENCRYPT_PEER_NUM>`_ in the Espressif API
          docs).

      **Raises:**

          - ``OSError(num, "ESP_ERR_ESPNOW_NOT_INIT")`` if not initialised.
          - ``OSError(num, "ESP_ERR_ESPNOW_EXIST")`` if *mac* is already
            registered.
          - ``OSError(num, "ESP_ERR_ESPNOW_FULL")`` if too many peers are
            already registered.
          - ``OSError(num, "ESP_ERR_ESPNOW_CHAN")`` if a channel value was
            set that doesn't match the channel currently configured for this
            interface.
          - ``ValueError()`` on invalid keyword args or values.

   .. method:: del_peer(mac: bytes) -> None

      Deregister the peer associated with the provided *mac* address.

      **Returns:**

          ``None``

      **Raises:**

          - ``OSError(num, "ESP_ERR_ESPNOW_NOT_INIT")`` if not initialised.
          - ``OSError(num, "ESP_ERR_ESPNOW_NOT_FOUND")`` if *mac* is not
            registered.
          - ``ValueError()`` on invalid *mac* values.

   .. method:: get_peer(mac: bytes) -> tuple[bytes, bytes, int, int, bool]

      Return information on a registered peer.

      **Returns:**

          ``(mac, lmk, channel, ifidx, encrypt)``: a tuple of the "peer
          info" associated with the given *mac* address.

      **Raises:**

          - ``OSError(num, "ESP_ERR_ESPNOW_NOT_INIT")`` if not initialised.
          - ``OSError(num, "ESP_ERR_ESPNOW_NOT_FOUND")`` if *mac* is not
            registered.
          - ``ValueError()`` on invalid *mac* values.

   .. method:: peer_count() -> tuple[int, int]

      Return the number of registered peers:

      - ``(peer_num, encrypt_num)``: where

        - ``peer_num`` is the number of peers which are registered, and
        - ``encrypt_num`` is the number of encrypted peers.

   .. method:: get_peers() -> tuple[tuple, ...]

      Return the "peer info" parameters for all the registered peers (as a tuple
      of tuples).

   .. method:: mod_peer(mac: bytes, lmk: bytes | str | None, channel: int | None = None, ifidx: int | None = None, encrypt: bool | None = None, /) -> None
               mod_peer(mac: bytes, **kwargs) -> None

      Modify the parameters of the peer associated with the provided *mac*
      address. Parameters may be provided as positional or keyword arguments
      (see `ESPNow.add_peer()`). Any parameter that is not set (or set to
      ``None``) will retain the existing value for that parameter.

   .. method:: irq(callback: Callable[[ESPNow], None] | None) -> None

      Set a callback function to be called *as soon as possible* after a message has
      been received from another ESPNow device. The callback function will be called
      with the `ESPNow` instance object as an argument. For more reliable operation,
      it is recommended to read out as many messages as are available when the
      callback is invoked and to set the read timeout to zero, eg: ::

            def recv_cb(e):
                while True:  # Read out all messages waiting in the buffer
                    mac, msg = e.irecv(0)  # Don't wait if no messages left
                    if mac is None:
                        return
                    print(mac, msg)
            e.irq(recv_cb)

      The `irq()<ESPNow.irq()>` callback method is an alternative method for
      processing incoming messages, especially if the data rate is moderate
      and the device is *not too busy* but there are some caveats:

      - The scheduler stack *can* overflow and callbacks will be missed if
        packets are arriving at a sufficient rate or if other MicroPython components
        (eg, bluetooth, machine.Pin.irq(), machine.timer, i2s, ...) are exercising
        the scheduler stack. This method may be less reliable for dealing with
        bursts of messages, or high throughput or on a device which is busy dealing
        with other hardware operations.

      - For more information on *scheduled* function callbacks see:
        `micropython.schedule()<micropython.schedule>`.

   .. attribute:: peers_table
      :type: dict[bytes, list[int]]

      A reference to the **peer device table**: a dict of known peer devices
      and rssi values::

          {peer: [rssi, time_ms], ...}

      where:

      - ``peer`` is the peer MAC address (as `bytes`);
      - ``rssi`` is the wifi signal strength in dBm (-127 to 0) of the last
        message received from the peer; and
      - ``time_ms`` is the time the message was received (in milliseconds since
        system boot - wraps every 12 days).

      Example::

        >>> e.peers_table
        {b'\xaa\xaa\xaa\xaa\xaa\xaa': [-31, 18372],
         b'\xbb\xbb\xbb\xbb\xbb\xbb': [-43, 12541]}

      **Note**: the ``mac`` addresses returned by `recv()` are references to
      the ``peer`` key values in the **peer device table**.

      **Note**: RSSI and timestamp values in the device table are updated only
      when the message is read by the application.

Constants
---------

.. data:: espnow.MAX_DATA_LEN(=250)
          espnow.KEY_LEN(=16)
          espnow.ADDR_LEN(=6)
          espnow.MAX_TOTAL_PEER_NUM(=20)
          espnow.MAX_ENCRYPT_PEER_NUM(=6)
    :type: int

The following constants correspond to different transmit data rates on ESP32
only. Lower data rates are generally more reliable over long distances:

.. data:: espnow.RATE_LORA_250K
          espnow.RATE_LORA_500K
    :type: int

             See  `espnow-long-range`.

.. data:: espnow.RATE_1M
          espnow.RATE_2M
          espnow.RATE_5M
          espnow.RATE_6M
          espnow.RATE_11M
          espnow.RATE_12M
          espnow.RATE_24M
          espnow.RATE_54M
    :type: int

Unless using the two proprietary long range data rates, only the sender must
configure the data rate.

.. _espnow-long-range:

Long Range Mode
---------------

(ESP32 Only, except ESP32-C2)

To use the `espnow.RATE_LORA_250K` and `espnow.RATE_LORA_500K` data rates,
first set the `WLAN` interface object to long-range mode, i.e.::

  import network, espnow
  sta = network.WLAN(network.WLAN.IF_STA)
  sta.active(True)
  sta.config(channel=6, protocol=WLAN.PROTOCOL_LR)  # Set on sender & receiver
  e = espnow.ESPNow()
  e.config(rate=espnow.RATE_LORA_250K)  # Needed on sender only

For more information about the limitations of long-range mode, see `WLAN.PROTOCOL_LR`.

Exceptions
----------

If the underlying Espressif ESP-NOW software stack returns an error code,
the MicroPython espnow module will raise an ``OSError(errnum, errstring)``
exception where ``errstring`` is set to the name of one of the error codes
identified in the
`Espressif ESP-NOW docs
<https://docs.espressif.com/projects/esp-idf/en/latest/
api-reference/network/esp_now.html#api-reference>`_. For example::

    try:
        e.send(peer, 'Hello')
    except OSError as err:
        if len(err.args) < 2:
            raise err
        if err.args[1] == 'ESP_ERR_ESPNOW_NOT_INIT':
            e.active(True)
        elif err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
            e.add_peer(peer)
        elif err.args[1] == 'ESP_ERR_ESPNOW_IF':
            network.WLAN(network.WLAN.IF_STA).active(True)
        else:
            raise err

Wifi Signal Strength (RSSI) - (ESP32 only)
------------------------------------------

The ESPNow object maintains a **peer device table** which contains the signal
strength and timestamp of the last received message from all hosts. The **peer
device table** can be accessed using `ESPNow.peers_table` and can be used to
track device proximity and identify *nearest neighbours* in a network of peer
devices. This feature is **not** available on ESP8266 devices.

Supporting asyncio
------------------

A supplementary module (`aioespnow`) is available to provide
:doc:`asyncio<asyncio>` support.

**Note:** Asyncio support is available on all ESP32 targets as well as those
ESP8266 boards which include the asyncio module (ie. ESP8266 devices with at
least 2MB flash memory).

A small async server example::

    import network
    import aioespnow
    import asyncio

    # A WLAN interface must be active to send()/recv()
    network.WLAN(network.WLAN.IF_STA).active(True)

    e = aioespnow.AIOESPNow()  # Returns AIOESPNow enhanced with async support
    e.active(True)
    peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'
    e.add_peer(peer)

    # Send a periodic ping to a peer
    async def heartbeat(e, peer, period=30):
        while True:
            if not await e.asend(peer, b'ping'):
                print("Heartbeat: peer not responding:", peer)
            else:
                print("Heartbeat: ping", peer)
            await asyncio.sleep(period)

    # Echo any received messages back to the sender
    async def echo_server(e):
        async for mac, msg in e:
            print("Echo:", msg)
            try:
                await e.asend(mac, msg)
            except OSError as err:
                if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                    e.add_peer(mac)
                    await e.asend(mac, msg)

    async def main(e, peer, timeout, period):
        asyncio.create_task(heartbeat(e, peer, period))
        asyncio.create_task(echo_server(e))
        await asyncio.sleep(timeout)

    asyncio.run(main(e, peer, 120, 10))

.. module:: aioespnow
    :synopsis: ESP-NOW :doc:`asyncio` support

.. class:: AIOESPNow()

    The `AIOESPNow` class inherits all the methods of `ESPNow<espnow.ESPNow>`
    and extends the interface with the following async methods.

   .. method:: async arecv() -> "list[bytes | None]"

      Asyncio support for `ESPNow.recv()`. Note that this method does not take a
      timeout value as argument.

   .. method:: async airecv() -> "list[bytes | bytearray | None]"

      Asyncio support for `ESPNow.irecv()`. Note that this method does not take a
      timeout value as argument.

   .. method:: async asend(mac: bytes | None, msg: str | bytes, sync: bool = True) -> bool
               async asend(msg: str | bytes) -> bool

      Asyncio support for `ESPNow.send()`.

   .. method:: __aiter__() -> AIOESPNow
               async __anext__() -> "tuple[bytes, bytes]"

      `AIOESPNow` also supports reading incoming messages by asynchronous
      iteration using ``async for``; eg::

        e = AIOESPNow()
        e.active(True)
        async def recv_till_halt(e):
            async for mac, msg in e:
                print(mac, msg)
                if msg == b'halt':
                  break
        asyncio.run(recv_till_halt(e))

Broadcast and Multicast
-----------------------

All active ESPNow clients will receive messages sent to their MAC address and
all devices (**except ESP8266 devices**) will also receive messages sent to the
*broadcast* MAC address (``b'\xff\xff\xff\xff\xff\xff'``) or any multicast
MAC address.

All ESPNow devices (including ESP8266 devices) can also send messages to the
broadcast MAC address or any multicast MAC address.

To `send()<ESPNow.send()>` a broadcast message, the broadcast (or
multicast) MAC address must first be registered using
`add_peer()<ESPNow.add_peer()>`. `send()<ESPNow.send()>` will always return
``True`` for broadcasts, regardless of whether any devices receive the
message. It is not permitted to encrypt messages sent to the broadcast
address or any multicast address.

**Note**: `ESPNow.send(None, msg)<ESPNow.send()>` will send to all registered
peers *except* the broadcast address. To send a broadcast or multicast
message, you must specify the broadcast (or multicast) MAC address as the
peer. For example::

    bcast = b'\xff' * 6
    e.add_peer(bcast)
    e.send(bcast, "Hello World!")

ESPNow and Wifi Operation
-------------------------

ESPNow messages may be sent and received on any `active()<network.WLAN.active>`
`WLAN<network.WLAN()>` interface (``network.WLAN.IF_STA`` or ``network.WLAN.IF_AP``),
even if that interface is also connected to a wifi network or configured as an access
point. When an ESP32 or ESP8266 device connects to a Wifi Access Point (see
`ESP32 Quickref <../esp32/quickref.html#networking>`__) the following things
happen which affect ESPNow communications:

1. Wifi Power-saving Mode (`network.WLAN.PM_PERFORMANCE`)
   is automatically activated and
2. The radio on the esp device changes wifi ``channel`` to match the channel
   used by the Access Point.

**Wifi Power-saving Mode:** (see `Espressif Docs <https://docs.espressif.com/
projects/esp-idf/en/latest/esp32/api-guides/
wifi.html#esp32-wi-fi-power-saving-mode>`_) The power saving mode causes the
device to turn off the radio periodically (typically for hundreds of
milliseconds), making it unreliable in receiving ESPNow messages. This can be
resolved by either of:

1. Disabling the power-saving mode on the STA_IF interface;

   - Use ``sta.config(pm=sta.PM_NONE)``

2. Turning on the AP_IF interface, which will disable the power saving mode.
   However, the device will then be advertising an active wifi access point.

   - You **may** also choose to send your messages via the AP_IF interface, but
     this is not necessary.
   - ESP8266 peers must send messages to this AP_IF interface (see below).

3. Configuring ESPNow clients to retry sending messages.

**Receiving messages from an ESP8266 device:** Strangely, an ESP32 device
connected to a wifi network using method 1 or 2 above, will receive ESPNow
messages sent to the STA_IF MAC address from another ESP32 device, but will
**reject** messages from an ESP8266 device!!!. To receive messages from an
ESP8266 device, the AP_IF interface must be set to ``active(True)`` **and**
messages must be sent to the AP_IF MAC address.

**Managing wifi channels:** Any other ESPNow devices wishing to communicate with
a device which is also connected to a Wifi Access Point MUST use the same
channel. A common scenario is where one ESPNow device is connected to a wifi
router and acts as a proxy for messages from a group of sensors connected via
ESPNow:

**Proxy:** ::

  import network, time, espnow

  sta, ap = wifi_reset()  # Reset wifi to AP off, STA on and disconnected
  sta.connect('myssid', 'mypassword')
  while not sta.isconnected():  # Wait until connected...
      time.sleep(0.1)
  sta.config(pm=sta.PM_NONE)  # ..then disable power saving

  # Print the wifi channel used AFTER finished connecting to access point
  print("Proxy running on channel:", sta.config("channel"))
  e = espnow.ESPNow(); e.active(True)
  for peer, msg in e:
      # Receive espnow messages and forward them to MQTT broker over wifi

**Sensor:** ::

  import network, espnow

  sta, ap = wifi_reset()   # Reset wifi to AP off, STA on and disconnected
  sta.config(channel=6)    # Change to the channel used by the proxy above.
  peer = b'0\xaa\xaa\xaa\xaa\xaa'  # MAC address of proxy
  e = espnow.ESPNow(); e.active(True);
  e.add_peer(peer)
  while True:
      msg = read_sensor()
      e.send(peer, msg)
      time.sleep(1)

Other issues to take care with when using ESPNow with wifi are:

- **Set WIFI to known state on startup:** MicroPython does not reset the wifi
  peripheral after a soft reset. This can lead to unexpected behaviour. To
  guarantee the wifi is reset to a known state after a soft reset make sure you
  deactivate the STA_IF and AP_IF before setting them to the desired state at
  startup, eg.::

    import network, time

    def wifi_reset():   # Reset wifi to AP_IF off, STA_IF on and disconnected
      sta = network.WLAN(network.WLAN.IF_STA); sta.active(False)
      ap = network.WLAN(network.WLAN.IF_AP); ap.active(False)
      sta.active(True)
      while not sta.active():
          time.sleep(0.1)
      sta.disconnect()   # For ESP8266
      while sta.isconnected():
          time.sleep(0.1)
      return sta, ap

    sta, ap = wifi_reset()

  Remember that a soft reset occurs every time you connect to the device REPL
  and when you type ``ctrl-D``.

- **STA_IF and AP_IF always operate on the same channel:** the AP_IF will change
  channel when you connect to a wifi network; regardless of the channel you set
  for the AP_IF (see `Attention Note 3
  <https://docs.espressif.com/
  projects/esp-idf/en/latest/esp32/api-reference/network/esp_wifi.html
  #_CPPv419esp_wifi_set_config16wifi_interface_tP13wifi_config_t>`_
  ). After all, there is really only one wifi radio on the device, which is
  shared by the STA_IF and AP_IF virtual devices.

- **Disable automatic channel assignment on your wifi router:** If the wifi
  router for your wifi network is configured to automatically assign the wifi
  channel, it may change the channel for the network if it detects interference
  from other wifi routers. When this occurs, the ESP devices connected to the
  wifi network will also change channels to match the router, but other
  ESPNow-only devices will remain on the previous channel and communication will
  be lost. To mitigate this, either set your wifi router to use a fixed wifi
  channel or configure your devices to re-scan the wifi channels if they are
  unable to find their expected peers on the current channel.

- **MicroPython re-scans wifi channels when trying to reconnect:** If the esp
  device is connected to a Wifi Access Point that goes down, MicroPython will
  automatically start scanning channels in an attempt to reconnect to the
  Access Point. This means ESPNow messages will be lost while scanning for the
  AP. This can be disabled by ``sta.config(reconnects=0)``, which will also
  disable the automatic reconnection after losing connection.

- Some versions of the ESP IDF only permit sending ESPNow packets from the
  STA_IF interface to peers which have been registered on the same wifi
  channel as the STA_IF::

    ESPNOW: Peer channel is not equal to the home channel, send fail!

ESPNow and Sleep Modes
----------------------

The `machine.lightsleep([time_ms])<machine.lightsleep>` and
`machine.deepsleep([time_ms])<machine.deepsleep>` functions can be used to put
the ESP32 and peripherals (including the WiFi and Bluetooth radios) to sleep.
This is useful in many applications to conserve battery power. However,
applications must disable the WLAN peripheral (using
`active(False)<network.WLAN.active>`) before entering light or deep sleep (see
`Sleep Modes <https://docs.espressif.com/
projects/esp-idf/en/latest/esp32/api-reference/system/sleep_modes.html>`_).
Otherwise the WiFi radio may not be initialised properly after wake from
sleep. If the ``STA_IF`` and ``AP_IF`` interfaces have both been set
`active(True)<network.WLAN.active()>` then both interfaces should be set
`active(False)<network.WLAN.active()>` before entering any sleep mode.

**Example:** deep sleep::

  import network, machine, espnow

  sta, ap = wifi_reset()            # Reset wifi to AP off, STA on and disconnected
  peer = b'0\xaa\xaa\xaa\xaa\xaa'   # MAC address of peer
  e = espnow.ESPNow()
  e.active(True)
  e.add_peer(peer)                  # Register peer on STA_IF

  print('Sending ping...')
  if not e.send(peer, b'ping'):
    print('Ping failed!')
  e.active(False)
  sta.active(False)                 # Disable the wifi before sleep
  print('Going to sleep...')
  machine.deepsleep(10000)          # Sleep for 10 seconds then reboot

**Example:** light sleep::

  import network, machine, espnow

  sta, ap = wifi_reset()            # Reset wifi to AP off, STA on and disconnected
  sta.config(channel=6)
  peer = b'0\xaa\xaa\xaa\xaa\xaa'   # MAC address of peer
  e = espnow.ESPNow()
  e.active(True)
  e.add_peer(peer)                  # Register peer on STA_IF

  while True:
    print('Sending ping...')
    if not e.send(peer, b'ping'):
      print('Ping failed!')
    sta.active(False)               # Disable the wifi before sleep
    print('Going to sleep...')
    machine.lightsleep(10000)       # Sleep for 10 seconds
    sta.active(True)
    sta.config(channel=6)           # Wifi loses config after lightsleep()
