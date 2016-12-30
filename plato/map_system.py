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

import threading
from navigation_system import *
from line_detection_system import *
import atexit
import sys 
import time
import intersection_enum
from linked_list import *
import gopigo
import Queue
from socket import *
import pickle

notif_queue = Queue.Queue()
hardcoded = True

if not hardcoded:
    s = socket()         # Create a socket object
    port = 12344                # Reserve a port for your service.
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('192.168.1.101', port))
    s.listen(1)
    (socket,address) = s.accept()
    print 'Got connection from: ', address
    s = socket
    data = s.recv(1024)
    linked_list = pickle.loads(data)
else: 
    #linked_list = [2,2,0,1]
    linked_list = [2, 1]

print linked_list

line_thread = lineDetectionThread(2,"lineDetectionThread",notif_queue)
straight_thread = goStraightThread(1,"straight_thread",notif_queue,linked_list)

def test_function():
    print "----------------------------------test function"
    
def stop_operations():
    gopigo.stop()
    straight_thread.stop_foward_operations()
    line_thread.stop_line_loop()



line_thread.start()
straight_thread.start()

if raw_input("let me know") == "e":
    stop_operations()








