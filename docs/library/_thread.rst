:mod:`_thread` --- multithreading support
=========================================

.. module:: _thread
   :synopsis: multithreading support

This module provides low-level primitives for working with multiple threads
of execution: spawning new threads, querying the current thread identifier,
and creating mutex locks for synchronisation.  It is intended as a foundation
for higher-level threading abstractions.

A thread, once started, executes independently from the thread that spawned it.
There is no built-in way to join, cancel, or otherwise interact with a running
thread; synchronisation must be performed explicitly using lock objects.

Functions
---------

.. function:: start_new_thread(function: Callable[..., Any], args: tuple, kwargs: dict | None = None) -> int

   Start a new thread that runs ``function(*args, **kwargs)`` and return its
   integer thread identifier.  *args* must be a tuple of positional arguments;
   *kwargs*, if given, must be a dict of keyword arguments.

   If the thread terminates with an unhandled exception (other than
   :exc:`SystemExit`), a traceback is printed and the thread exits.

.. function:: exit() -> None

   Raise :exc:`SystemExit` in the calling thread, terminating it.  This has
   the same effect as ``raise SystemExit``.

.. function:: get_ident() -> int

   Return the integer "thread identifier" of the current thread.  The value
   has no direct meaning beyond identifying a particular thread for the
   lifetime of that thread.

.. function:: allocate_lock() -> Lock

   Return a new lock object (initially unlocked).  See the :class:`Lock`
   class below for details.

.. function:: stack_size(size: int = 0, /) -> int

   Return the thread stack size used when creating new threads.  The optional
   *size* argument sets the stack size, in bytes, to be used for subsequently
   created threads; a value of ``0`` selects the platform default.  The
   previous value is returned.

Lock objects
------------

.. class:: Lock

   A primitive mutex (mutual exclusion) lock.  When locked, it belongs to
   the thread that locked it; when unlocked, it does not belong to any
   thread.  Lock objects are created via :func:`allocate_lock` and cannot
   be instantiated directly.

   Lock objects support the context manager protocol: using a lock with the
   ``with`` statement acquires it on entry and releases it on exit.

   .. method:: acquire(blocking: bool = True, /) -> bool

      Acquire the lock.  If *blocking* is true (the default), block until
      the lock is available, then take it and return ``True``.  If
      *blocking* is false, return ``True`` immediately if the lock could
      be taken, or ``False`` if it could not.

   .. method:: release() -> None

      Release the lock, allowing another thread that is blocked waiting
      for it to proceed.  The lock must be held by the calling thread;
      calling :meth:`release` on an unlocked lock raises :exc:`RuntimeError`.

   .. method:: locked() -> bool

      Return ``True`` if the lock is currently held by some thread, and
      ``False`` otherwise.
