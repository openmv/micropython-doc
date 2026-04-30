.. currentmodule:: zsensor

:mod:`zsensor` --- Zephyr sensor bindings
=========================================

.. module:: zsensor
    :synopsis: zephyr sensor bindings

The ``zsensor`` module contains a class for using sensors with Zephyr.

.. _zsensor.Sensor:

class Sensor --- sensor control for the Zephyr port
---------------------------------------------------

Use this class to access data from sensors on your board.
See Zephyr documentation for sensor usage here: `Sensors
<https://docs.zephyrproject.org/latest/reference/peripherals/sensor.html?highlight=sensor#sensors>`_.

Sensors are defined in the Zephyr devicetree for each board. The quantities that a given sensor can
measure are called a sensor channels. Sensors can have multiple channels to represent different axes
of one property or different properties a sensor can measure. See `Channels`_ below for defined sensor
channels. Each channel may have multiple attributes that can be changed and/or queried.
See `Channel Attributes`_ below for defined sensor channel attributes.

Constructor
~~~~~~~~~~~

.. class:: Sensor(device_name: str)

    Device names are defined in the devicetree for your board.
    For example, the device name for the accelerometer in the FRDM-k64f board is "FXOS8700".

   .. method:: measure() -> None

      Obtains a measurement sample from the sensor device using Zephyr sensor_sample_fetch and
      stores it in an internal driver buffer as a useful value, a pair of (integer part of value,
      fractional part of value in 1-millionths).
      Returns none if successful or OSError value if failure.

   .. method:: get_float(sensor_channel: int) -> float

      Returns the value of the sensor measurement sample as a float.

   .. method:: get_micros(sensor_channel: int) -> int

      Returns the value of the sensor measurement sample in millionths.
      (Ex. value of ``(1, 500000)`` returns as ``1500000``)

   .. method:: get_millis(sensor_channel: int) -> int

      Returns the value of sensor measurement sample in thousandths.
      (Ex. value of ``(1, 500000)`` returns as ``1500``)

   .. method:: get_int(sensor_channel: int) -> int

      Returns only the integer value of the measurement sample.
      (Ex. value of ``(1, 500000)`` returns as ``1``)

   .. method:: attr_set(sensor_channel: int, channel_attribute: int, val1: float | int, val2: int | None = None, /) -> None

      Set the given channel's attribute to the given value.
      ``val1`` may be a float, in which case ``val2`` is not given, or
      ``val1`` can be used for the value's
      integer part and ``val2`` for the value's fractional part in millionths.

      Returns ``None`` if successful, or raises ``OSError``.

   .. method:: attr_get_float(sensor_channel: int, channel_attribute: int) -> float

      Returns the value of the sensor channel's attribute as a float.

      Many sensors do not support this or any other of the ``attr_get`` methods.

   .. method:: attr_get_micros(sensor_channel: int, channel_attribute: int) -> int

      Returns the value of the sensor channel's attribute in millionths.
      (Ex. value of ``(1, 500000)`` returns as ``1500000``)

   .. method:: attr_get_millis(sensor_channel: int, channel_attribute: int) -> int

      Returns the value of the sensor channel's attribute in thousandths.
      (Ex. value of ``(1, 500000)`` returns as ``1500``)

   .. method:: attr_get_int(sensor_channel: int, channel_attribute: int) -> int

      Returns only the integer value of the channel's attribute.
      (Ex. value of ``(1, 500000)`` returns as ``1``)

Channels
~~~~~~~~

.. data:: ACCEL_X
    :type: int

    Acceleration on the X axis, in m/s^2.

.. data:: ACCEL_Y
    :type: int

    Acceleration on the Y axis, in m/s^2.

.. data:: ACCEL_Z
    :type: int

    Acceleration on the Z axis, in m/s^2.

.. data:: ACCEL_XYZ
    :type: int

    Pseudo-channel representing all three accelerometer axes.
    Used for :meth:`Sensor.attr_set` and the ``Sensor.attr_get_xxx()`` methods.

.. data:: GYRO_X
    :type: int

    Angular velocity around the X axis, in radians/s.

.. data:: GYRO_Y
    :type: int

    Angular velocity around the Y axis, in radians/s.

.. data:: GYRO_Z
    :type: int

    Angular velocity around the Z axis, in radians/s.

.. data:: GYRO_XYZ
    :type: int

    Pseudo-channel representing all three gyroscope axes.
    Used for :meth:`Sensor.attr_set` and the ``Sensor.attr_get_xxx()`` methods.

.. data:: MAGN_X
    :type: int

    Magnetic field on the X axis, in Gauss.

.. data:: MAGN_Y
    :type: int

    Magnetic field on the Y axis, in Gauss.

.. data:: MAGN_Z
    :type: int

    Magnetic field on the Z axis, in Gauss.

.. data:: DIE_TEMP
    :type: int

    Device die temperature in degrees Celsius.

.. data:: PRESS
    :type: int

    Pressure in kilopascal.

.. data:: PROX
    :type: int

    Proximity. Dimensionless. A value of 1 indicates that an object is close.

.. data:: HUMIDITY
    :type: int

    Humidity, in percent.

.. data:: LIGHT
    :type: int

    Illuminance in visible spectrum, in lux.

.. data:: ALTITUDE
    :type: int

    Altitude, in meters.

Channel Attributes
~~~~~~~~~~~~~~~~~~~

.. data:: ATTR_SAMPLING_FREQUENCY
    :type: int

    Sensor sampling frequency, i.e. how many times a second the sensor takes a measurement.

.. data:: ATTR_LOWER_THRESH
    :type: int

    Lower threshold for trigger.

.. data:: ATTR_UPPER_THRESH
    :type: int

    Upper threshold for trigger.

.. data:: ATTR_SLOPE_TH
    :type: int

    Threshold for any-motion (slope) trigger.

.. data:: ATTR_SLOPE_DUR
    :type: int

    Duration for which the slope values needs to be outside the threshold for the trigger to fire.

.. data:: ATTR_HYSTERESIS
    :type: int

    Hysteresis applied to the slope/threshold trigger to prevent rapid retriggering when
    the measured value is near the threshold.

.. data:: ATTR_OVERSAMPLING
    :type: int

    Oversampling factor.

.. data:: ATTR_FULL_SCALE
    :type: int

    Sensor range, in SI units.

.. data:: ATTR_OFFSET
    :type: int

    The sensor value returned will be altered by the amount indicated by offset: final_value = sensor_value + offset.

.. data:: ATTR_CALIB_TARGET
    :type: int

    Calibration target. This will be used by the internal chip's algorithms to calibrate itself on a certain axis, or all of them.

.. data:: ATTR_CONFIGURATION
    :type: int

    Configure the operating modes of a sensor.

.. data:: ATTR_CALIBRATION
    :type: int

    Set a calibration value needed by a sensor.

.. data:: ATTR_FEATURE_MASK
    :type: int

    Enable/disable sensor features.

.. data:: ATTR_ALERT
    :type: int

    Alert threshold or alert enable/disable.

.. data:: ATTR_FF_DUR
    :type: int

    Free-fall duration represented in milliseconds.
    If the sampling frequency is changed during runtime, this attribute should be set to adjust freefall duration to the new sampling frequency.

.. data:: ATTR_BATCH_DURATION
    :type: int

    Hardware batch duration in ticks.

.. data:: ATTR_GAIN
    :type: int

    Sensor gain setting, used to scale the raw measurement to the desired output range.

.. data:: ATTR_RESOLUTION
    :type: int

    Sensor resolution setting, controlling the number of bits used to represent
    each measurement.
