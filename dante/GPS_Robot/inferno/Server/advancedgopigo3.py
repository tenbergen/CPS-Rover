

from __future__ import print_function
from __future__ import division
# from builtins import input

import sys
# import tty
# import select
import time
import os
from I2C_mutex import Mutex
import easysensors
try:
    from di_sensors import easy_distance_sensor
except ImportError as e:
    # It is quite possible to use the GPG3 without having the di_sensors repo installed
    pass
except Exception as e:
    print("Importing di_sensors error: {}".format(e))


mutex = Mutex(debug=False)


hardware_connected = True
try:
    import gopigo3
except ImportError:
    hardware_connected = False
    print("Cannot import gopigo3 library")
except Exception as e:
    hardware_connected = False
    print("Unknown issue while importing gopigo3")
    print(e)

try:
    import easygopigo3
except ImportError:
    hardware_connected = False
    print("Cannot import gopigo3 library")
except Exception as e:
    hardware_connected = False
    print("Unknown issue while importing gopigo3")
    print(e)

import threading


class AdvancedGoPiGo3:
    """
        this class exists to return some functionality from the original gopigo
        and to simplify other aspects of EasyGoPiGo3 and gopigo3 for easy of typing.

        It also allows users to compensate for asymmetries between calculated versus actual rotation in the hardware.
        It additionally makes overriding existing methods much easier.

"   """

    def __init__(self, angle_compensation=0, use_mutex=False):
        self.lock = threading.Lock()
        self.gpg = easygopigo3.EasyGoPiGo3(use_mutex)
        self.speed = self.gpg.get_speed()
        self.angle_compensation = angle_compensation  # this corrects for the ability to rotate one full circle.
        self.antenna_color = (255,255,255)
        
    def volt(self):
        return self.gpg.volt()
    '''
    The following methods involve the speed of the robot.

    '''
    def get_speed(self):
        return self.speed

    def set_speed(self, in_speed):
        self.gpg.set_speed(in_speed)

    def reset_speed(self):
        self.gpg.reset_speed()

    def set_left_wheel(self, speed):
        self.gpg.set_motor_limits(self.gpg.MOTOR_LEFT, dps=speed)

    def set_right_wheel(self, speed):
        self.gpg.set_motor_limits(self.gpg.MOTOR_RIGHT, dps=speed)

    '''
    The following methods involve the movement of the robot, including turning and rotation.
    '''
    def rotate_left(self, degrees, blocking):
        self.lock.acquire()
        try:
            self.gpg.turn_degrees(-abs(self.__rotation_compensation(degrees)), blocking)
        finally:
            self.lock.release()

    def rotate_right_forever(self):
        self.gpg.set_motor_dps(self.gpg.MOTOR_LEFT, self.speed/2)
        self.gpg.set_motor_dps(self.gpg.MOTOR_RIGHT, -self.speed/2)

    def rotate_left_forever(self):
        self.gpg.set_motor_dps(self.gpg.MOTOR_LEFT, -self.speed/2)
        self.gpg.set_motor_dps(self.gpg.MOTOR_RIGHT, self.speed/2)

    def rotate_right(self, degrees, blocking):
        self.lock.acquire()
        try:
            self.gpg.turn_degrees(abs(self.__rotation_compensation(degrees)), blocking)
        finally:
            self.lock.release()
        
    def __rotation_compensation(self, degrees):
        return degrees + (degrees * (self.angle_compensation/360))

    def right(self):
        self.lock.acquire()
        try:
            self.gpg.right()
        finally:
            self.lock.release()

    def left(self):
        self.lock.acquire()
        try:
            self.gpg.left()
        finally:
            self.lock.release()

    def forward(self):
        self.lock.acquire()
        try:
            self.gpg.forward()
        finally:
            self.lock.release()
        
    def backward(self):
        self.gpg.backward()
        
    def stop(self):
        self.lock.acquire()
        try:
            self.gpg.stop()
        finally:
            self.lock.release()
        
    def drive_cm(self, distance, blocking=True):
        self.lock.acquire()
        try:
            self.gpg.drive_cm(distance, blocking)
        finally:
            self.lock.release()

    def drive_inches(self, dist, blocking=True):
        self.lock.acquire()
        try:
            self.gpg.drive_inches(dist, blocking)
        finally:
            self.lock.release()

    def drive_degrees(self, degrees, blocking=True):
        self.lock.acquire()
        try:
            self.gpg.drive_degrees(degrees, blocking)
        finally:
            self.lock.release()

                               
        
    '''
    The following methods involve the lights and LEDS on the gpg board.
    '''

    def led_on(self, led):
        self.gpg.led_on(led)

    def led_off(self, led):
        self.gpg.led_off(led)

    def open_eyes(self):
        self.gpg.open_eyes()

    def close_eyes(self):
        self.gpg.close_eyes()

    def open_right_eye(self):
        self.gpg.open_right_eye()

    def close_right_eye(self):
        self.gpg.close_right_eye()

    def open_left_eye(self):
        self.gpg.open_left_eye()

    def close_left_eye(self):
        self.gpg.close_left_eye()

    def set_right_eye_color(self,color):
        self.gpg.set_right_eye_color(color)

    def set_left_eye_color(self,color):
        self.gpg.set_left_eye_color(color)

    def set_eye_color(self,color):
        self.gpg.set_eye_color(color)

    def set_antenna_color(self,color):
        if isinstance(color, tuple) and len(color) == 3:
            self.antenna_color = color
        else:
            raise TypeError("antenna color not valid")

    def open_antenna(self):
        self.gpg.set_led(self.gpg.LED_WIFI,self.antenna_color[0],self.antenna_color[1],self.antenna_color[2])

    def close_antenna(self):
        self.gpg.set_led(self.gpg.LED_WIFI,0,0,0)

    def open_all_leds(self):
        self.open_eyes()
        self.open_antenna()

    def close_all_leds(self):
        self.close_eyes()
        self.close_antenna()

