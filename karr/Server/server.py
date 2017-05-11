import socket
from threading import Thread
from gps import *
from time import sleep
import urllib2
import Queue
from gopigo import *
from offline import *
from math import degrees, atan2
import os
import select

"""""""""""""""""""""""""""""""""
Creator: Jonathan Baker

Description:
This program runs on the GoPiGo rover. The program directly controls the rover's movements based on commands
sent from the controller program. The rover can move forwards, backwards, diagonally, and pivot and has a working LED light.

Functionality:
Every 5 seconds, the rover takes a new GPS coordinate and sends it to the controller.
Every 0.1 seconds, the rover sends its current speed to the controller to confirm its current speed. If the two speeds are
  different, then the controller will automatically send back the correct speed and the rover will automatically
  travel at the new speed.

"""""""""""""""""""""""""""""""""


global host
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '192.168.1.106'
port = 10000

address = (host, port)

sock.bind(address)
sock.listen(10)

print "Running at", volt(), "volts."
print "Host:", host

conn, addr = sock.accept()
print "Connection from ", addr

class Connection(Thread):
    #receives server commands from controller
    #populates a server command for Main class to handle
    
    def __init__(self):
        Thread.__init__(self)
        
    def run(self):
        global movement_commands
        global general_commands
        global running
        movement_commands = Queue.Queue()
        general_commands = Queue.Queue()
        while running:
            r, _, _ = select.select([conn], [], [], 2)
            if r:
                data = conn.recv(1024).split()
                self.fill_movement_list(data)
                while len(data) > 4:
                    data = data[3:]
                    data[0] = data[0][3:]
                    self.fill_movement_list(data)

    def fill_movement_list (self, data):
        global movement_commands
        global general_commands
        if not data:
            general_commands.put(None)
            return
        if data[0] == "M" or data[0] == "Stop":
            movement_commands.put(data)
        else:
            general_commands.put(data)

class GPS_Coord(Thread):
    #clears the GPS reading buffer
    
    def __init__(self):
        Thread.__init__(self)
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)

    def run(self):
        global gpsd
        global running
        while running:
            gpsd.next()


class GPSServer(Thread):
    #sends current GPS location to controller every 5 seconds
    
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global gpsd
        global running
        global home_coord
        while home_coord[0] == 0:
            home_coord = [gpsd.fix.latitude, gpsd.fix.longitude]
        while running:
            _, r, _ = select.select([], [conn], [], 2)
            if r:
                conn.send(str.encode("G " + str(gpsd.fix.latitude) + " " + str(gpsd.fix.longitude)))
                sleep(5)

class SendSpeed(Thread):
    #sends current running speed to controller every 0.1 seconds
    
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
    #handles all server commands from controller
    
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global running
        global movement_commands
        global general_commands
        global home_coord
        servo_pos = 90
        while running:
            while movement_commands.empty() and general_commands.empty():
                sleep(0.1)
                if not running:
                    return
            if not general_commands.empty():
                data = general_commands.get()
            else:
                data = movement_commands.get()
            if not data:
                print "Received nothing and quitting"
                running = False
                break
            if data[0] == "Stop":
                if data[2] != 0 and data[3] != 0:
                    with movement_commands.mutex:
                        movement_commands.queue.clear()
                data = data[1:]
            if data[0] == "Quit":
                print "Quitting"
                break
            elif data[0] == "M":
                xspeed = int(data[1])
                yspeed = int(data[2])

                if xspeed == 0 and yspeed == 0:
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
            elif data[0] == "Home":
                print "Going home"
                goHome(home_coord)
                with movement_commands.mutex:
                    movement_commands.queue.clear()
                with general_commands.mutex:
                    general_commands.queue.clear()

#checks if rover is still connected to the network
def isConnected():
    global host
    try:
        urllib2.urlopen("http://" + host, timeout=1)
        return True
    except urllib2.URLError as err:
        return False




global running
running = True
global disconnected
disconnected = False

speed = 0
set_speed(speed)
xspeed = 0
yspeed = 0
servo_pos = 90
servo(servo_pos)

home_coord = [0,0]

#os.system("sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock")
gpsd = None

#initialize and start threads
connect = Connection()
connect.start()
gps_coord = GPS_Coord()
gps_coord.start()
gps = GPSServer()
gps.start()
commander = Main()
commander.start()
speeder = SendSpeed()
speeder.start()
try:
    while running:
            if isConnected():
                sleep(3)
            else:
                running = False
                disconnected = True
                print "Disconnect detected"
finally:
    conn.close()
    sock.close()
    connect.join()
    gps_coord.join()
    gps.join()
    speeder.join()
    commander.join()
    stop()
    
if disconnected:
    print "Starting to run myself"
    followCoords()
    stop()
