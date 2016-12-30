# !/usr/bin/env python
###########################################################################################
#This file is part of the CPS-Rover Project of the State University of New York at Oswego.
#
#The purpose of robot "KITT" is to recognize another Dexter Industries GoPiGo robot
#using the Raspberry Pi camera and drive towards it. Assuming the other GoPiGo is
#following a labyrinth made up of perpendicular "paths," the algorithm will
#look for the other GoPiGo, pay attention to it's movement, and, once the other GoPiGo moved
#outside of KITT's visual field, drive to the last known position and turn left or right
#in order to continue following the other robot after that turn.
#
#Copyright (c) 2016 Mike Mekker, Justin MacCreery, Ryan Staring, Bastian Tenbergen
#Principle Investigator and Project Lead: Bastian Tenbergen, bastian.tenbergen@oswego.edu
#
#License: Creative Commons BY-NC-SA 4.0 https://creativecommons.org/licenses/by-nc-sa/4.0/
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including the rights to use, copy, modify, merge,
#publish, and/or distribute copies of the Software for non-commercial purposes,
#and to permit persons to whom the Software is furnished to do so,
#subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
###########################################################################################

import io
from gopigo import *
import time

class MotorControl:
    def __init__(self):
        enable_encoders()

    def __del__(self):
        stop()
        disable_encoders()

    def turnRight(self, r):
        enc_tgt(1,0, r)
        right()
        time.sleep(.5)
        
    def turnLeft(self, r):
        enc_tgt(0,1, r)
        left()
        time.sleep(.5)
        
    def moveForward(self, r):
        enc_tgt(1,1, r)
        speed = 200
        right_speed = speed 
        higher_constant = 15
        lower_constant = 1
        set_right_speed(150)
        set_left_speed(155)
        fwd()
        
        
    def moveBackward(self, r): 
        enc_tgt(1,1, r)
        bwd()
        time.sleep(.5)

    def stop(self):
        stop()

    def rot(self, r):
        left_rot()
        time.sleep()
        stop()
