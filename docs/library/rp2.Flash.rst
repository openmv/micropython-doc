.. currentmodule:: rp2
.. _rp2.Flash:

class Flash -- access to built-in flash storage
===============================================

This class gives access to the SPI flash memory.

In most cases, to store persistent data on the device, you'll want to use a
higher-level abstraction, for example the filesystem via Python's standard file
API, but this interface is useful to :ref:`customise the filesystem
configuration <filesystem>` or implement a low-level storage system for your
application.


Constructors
------------

.. class:: Flash()

   Gets the singleton object for accessing the SPI flash memory.

   .. method:: readblocks(block_num: int, buf: bytearray) -> None
               readblocks(block_num: int, buf: bytearray, offset: int) -> None
   .. method:: writeblocks(block_num: int, buf: bytes) -> None
               writeblocks(block_num: int, buf: bytes, offset: int) -> None
   .. method:: ioctl(cmd: int, arg: int) -> int | None

      These methods implement the simple and extended
      :ref:`block protocol <block-device-interface>` defined by
      :class:`vfs.AbstractBlockDev`.
