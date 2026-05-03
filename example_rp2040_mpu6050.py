# Copyright (c) 2026 Alex Yeryomin
#
# A program to demonstrate using MPU6050 class to setup MPU6050
# module as Motion Detection sensor.

from machine import Pin, I2C
from time import sleep, time, ticks_ms, ticks_diff
from mpu6050_irq import MPU6050

led = Pin(25, Pin.OUT, value=0) # PICO PI (RP2040)

motionDetected = False

def imuHandler(pin):
    global motionDetected
    # If motion detection is enabled with the latch,
    # reset the latch and check the reason of IRQ.
    # motionDetected = imu.resetMotionDetectionLatch() & MOT_INT
    motionDetected = True

imuIRQ = Pin(13, Pin.IN) # Any pin to catch the interrupt.
imuIRQ.irq(trigger=Pin.IRQ_RISING, handler=imuHandler, hard=True)

i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
imu = MPU6050(i2c)
print(imu.readGyroData(), imu.readAccelData())

imu.setupMotionDetection(8, 16) # To detect a small, short movements like a knock.
imu.enableMotionDetectionIRQ()  # Might rise IRQ immediately when enabled.

tLastDetected = ticks_ms()
while True:
    now = ticks_ms()
    if motionDetected:
        motionDetected = False # Not the best way to sync, but for the demo it's fine.
        led.on()
        print(imu.readGyroData(), imu.readAccelData())
        tLastDetected = now
    elif ticks_diff(now, tLastDetected) > 1000:
        led.off()
    sleep(0.1) # Non necessary to update frequently.
