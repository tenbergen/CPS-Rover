

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
class AdvancedGoPiGo3():
    """
        this class exists to return some functionatlity from the original gopigo
        and to simplify other aspects of Easygopigo3 and gopigo3 for easy of typing.

        It also allows users to compensate for assymetries between calculated versus actual in the hardware.

"   """

    def __init__(self, angle_compensation = 0,use_mutex = False):
        self.gpg = easygopigo3.EasyGoPiGo3(use_mutex)
        self.speed = self.gpg.get_speed()
        self.angle_compensation = angle_compensation #this corrects for the ability to rotate one full circle.


    def rotate_left(self,degrees):
        self.gpg.turn_degrees(abs(self.__rotation_compensation(degrees)))

    def rotate_right_forever(self):
        self.gpg.set_motor_dps(self.gpg.MOTOR_LEFT, -self.speed/2)
        self.gpg.set_motor_dps(self.gpg.MOTOR_RIGHT, self.speed/2)

    def rotate_left_forever(self):
        self.gpg.set_motor_dps(self.gpg.MOTOR_LEFT, self.speed/2)
        self.gpg.set_motor_dps(self.gpg.MOTOR_RIGHT, -self.speed/2)

    def rotate_right(self,degrees):
        self.gpg.turn_degrees(-abs(self.__rotation_compensation(degrees)))
        
    def __rotation_compensation(self,degrees):
        return degrees + (degrees * (self.angle_compensation/360))

    def set_left_wheel(self,speed):
        self.gpg.set_motor_limits(self.gpg.MOTOR_LEFT, dps=speed)

    def set_right_wheel(self,speed):
        self.gpg.set_motor_limits(self.gpg.MOTOR_RIGHT, dps=speed)

    def forward(self):
        self.gpg.forward()
    def backward(self):
        self.gpg.backward()
    def stop(self):
        self.gpg.stop()
    def drive_cm(self,distance):
        self.gpg.drive_cm(distance)
    def set_speed(self,speed):
        self.gpg.set_speed(speed)

    def led_on(self,id):
        self.gpg.led_on(id)
    def led_off(self,id):
        self.gpg.led_off(id)
    def open_eyes(self):
        self.gpg.open_eyes()
    def close_eyes(self):
        self.gpg.close_eyes()
    def volt(self):
        return self.gpg.volt()
