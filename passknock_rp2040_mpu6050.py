# Copyright (c) 2026 Alex Yeryomin
#
# A program to demonstrate using MPU6050 class to setup MPU6050
# module as Motion Detection sensor.

from machine import Pin, I2C
from time import sleep, sleep_ms, time, ticks_ms, ticks_us, ticks_diff
from mpu6050_irq import MPU6050, MOT_INT

led = Pin(25, Pin.OUT, value=0) # PICO PI (RP2040)

motionDetectedTime = None

def imuHandler(pin):
    global motionDetectedTime
    motionDetectedTime = ticks_ms()
        
imuIRQ = Pin(13, Pin.IN) # Any pin to catch the interrupt.
imuIRQ.irq(trigger=Pin.IRQ_RISING, handler=imuHandler)

i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
imu = MPU6050(i2c)
imu.wake()
imu.setupMotionDetection(12, 16, latchEnabled=True) # To detect a small, short movements like a knock.
imu.enableMotionDetectionIRQ() # Rises IRQ immediately when enabled.
time_ms = ticks_ms()
while not motionDetectedTime and ticks_diff(ticks_ms(), time_ms) < 500:
    pass
imu.resetMotionDetectionLatch()

def recordPassKnock(debounce_ms=50, timeout_s=5):
    global motionDetectedTime
    timeout_ms = timeout_s * 1000
    knocksTimes = []
    tLastDetected = ticks_ms()
    led.off()
    imu.disableMotionDetectionIRQ()
    motionDetectedTime = None
    imu.resetMotionDetectionLatch()
    imu.enableMotionDetectionIRQ()
    while True:
        if motionDetectedTime:
            # A proper synchronization is done by keeping the time first, reset the time,
            # and only then release the latch to enable the motion detection again. 
            knocksTimes.append(motionDetectedTime)
            tLastDetected = motionDetectedTime
            motionDetectedTime = None
            led.on() # Confirm the knock.
            sleep_ms(debounce_ms)
            led.off()
            imu.resetMotionDetectionLatch()
        elif ticks_diff(ticks_ms(), tLastDetected) > timeout_ms:
            break

    for i in range(len(knocksTimes) - 1):
        knocksTimes[i] = ticks_diff(knocksTimes[i+1], knocksTimes[i])
    return knocksTimes[:-1]
    
def waitForPassKnock(minPassknockSize=2):
    while True:
        print(f"Knock your password to record (at least {minPassknockSize + 1} knocks required)")
        passknock = recordPassKnock()
        passknockLen = len(passknock)
        if passknockLen >= minPassknockSize:
            print("Passknock has been recorded")
            return passknock
        elif passknockLen > 0:
            print("Passknock is too weak, try again")

def checkPassKnock(passknock, testknonk, tolerance_ms=100):
    if len(passknock) != len(testknonk):
        return False
    for i in range(len(passknock)):
        if abs(passknock[i] - testknonk[i]) > tolerance_ms:
            return False
    return True

def unlockByPassKnock(passknock):
    while True:
        print(f"Knock your password to unlock your account")
        testknock = recordPassKnock()
        if checkPassKnock(passknock, testknock):
            print("You have successfully logged in")
            break
        print("Wrong passknock")


# One one thousand, two one thousand, three one thousand, four one thousand, five one thousand...
passknock = waitForPassKnock()
# Save the passknock secretely.
print("\n\n")
unlockByPassKnock(passknock)
