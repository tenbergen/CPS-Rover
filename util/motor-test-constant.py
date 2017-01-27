# !/usr/bin/env python
###########################################################################################
#This file is part of the CPS-Rover Project of the State University of New York at Oswego.
#
#The purpose of this file is to turn on both GoPiGo motors and run them
#continuously at a constant speed.
#The script continuously monitors the battery voltage delivered to the motors as well as
#the elapsed ticks on both encoder wheels.
#This can be useful to test the speed difference between both motors, since production
#tolerances in the motors cause them to inevitably go at different speeds, resulting
#over time in largely unequal distances traveled (and hence the GoPiGo to slightly
#veer of course). Using this script, these differences can be measured and correlated
#to the voltage delivered to the motors to establish the change in differences over time.
#
#Copyright (c) 2016 Bastian Tenbergen
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

from gopigo import *
import sys
import atexit

atexit.register(stop)

#change the following two, if you want to change speed (0 < speed <= 255)
# or the time between measurements
measure_interval = 10
speed = 200

enable_encoders()
set_speed(speed)
fwd()
elapsed = 0

while True:
    print elapsed, volt(), enc_read(0), enc_read(1), speed
    sys.stdout.flush()
    elapsed += measure_interval
    time.sleep(measure_interval)
