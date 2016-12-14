#Author: Andres Ramos

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
import socket
import pickle

notif_queue = Queue.Queue()

linked_list = linked_list()

line_thread = lineDetectionThread(2,"lineDetectionThread",notif_queue)
straight_thread = goStraightThread(1,"straight_thread",notif_queue,linked_list)


def test_function():
    print "----------------------------------test function"
    
def stop_operations():
    gopigo.stop()
    straight_thread.stop_foward_operations()
    line_thread.stop_line_loop()
    send_final_map()

def send_final_map():
    s = socket.socket()
    host = socket.gethostname()
    port = 12344
    s.connect(('192.168.1.101', port))
    final_map = linked_list.done()
    map_string = pickle.dumps(final_map)
    s.send(map_string)
    
line_thread.start()
straight_thread.start()

if raw_input("let me know") == "e":
    stop_operations()

