# micropython_mpu6050
MicroPython driver for MPU6050 sensor with extended functionality

Copyright (c) 2026 Alex Yeryomin

A simple class for MicroPython to control well-known MPU6050 module.
You can find many libraries for this module, however, this one,
besides common methods to read gyros and accelemometers, allows
to setup MPU6050 module as Motion Detection sensor. In this mode,
the module generates the interrupt when a motion of specific amount
and duration is detected.

This code uses prealocated buffers and memory views, which makes
much faster than other implementations I found online. I have tested
on ESP32-D1, ESP32-S2, ESP32-C3, Raspberry Pico, WeMos W600.

Only registers and flags that are necessary to implement
the required fuctionality are listed below. For the full list
of available registres, see the datasheet for MPU6050.
The best available resource about MPU6050 can be found here:
https://www.i2cdevlib.com/devices/mpu6050 (by Jeff Rowberg)
