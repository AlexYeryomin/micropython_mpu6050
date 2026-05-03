# Copyright (c) 2026 Alex Yeryomin
#
# A simple class for MicroPython to control well-known MPU6050 module.
# You can find many libraries for this module, however, this one,
# besides common methods to read gyros and accelemometers, allows
# to setup MPU6050 module as Motion Detection sensor. In this mode,
# the module generates the interrupt when a motion of specific amount
# and duration is detected.
#
# This code uses prealocated buffers and memory views, which makes
# much faster than other implementations I found online. I have tested
# on ESP32-D1, ESP32-S2, ESP32-C3, Raspberry Pico, WeMos W600.
#
# Only registers and flags that are necessary to implement
# the required fuctionality are listed below. For the full list
# of available registres, see the datasheet for MPU6050.
# The best available resource about MPU6050 can be found here:
# https://www.i2cdevlib.com/devices/mpu6050 (by Jeff Rowberg)

import machine

from time import ticks_us, ticks_diff

DEFAULT_ADDRESS = const(0x68)

''''''''''''''''''''''''''''''
REG_PWR_MGMT_1 = const(0x6B)
REG_PWR_MGMT_2 = const(0x6C)

DEVICE_RESET   = const(0x80)
SLEEP          = const(0x40)
CYCLE          = const(0x20)
TEMP_DIS       = const(0x08)

CLK_INTERNAL   = const(0x00)
CLK_PLL_XGYRO  = const(0x01)
CLK_PLL_YGYRO  = const(0x02)
CLK_PLL_ZGYRO  = const(0x03)
CLK_PLL_EXT32K = const(0x04)
CLK_PLL_EXT19M = const(0x05)
CLK_KEEP_RESET = const(0x07)

''''''''''''''''''''''''''''''
REG_SIGNAL_PATH_RESET = const(0x68)

GYRO_RESET     = const(0x4)
ACCEL_RESET    = const(0x2)
TEMP_RESET     = const(0x1)

''''''''''''''''''''''''''''''
REG_INT_PIN_CFG = const(0x37)

MOT_EN          = const(0x40)
LATCH_INT_EN    = const(0x20)

''''''''''''''''''''''''''''''
REG_INT_STATUS = const(0x3A)

FF_INT         = const(0x80)
MOT_INT        = const(0x40)
ZMOT_INT       = const(0x20) 
FIFO_OFLOW_INT = const(0x10)
I2C_MST_INT    = const(0x08)
PLL_RDY_INT    = const(0x04)
DMP_INT        = const(0x02)  
RAW_RDY_INT    = const(0x01)

''''''''''''''''''''''''''''''
REG_CONFIG            = const(0x1A)
REG_GYRO_CONFIG       = const(0x1B)
REG_ACCEL_CONFIG      = const(0x1C)
REG_MOT_THR           = const(0x1F)
REG_MOT_DUR           = const(0x20)
REG_INT_ENABLE        = const(0x38)
REG_ACCEL_XOUT_H      = const(0x3B)
REG_ACCEL_XOUT_L      = const(0x3C)
REG_ACCEL_YOUT_H      = const(0x3D)
REG_ACCEL_YOUT_L      = const(0x3E)
REG_ACCEL_ZOUT_H      = const(0x3F)
REG_ACCEL_ZOUT_L      = const(0x40)
REG_TEMP_OUT_H        = const(0x41)
REG_TEMP_OUT_L        = const(0x42)
REG_GYRO_XOUT_H       = const(0x43)
REG_GYRO_XOUT_L       = const(0x44)
REG_GYRO_YOUT_H       = const(0x45)
REG_GYRO_YOUT_L       = const(0x46)
REG_GYRO_ZOUT_H       = const(0x47)
REG_GYRO_ZOUT_L       = const(0x48)

REG_MOT_DETECT_CTRL   = const(0x69)
REG_WHO_I_AM          = const(0x75)

FS_SEL_MASK           = const(0x18)
FS_SEL_OFFSET         = const(3)

DLPF_MASK             = const(0x7)

class MPU6050:
    
    def __init__(self, i2c:machine.I2C, address = DEFAULT_ADDRESS):
        self.i2c = i2c
        self.address = address
        self.dataToWrite = bytearray(1)
        self.data1 = bytearray(1)
        self.data2 = bytearray(2)
        self.data6 = bytearray(6)
        self.data14 = bytearray(14)
        self.mv2 = memoryview(self.data2)
        self.mv6 = memoryview(self.data6)
        self.mv14 = memoryview(self.data14)
        self.gyroRange = self._readGyroRange()
        self.accelRange = self._readAccelRange()

    def wake(self):
        self._writeData(REG_PWR_MGMT_1, CLK_PLL_XGYRO)

    def sleep(self):
        self._writeData(REG_PWR_MGMT_1, SLEEP)
        
    def whoAmI(self):
        self._readData1(REG_WHO_I_AM)
        return self.data1[0]
    
    # Returns the temperature of the board. [C°]
    def readTemperature(self):
        self._readData2(REG_TEMP_OUT_H) # :REG_TEMP_OUT_L
        temp = MPU6050._bytes_to_signed_word(self.data2[0], self.data2[1])
        return (temp / 340.0) + 36.53

    def getGyroRange(self):
        return self.gyroRange

    def setGyroRange(self, range):
        self.gyroRange = MPU6050._constrain(range, 0, 3)
        self._writeGyroRange(self.gyroRange)

    def _readGyroRange(self):
        self._readData1(REG_GYRO_CONFIG)
        return MPU6050._fs_sel_to_range(self.data1[0])
        
    def _writeGyroRange(self, range):
        self._writeData(REG_GYRO_CONFIG, MPU6050._range_to_fs_sel(range))

    GYRO_RANGE_SCALES = ( 1/131.0, 1/65.5, 1/32.8, 1/16.4 )

    # Returns gyro measurements as [x, y, z].
    @micropython.native
    def readGyroData(self):
        gyroScale = MPU6050.GYRO_RANGE_SCALES[self.gyroRange]
        self._readData6(REG_GYRO_XOUT_H)
        mv6 = self.mv6
        x = MPU6050._slice_to_signed_word(mv6[0:2]) * gyroScale
        y = MPU6050._slice_to_signed_word(mv6[2:4]) * gyroScale
        z = MPU6050._slice_to_signed_word(mv6[4:6]) * gyroScale
        return x, y, z

    @micropython.native
    def readGyroDataY(self):
        gyroScale = MPU6050.GYRO_RANGE_SCALES[self.gyroRange]
        self._readData2(REG_GYRO_YOUT_H)
        return MPU6050._slice_to_signed_word(self.data2) * gyroScale

    def getAccelRange(self):
        return self.accelRange

    def setAccelRange(self, range):
        self.accelRange = MPU6050._constrain(range, 0, 3)
        self._writeAccelRange(self.accelRange)

    def _readAccelRange(self):
        self._readData1(REG_ACCEL_CONFIG)
        return MPU6050._fs_sel_to_range(self.data1[0])

    def _writeAccelRange(self, range):
        self._writeData(REG_ACCEL_CONFIG, MPU6050._range_to_fs_sel(range))

    # Returns acceleration measurements as [x, y, z].
    @micropython.native
    def readAccelData(self):
        accelScale = 0x4000 >> self.accelRange
        self._readData6(REG_ACCEL_XOUT_H)
        mv6 = self.mv6
        x = MPU6050._slice_to_signed_word(mv6[0:2]) / accelScale
        y = MPU6050._slice_to_signed_word(mv6[2:4]) / accelScale
        z = MPU6050._slice_to_signed_word(mv6[4:6]) / accelScale
        return x, y, z

    @micropython.native
    def readGyroAccelData(self):
        accelScale = 0x4000 >> self.accelRange
        gyroScale = MPU6050.GYRO_RANGE_SCALES[self.gyroRange]
        self.i2c.readfrom_mem_into(self.address, REG_ACCEL_XOUT_H, self.data14)
        mv14 = self.mv14
        ax = MPU6050._slice_to_signed_word(mv14[0:2]) / accelScale
        ay = MPU6050._slice_to_signed_word(mv14[2:4]) / accelScale
        az = MPU6050._slice_to_signed_word(mv14[4:6]) / accelScale
        # [6:8] - temperature, skipped.
        gx = MPU6050._slice_to_signed_word(mv14[8:10]) * gyroScale
        gy = MPU6050._slice_to_signed_word(mv14[10:12]) * gyroScale
        gz = MPU6050._slice_to_signed_word(mv14[12:14]) * gyroScale
        return (ax, ay, az), (gx, gy, gz)

    def setupMotionDetection(self, motionThreshold, motionDuration_ms, latchEnabled=False):
        self._writeData(REG_SIGNAL_PATH_RESET, GYRO_RESET|ACCEL_RESET|TEMP_RESET)
        self._writeData(REG_INT_PIN_CFG, LATCH_INT_EN if latchEnabled else 0)
        self._writeData(REG_ACCEL_CONFIG, 0x01) # FIXME: Define 3:0 bits
        self._writeData(REG_MOT_THR, motionThreshold)
        self._writeData(REG_MOT_DUR, motionDuration_ms)
        self.resetMotionDetectionLatch()
        self._writeData(REG_MOT_DETECT_CTRL, 0x0)

    def enableMotionDetectionIRQ(self):
        self._writeData(REG_INT_ENABLE, MOT_EN)

    def disableMotionDetectionIRQ(self):
        self._writeData(REG_INT_ENABLE, 0)

    def resetMotionDetectionLatch(self):
        self._readData1(REG_INT_STATUS)
        return self.data1[0]

    def read_DLPF_Range(self):
        self._readData1(REG_CONFIG)
        return self.data1[0]
    
    def write_DLPF_Range(self, range):
        self._writeData(REG_CONFIG, range & DLPF_MASK)

    # Private methods - do not call directly.

    def _writeData(self, register, data):
        self.dataToWrite[0] = data
        self.i2c.writeto_mem(self.address, register, self.dataToWrite)

    @micropython.native
    def _readData1(self, register):
        self.i2c.readfrom_mem_into(self.address, register, self.data1)

    @micropython.native
    def _readData2(self, register):
        self.i2c.readfrom_mem_into(self.address, register, self.data2)

    @micropython.native
    def _readData6(self, register):
        self.i2c.readfrom_mem_into(self.address, register, self.data6)

    @staticmethod
    @micropython.native
    def _slice_to_signed_word(high_low):
        return MPU6050._bytes_to_signed_word(high_low[0], high_low[1])

    @staticmethod
    @micropython.native
    def _bytes_to_signed_word(high, low):
        word = (high << 8) + low
        return -((0xFFFF - word) + 1) if word >= 0x8000 else word # two’s complement
    
    @staticmethod
    def _fs_sel_to_range(fs_sel):
        return (fs_sel & FS_SEL_MASK) >> FS_SEL_OFFSET

    @staticmethod
    def _range_to_fs_sel(range):
        return (range << FS_SEL_OFFSET) & FS_SEL_MASK
    
    @staticmethod
    def _constrain(x, out_min, out_max):
        return max(out_min, min(x, out_max))

 
