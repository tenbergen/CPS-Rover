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
left	=[1,1,1,0,0]	# Slightly to the left.
superLeft = [1,1,1,1,0]
right	=[0,0,1,1,1]	# Sensor reads strongly to the right.
superRight = [0,1,1,1,1]
intersection	=[1,1,1,1,1]	# Sensor reads stop.
stop1	=[0,0,0,0,0]	# Sensor reads stop.

#-------------- helper methods ----------------------

#Converts the raw values to absolute 0 and 1 depending on the threshold set
def absolute_line_pos():
	raw_vals=line_sensor.get_sensorval()
	for i in range(5):
		if raw_vals[i]>threshold[i]:
			line_pos[i]=1
		else:
			line_pos[i]=0
	return line_pos

def is_line():
    absolute_line_pos()
    line = absolute_line_pos()
    isLine = (line != stop1)
    return isLine

def is_intersection():
    absolute_line_pos()
    line = absolute_line_pos()
    print 'line is: ' ,line 
    isIntersection = (line == intersection)
    isLeft = (line == right or line == superRight)
    isRight = (line == left)
    result = ""
    if isIntersection:
            result = "IT"
    elif isLeft:
            result = "L"
    elif isRight:
            result = "R"
    return result

def line_check(self):
        #check if theres a line, send result, await for restatr
        self.notif_queue.put(is_line())
        time.sleep(.5)
        self.notif_queue.get()
        run_gpg(self)

#block until told otherwise
def send_notification(self, message):
        if message != "SR" and message != "SL":
                print "sending notifiation"
                print message
        
        self.notif_queue.put(message)
        time.sleep(.5)
        result = self.notif_queue.get()
        if result == "IT?":
                self.notif_queue.put(is_intersection())
                time.sleep(.5)
                if self.notif_queue.get() == "L?":
                        line_check(self)
                else:
                        run_gpg(self)       
        elif result == "L?":
                line_check(self)
        else:
                run_gpg(self)
                
#-------------- main loop--------------
def run_gpg(self):
        curr = absolute_line_pos()
        while not self._stop_line_loop.isSet():
                last_val=curr
                curr=absolute_line_pos()
                #If the line is towards the sligh left, turn slight right
                if curr==small_l1:
                        send_notification(self,"SR")
                elif curr==left or curr == superLeft:
                        print 'line read for right was: ', curr
                        send_notification(self,"R")
                #If the line is towards the sligh right, turn slight left
                elif curr==small_r1:
                        send_notification(self,"SL")
                elif curr==right or curr == superRight:
                        print 'line read for left was: ', curr
                        send_notification(self,"L")
                elif curr==intersection:
                        send_notification(self,"IT")
                elif curr==stop1:
                        send_notification(self,"TA")
                time.sleep(poll_time)

#------------------ class definition ------------------

class lineDetectionThread(threading.Thread):
        def __init__(self, threadId, name, notif_queue):
                threading.Thread.__init__(self)
                self.threadId = threadId
                self.name = name
                self.notif_queue = notif_queue
                self._stop_line_loop= threading.Event()
        def run(self):
                run_gpg(self)
        def stop_line_loop(self):
            self._stop_line_loop.set()

	
