import socket
from threading import Thread
from gps import *
from time import sleep
import urllib2
import Queue
from gopigo import *
from math import degrees, atan2
import os
import select

"""""""""""""""""""""""""""""""""
Creator: Jonathan Baker

Description:
This program runs on the GoPiGo rover. The program directly controls the rover's movements based on commands
sent from the controller program. The rover can move forwards, backwards, and pivot and has a working LED light.

Every 5 seconds, the rover takes a new GPS coordinate and sends it to the controller.
Every 0.1 seconds, the rover sends it current speed to the controller to confirm its current speed. If the two speeds are
different, then the controller will automatically send back the correct speed and the rover will automatically
travel at the new speed.

TO DO:
Moving Diagonally
Rover can sense when disconnected from controller
Calculate bearing
Allow rover to move freely when disconnected for a short time
Rover can return home
Calculate Shortest Path in Graph
Rover can follow a set of GPS coordinates when disconnected
"""""""""""""""""""""""""""""""""

class Connection(Thread):
    def __init__(self):
        Thread.__init__(self)
        
    def run(self):
        global commands
        global running
        commands = Queue.Queue()
        while running:
            #try:
            r, _, _ = select.select([conn], [], [], 2)
            if r:
                data = conn.recv(1024).split()
                print data
            #except socket.timeout:
            #   print "Timeout exceeded"
                commands.put(data)
                while len(data) > 4:
                    data = data[3:]
                    data[0] = data[0][3:]
                    commands.put(data)
    #def isConnected(self):
    #    global host
    #    try:
    #        urllib2.urlopen("http://" + host, timeout=1)
    #        return True
    #    except urllib2.URLError as err:
    #        return False

"""    def run(self):
        global running
        while running:
            if self.isConnected():
                sleep(10)
            else:
                running = False
                disconnected = True
                print "Disconnect detected"
                """




class GPS(Thread):
    def __init__(self):
        Thread.__init__(self)
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)

    def run(self):
        global gpsd
        global running
        while running:
            gpsd.next()
            _, r, _ = select.select([], [conn], [], 2)
            if r:
                conn.send(str.encode("G " + str(gpsd.fix.latitude) + " " + str(gpsd.fix.longitude)))
                sleep(5)

class SendSpeed(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global running
        while running:
            _, r, _ = select.select([], [conn], [], 2)
            if r:
                conn.send(str.encode("M " + str(xspeed) + " " + str(yspeed)))
                sleep(0.1)

class Main(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global running
        global commands
        servo_pos = 90
        while running:
            while commands.empty():
            #   if self.isConnected():
                sleep(0.1)
                print "Waiting"
                if not running:
                    return
            #   else:
            #       running = False
            print "Getting command"
            data = commands.get()
            print "Command Received"
            if not data:
                print "Received nothing and quitting"
                running = False
                break
            if data[0] == "Stop":
                if data[2] != 0 and data[3] != 0:
                    with commands.mutex:
                        commands.queue.clear()
                data = data[1:]
            if data[0] == "Quit":
                print "Quitting"
                break
            elif data[0] == "M":
               # print "Moving in a direction"
               # print data
                xspeed = int(data[1])
                yspeed = int(data[2])

                if xspeed == 0 and yspeed == 0:
                   # print "Stopping"
                    stop()
                else:
                    set_left_speed(abs(xspeed))
                    set_right_speed(abs(yspeed))
                    if yspeed > 25 and  xspeed > 25:
                        bwd()
                    else:
                        fwd()
            elif data[0] == "SER":
                print "Changing Looking Direction"
                print data
                x = float(data[1])
                xpos = int(x * 5)
                if xpos > 0 and servo_pos > 10:
                    servo_pos = servo_pos - xpos
                    servo(servo_pos)
                if xpos < 0 and servo_pos < 140:
                    servo_pos = servo_pos - xpos
                    servo(servo_pos)
            elif data[0] == "LON":
                print "Turning LED on"
                led_on(1)
            elif data[0] == "LOFF":
                print "Turning LED off"
                led_off(1)

def isConnected():
    global host
    try:
        urllib2.urlopen("http://" + host, timeout=1)
        return True
    except urllib2.URLError as err:
        return False

def bearing(x, y, prevx, prevy):
    angle = degrees(atan2(y - prevy, x - prevx))
    return (angle + 360) % 360

#global commands
#commands = Queue.Queue()
global running
running = True
global disconnected
disconnected = False

global speed
speed = 0
set_speed(speed)
global xspeed
xspeed = 0
global yspeed
yspeed = 0
servo_pos = 90
servo(servo_pos)

os.system("sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock")
gpsd = None

global host
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '192.168.1.101'
port = 10000

address = (host, port)

sock.bind(address)
#sock.settimeout(5)
sock.listen(10)

print "Running at", volt(), "volts."
print "Host:", host
global addr
global conn

conn, addr = sock.accept()
print "Connection from ", addr

connect = Connection()
connect.start()
gps = GPS()
gps.start()
commander = Main()
commander.start()
speeder = SendSpeed()
speeder.start()
try:
    
    """
    while running:
        data = conn.recv(1024).split()
        commands.put(data)
        while len(data) > 4:
            data = data[3:]
            data[0] = data[0][3:]
            commands.put(data)
    """
    while running:
            if isConnected():
                sleep(3)
            else:
                running = False
                disconnected = True
                print "Disconnect detected"
finally:
    print "Trying to disconnect"
    conn.close()
    running = False
    print "Joining Threads"
    sock.close()
    print "Socket closed"
    #if not disconnected:
    connect.join()
    print "Connect has terminated"
    gps.join()
    print "GPS has terminated"
    speeder.join()
    print "Speeder has terminated"
    commander.join()
    print "Commander has terminated"
    stop()
    print "Connection closed"
if disconnected:
    print "Starting to run myself"
    set_speed(100)
    fwd()
    sleep(5)
    stop()
