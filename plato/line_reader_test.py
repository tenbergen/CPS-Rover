# !/usr/bin/env python
###########################################################################################
#This file is part of the CPS-Rover Project of the State University of New York at Oswego.
#
#The purpose of robot "PLATO" is to navigate a labyrinth made up of perpendicular "paths,"
#according to a map that it received. PLATO shall identify intersections and take the
#corresponding turns outlined in the map.
#
#Copyright (c) 2016 Andres Ramos, Keith Martin, Bastian Tenbergen
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

#This file is based on the Dexter Industries Line follower example. http://www.dexterindustries.com/
'''
    ## License
    Copyright (C) 2015  Dexter Industries
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.txt>.
    '''

import line_sensor
import time
import threading
import gopigo
import atexit
from gopigo import *

atexit.register(gopigo.stop)		# When you ctrl-c out of the code, it stops the gopigo motors.

#Calibrate speed at first run
#100 is good with fresh batteries 
#125 for batteries with half capacity

speed = 60    #base speed
left_speed = speed + 3  #higher speed for left motor sine weaker
higher_constant = 5 # higher constant used for course correcting
lower_constant = 3 # lower constant used for course correcting

stop_foward = False #if fwd_enc is active switching this value to true stops it.

poll_time=0.01						# Time between polling the sensor, seconds.
									
slight_turn_speed=int(.8*speed)
turn_speed=int(.8*speed)

last_val=[0]*5						# An array to keep track of the previous values.
curr=[0]*5							# An array to keep track of the current values.

gpg_en=0							#Enable/disable gopigo
msg_en=0							#Enable messages on screen.  Turn this off if you don't want messages.

#Get line parameters
line_pos=[0]*5
white_line=line_sensor.get_white_line()
black_line=line_sensor.get_black_line()
range_sensor= line_sensor.get_range()
threshold=[a+b/2 for a,b in zip(white_line,range_sensor)]	# Make an iterator that aggregates elements from each of the iterables.

#Position to take action on
mid 	=[0,0,1,0,0]	# Middle Position.
mid1	=[0,1,1,1,0]	# Middle Position.
small_l	=[0,1,1,0,0]	# Slightly to the left.
small_l1=[0,1,0,0,0]	# Slightly to the left.
small_r	=[0,0,1,1,0]	# Slightly to the right.
small_r1=[0,0,0,1,0]	# Slightly to the right.
left	=[1,1,0,0,0]	# Slightly to the left.
left1	=[1,0,0,0,0]	# Slightly to the left.
right	=[0,0,0,1,1]	# Sensor reads strongly to the right.
right1	=[0,0,0,0,1]	# Sensor reads strongly to the right.
stop	=[1,1,1,1,1]	# Sensor reads stop.
stop1	=[0,0,0,0,0]	# Sensor reads stop.

def absolute_line_pos():
	raw_vals=line_sensor.get_sensorval()
	for i in range(5):
		if raw_vals[i]>threshold[i]:
			line_pos[i]=1
		else:
			line_pos[i]=0
	return line_pos

def run_gpg():
        curr = absolute_line_pos()
        while True:
                last_val=curr
                curr=absolute_line_pos()
                #If the line is towards the sligh left, turn slight right
                if curr==small_l1:
                        #send_notification(self,"SR")
                	#turn_slight_right()
                    print "small_l1"
                elif curr==left or curr==left1:
                        #send_notification(self,"R")
                        #turn_right()
                    print "left"
                #If the line is towards the sligh right, turn slight left
                elif curr==small_r1:
                        #send_notification(self,"SL")
                        #turn_slight_left()
                    print "small_r1"
                elif curr==right or curr==right1:
                        #send_notification(self,"L")
                        #turn_left()
                    print "right"
                elif curr==stop:
                        #send_notification(self,"ST")
                        #handle_intersection()
                    print "stop"
                elif curr==stop1:
                        #send_notification(self,"TA")
                        #turn_around()
                        print "stop1"
                else:
                        print "Straight"
                        print curr
                time.sleep(poll_time)


run_gpg()
