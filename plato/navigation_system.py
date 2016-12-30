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

import atexit
import threading
from intersection_enum import *
import linked_list
from socket import *
import pickle
from gopigo import *
import Queue

speed = 50
left_speed = speed + 5
higher_constant = 5
lower_constant = 3
msg_on = 0
intersectionCount = 0

atexit.register(stop)		# When you ctrl-c out of the code, it stops the gopigo motors.

#------------------ helper methods ------------------
def set_speed_us():
        set_right_speed(speed)
        set_left_speed(left_speed)

def is_line(self):
        self.notif_queue.put("L?")
        time.sleep(.5)
        isLine = self.notif_queue.get()
        return isLine

def is_intersection(self):
        self.notif_queue.put("IT?")
        time.sleep(.5)
        isIntersection = self.notif_queue.get()
        return isIntersection

def handle_sr(self):
        move_slightly_left()
        notify_line_sensor(self)

def handle_sl(self):
        move_slightly_right()
        notify_line_sensor(self)

def handle_r(self):
        print "handling right"
        small_bwd()
        turn_right()
        notify_line_sensor(self)

def handle_l(self):
        print "handling left"
        small_bwd()
        turn_left()
        notify_line_sensor(self)

def handle_ta(self):
                turn_around()
                notify_line_sensor(self)

def handle_intersection(self):
        small_fwd()
        time.sleep(.5)
        if is_line(self):
                intersection_obj = self.linked_list[intersectionCount]
                handle_intersection_obj(self, intersection_obj)
        else:
                intersection_obj = self.linked_list[intersectionCount]
                handle_intersection_obj(self, intersection_obj)
        small_bwd()
        handle_r(self)

# send notification that we are done. and resume going straight
def notify_line_sensor(self):
  self.notif_queue.put("DONE")
  go_straight_loop(self)

#----------- custom gopigo movement manuevers ---------------

def move_slightly_left():
        set_left_speed(0)
        enc_tgt(0,1,1)
        bwd()
        time.sleep(.5)
        
def move_slightly_right():
        set_right_speed(0)
        enc_tgt(1,0,1)
        bwd()
        time.sleep(.5)

def small_fwd():
        enc_tgt(1,1,2)
        fwd()
        time.sleep(1)

def small_bwd():
        enc_tgt(1,1,2)
        bwd()
        time.sleep(1)

def turn_left():
  set_left_speed(0)
  set_right_speed(90)
  enc_tgt(0,1,18)
  fwd()
  time.sleep(2)
  set_speed(60)
  enc_tgt(1,1,7)
  bwd()
  time.sleep(2)
  
def turn_right():
  set_right_speed(0)
  set_left_speed(90)
  enc_tgt(1,0,18)
  fwd()
  time.sleep(2)
  set_speed(60)
  enc_tgt(1,1,7)
  bwd()
  time.sleep(2)

def turn_around():
          enc_tgt(1,1,5)
          fwd()
          time.sleep(1)
          set_speed(100)
          enc_tgt(1,1,17)
          right_rot()
          time.sleep(2)

#----------- main methods ---------------
def go_straight_loop(self):
        while not self._stop_forward.isSet():
                set_speed_us()
                fwd()
                try :
                  #Handle notification posted and stop going forward
                  handle_notification(self,self.notif_queue.get(False))
                  break
                except Queue.Empty:
                   # there's no notifications pending continue forward
                   right = enc_read(0)
                   left = enc_read(1)
                   if msg_on:
                           print right,
                           print left
                   if (right - left) >= 2:
                        if msg_on:
                                print'Left IS GOING FASTER'

                        lower_speed = speed - lower_constant
                        higher_speed = speed + higher_constant
                        set_right_speed(higher_speed)
                        set_left_speed(lower_speed)
                   elif (left - right) >= 2:
                      if msg_on:
                        print'Right IS GOING FASTER'

                      lower_speed = speed - lower_constant
                      higher_speed = speed + higher_constant
                      set_right_speed(lower_speed)
                      set_left_speed(higher_speed)
                   else:
                      set_speed_us()

def handle_intersection_obj(self, intersectionObj):
                global intersectionCount
                intersectionCount += 1
                print 'intersectionCount is now at', intersectionCount        

                if intersectionObj == intersection_enum.Left:
                        print "Map told us to go left"
                        handle_l(self)
                elif intersectionObj == intersection_enum.Right:
                        print "Map told us to go Right"
                        handle_r(self)
                elif intersectionObj == intersection_enum.Forward:
                        print "Map told us to go Forward"
                        notify_line_sensor(self)
                elif intersectionObj == intersection_enum.Backward:
                        print "Map told us to go Backward"
                        handle_ta(self)


def handle_notification(self, notification):
        stop()
        if notification == "SR":
                handle_sr(self)
        elif notification == "SL":
                handle_sl(self)
        elif notification == "R":
                small_fwd()
                time.sleep(.5)
                if is_line(self):
                        intersection_obj = self.linked_list[intersectionCount]
                        handle_intersection_obj(self, intersection_obj)
                else:
                        handle_r(self)
        elif notification == "L":
                result = is_intersection(self)
                isLeft = (result == "L")
                isIntersection = (result == "IT")

                print 'results: isLeft=', isLeft, 'isIntersection=', isIntersection
                
                small_fwd()
                time.sleep(.5)
                if is_line(self):
                        if isLeft or isIntersection:
                                print "real left"
                                intersection_obj = self.linked_list[intersectionCount]
                                handle_intersection_obj(self, intersection_obj)
                        else:
                                print "picked up a left but not left or intersection, moving forward"
                                notify_line_sensor(self)  
                else:
                        handle_l(self)
        elif notification == "IT":
                handle_intersection(self)
        elif notification == "TA":
                if is_line(self):
                        print "false TA notifying"
                        time.sleep(.5)
                        notify_line_sensor(self)
                else:
                        handle_ta(self)

#----------- class definition ---------------
class goStraightThread(threading.Thread):
        def __init__(self, threadId, name, notif_queue,linked_list):
                super(goStraightThread, self).__init__()
                self._stop_forward = threading.Event()
                threading.Thread.__init__(self)
                self.threadId = threadId
                self.notif_queue = notif_queue
                self.name = name
                self.linked_list = linked_list
        def run(self):
                go_straight_loop(self)
        def stop_foward_operations(self):
                self._stop_forward.set()
        def line_follower_notification(self):
                stop_foward_operations(self)
                     
