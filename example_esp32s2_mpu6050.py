# Copyright (c) 2026 Alex Yeryomin
#
# A program to demonstrate using MPU6050_IRQ class to setup MPU6050
# module as Motion Detection sensor.

import machine
from machine import Pin, I2C
from time import sleep, time, ticks_ms, ticks_diff
from mpu6050_irq import MPU6050

ledR = Pin(34, Pin.OUT, value=0)
ledG = Pin(21, Pin.OUT, value=1)

motionDetected = False

def imuHandler(pin):
    global motionDetected
    # If motion detection is enabled with the latch,
    # reset the latch and check the reason of IRQ.
    # motionDetected = imu.resetMotionDetectionLatch() & MOT_INT
    motionDetected = True

imuIRQ = Pin(14, Pin.IN) # Any pin to catch the interrupt.
imuIRQ.irq(trigger=Pin.IRQ_RISING, handler=imuHandler)

i2c = I2C(0, sda=Pin(5), scl=Pin(3), freq=400000)

imu = MPU6050(i2c)
imu.wake()
imu.setupMotionDetection(4, 16) # To detect a small, short movements like a knock.
imu.enableMotionDetectionIRQ()  # Might rise IRQ immediately when enabled.

print("Start.")

tLastDetected = ticks_ms()
while True:
    now = ticks_ms()
    if motionDetected:
        print("Motion detected.")
        motionDetected = False # Not the best way to sync, but for the demo it's fine.
        ledG.off()        
        ledR.on()        
        print(imu.readGyroData(), imu.readAccelData())
        tLastDetected = now
    elif ticks_diff(now, tLastDetected) > 1000:
        ledR.off()        
        ledG.on()
    sleep(0.1) # Non necessary to update frequently.
