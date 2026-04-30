.. currentmodule:: rp2
.. _rp2.PIO:

class PIO -- advanced PIO usage
===============================

The :class:`PIO` class gives access to an instance of the RP2040's PIO
(programmable I/O) interface.

The preferred way to interact with PIO is using :class:`rp2.StateMachine`, the
PIO class is for advanced use.

For assembling PIO programs, see :func:`rp2.asm_pio`.


Constructors
------------

.. class:: PIO(id: int)

    Gets the PIO instance numbered *id*. The RP2040 has two PIO instances,
    numbered 0 and 1.

    Raises a ``ValueError`` if any other argument is provided.

   .. method:: gpio_base(base: Pin | int | None = None, /) -> int

      Query and optionally set the current GPIO base for this PIO instance.

      If an argument is given then it must be a pin (or integer corresponding to a pin
      number), restricted to either GPIO0 or GPIO16.  The GPIO base will then be set to
      that pin.  Setting the GPIO base must be done before any programs are added or state
      machines created.

      Returns the current GPIO base pin.

   .. method:: add_program(program: Callable) -> None

      Add the *program* to the instruction memory of this PIO instance.

      The amount of memory available for programs on each PIO instance is
      limited. If there isn't enough space left in the PIO's program memory
      this method will raise ``OSError(ENOMEM)``.

   .. method:: remove_program(program: Callable | None = None, /) -> None

      Remove *program* from the instruction memory of this PIO instance.

      If no program is provided, it removes all programs.

      It is not an error to remove a program which has already been removed.

   .. method:: state_machine(id: int, program: Callable | None = None, *args, **kwargs) -> StateMachine

      Gets the state machine numbered *id*. On the RP2040, each PIO instance has
      four state machines, numbered 0 to 3.

      Optionally initialize it with a *program*: see `StateMachine.init`.

      >>> rp2.PIO(1).state_machine(3)
      StateMachine(7)

   .. method:: irq(handler: Callable[[PIO], None] | None = None, trigger: int = IRQ_SM0 | IRQ_SM1 | IRQ_SM2 | IRQ_SM3, hard: bool = False) -> Callable

      Returns the IRQ object for this PIO instance.

      MicroPython only uses IRQ 0 on each PIO instance. IRQ 1 is not available.

      Optionally configure it.

   .. data:: IN_LOW
             IN_HIGH
             OUT_LOW
             OUT_HIGH
      :type: int

      These constants are used for the *out_init*, *set_init*, and *sideset_init*
      arguments to `asm_pio`.

   .. data:: SHIFT_LEFT
             SHIFT_RIGHT
      :type: int

      These constants are used for the *in_shiftdir* and *out_shiftdir* arguments
      to `asm_pio` or `StateMachine.init`.

   .. data:: JOIN_NONE
             JOIN_TX
             JOIN_RX
      :type: int

      These constants are used for the *fifo_join* argument to `asm_pio`.

   .. data:: IRQ_SM0
             IRQ_SM1
             IRQ_SM2
             IRQ_SM3
      :type: int

      These constants are used for the *trigger* argument to `PIO.irq`.
