# Copyright (c) 2026 Alex Yeryomin
#
# A program to demonstrate using MPU6050 class to setup MPU6050
# module as Motion Detection sensor. ESP32 falls into a deep sleep
# waiting for a single from MPU6050 to wake up.

import esp32
import machine
from machine import Pin, I2C
from time import sleep, time, ticks_ms, ticks_diff
from mpu6050_irq import MPU6050

wokeFromDeepSleep = machine.reset_cause() == machine.DEEPSLEEP_RESET

ledR = Pin(34, Pin.OUT, value=wokeFromDeepSleep)
ledG = Pin(21, Pin.OUT, value=not wokeFromDeepSleep)

if wokeFromDeepSleep:
    # Process motion detection event.
    sleep(5)
    ledR.off()
    ledG.on()

wakeIRQ = Pin(14, Pin.IN) # Any RTC pin to catch the interrupt.
esp32.wake_on_ext0(wakeIRQ, esp32.WAKEUP_ANY_HIGH)

i2c = I2C(0, sda=Pin(5), scl=Pin(3), freq=400000)

imu = MPU6050(i2c)
imu.wake()
imu.setupMotionDetection(4, 16) # To detect a small, short movements like a knock.
imu.enableMotionDetectionIRQ()  # Might rise IRQ immediately when enabled.

# If motion detection is enabled with the latch, reset the latch.
# motionDetected = imu.resetMotionDetectionLatch() & MOT_INT

print("going to sleep in 5 s...")
sleep(5) 
machine.deepsleep()
