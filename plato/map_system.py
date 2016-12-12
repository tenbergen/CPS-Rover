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








