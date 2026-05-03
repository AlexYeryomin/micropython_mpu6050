# Copyright (c) 2026 Alex Yeryomin
#
# A program to demonstrate using MPU6050 class to read accelaration.
# The simplest code to test the sensor.

from machine import Pin, I2C
from time import sleep
from mpu6050_irq import MPU6050

i2c = I2C(0, sda=Pin(5), scl=Pin(3), freq=400000)

imu = MPU6050(i2c)
imu.wake()
imu.setAccelRange(3)

while True:
    acc = imu.readAccelData()
    print(acc)
    sleep(0.1)
