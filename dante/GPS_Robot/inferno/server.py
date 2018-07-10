import socket
from threading import Thread
#from gps import *
from time import sleep
from urllib.request import *
from urllib.error import *
import queue
from advancedgopigo3 import *
from math import degrees, atan2
import os
import select
'''
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
'''
xspeed = 0
yspeed = 0
class Server(Thread):
    def __init__(self,gpg,h,p):
        Thread.__init__(self)
        self.gpg = gpg
        global host
        host = h
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = p

        address = (host, port)

        self.sock.bind(address)
        self.sock.listen(100)

        print("Running at", self.gpg.volt(), "volts.")
        print("Host:", host)

        self.conn, self.addr = self.sock.accept()
        print("Connection from ", self.addr)
        global running
        running = True
        global disconnected
        disconnected = False

        self.speed = 300
        self.gpg.set_speed(self.speed)


        #initialize and start threads
        self.connect = Connection(self.conn)
        
        self.commander = Main(self.gpg)
        
        self.speeder = SendSpeed(self.conn)
        print(self.conn)
        

    def run(self):
        self.connect.start()
        self.commander.start()
        self.speeder.start()
        global running
        print(running)
        try:
            while running:
                if isConnected():
                    sleep(3)
                else:
                    running = False
                    disconnected = True
                    print("Disconnect detected")
        finally:
            self.connect.join()
            self.speeder.join()
            self.commander.join()
            self.conn.close()
            self.sock.close()
            self.gpg.stop()

    def can_run(self,canrun):
        self.commander.can_accept_commands = canrun
        print(self.commander.can_accept_commands)

class Connection(Thread):
    #receives server commands from controller
    #populates a server command for Main class to handle
    
    def __init__(self,conn):
        Thread.__init__(self)
        self.conn = conn
        
    def run(self):
        global movement_commands
        global general_commands
        global running

        movement_commands = queue.Queue()
        general_commands = queue.Queue()
        while running:
            r, _, _ = select.select([self.conn], [], [], 2)
            if r:
                data = self.conn.recv(1024).split()
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


class SendSpeed(Thread):
    #sends current running speed to controller every 0.1 seconds
    
    def __init__(self,conn):
        Thread.__init__(self)
        self.conn = conn

    def run(self):
        global running
        while running:
            _, r, _ = select.select([], [self.conn], [], 2)
            if r:
                self.conn.send(str.encode("M " + str(xspeed) + " " + str(yspeed)))
                sleep(0.1)

class Main(Thread):
    #handles all server commands from controller
    
    def __init__(self,gpg):
        Thread.__init__(self)
        self.gpg = gpg
        self.queue = queue.Queue()
        self.can_accept_commands = True

    def run(self):
        global running
        global movement_commands
        global general_commands
        global home_coord
        servo_pos = 90
        while running:
            if not self.queue.empty():
                    self.can_accept_commands = self.queue.get()
            if not self.can_accept_commands:
                self.gpg.stop()
                while not self.can_accept_commands:
                    sleep(.1)
                    if not self.queue.empty():
                        self.can_accept_commands = self.queue.get()
            while movement_commands.empty() and general_commands.empty():
                sleep(0.1)
                if not running:
                    return
            if not general_commands.empty():
                data = general_commands.get()
            else:
                data = movement_commands.get()
            if not data:
                print("Received nothing and quitting")
                running = False
                break
            dat = data
            data = []
            for d in dat:
                data.append(d.decode('utf-8'))
            print(data)
            if data[0] == "Stop":
##                if data[2] != 0 and data[3] != 0:
##                    with movement_commands.mutex:
##                        movement_commands.queue.clear()
##
                gpg.stop()
                data = data[1:]
            if data[0] == "Quit":
                print("Quitting")
                break
            elif data[0] == "M":
                xspeed = float(data[1])
                yspeed = float(data[2])
                xspeed = int(xspeed)
                yspeed = int(yspeed)

                if xspeed == 0 and yspeed == 0:
                    self.gpg.stop()
                elif xspeed == 0:
                    self.gpg.rotate_right_forever()
                elif yspeed ==0:
                    self.gpg.rotate_left_forever()
                else:
                    self.gpg.set_left_wheel(abs(xspeed))
                    self.gpg.set_right_wheel(abs(yspeed))
                    if yspeed > 25 and  xspeed > 25:
                        self.gpg.backward()
                    else:
                        self.gpg.forward()
##            elif data[0] == "SER":
##                print("Changing Looking Direction")
##                print(data)
##                x = float(data[1])
##                xpos = int(x * 5)
##                if xpos > 0 and servo_pos > 10:
##                    servo_pos = servo_pos - xpos
##                    servo(servo_pos)
##                if xpos < 0 and servo_pos < 140:
##                    servo_pos = servo_pos - xpos
##                    servo(servo_pos)
            elif data[0] == "LON":
                print("Turning LED on")
                self.gpg.led_on(0)
                self.gpg.led_on(1)
                self.gpg.open_eyes()
            elif data[0] == "LOFF":
                print("Turning LED off")
                self.gpg.led_off(0)
                self.gpg.led_off(1)
                self.gpg.close_eyes()

#checks if rover is still connected to the network
def isConnected():
    global host
    try:
        urlopen("http://" + host, timeout=1)
        return True
    except URLError as err:
        return False




if __name__ == '__main__':
    app = Server(AdvancedGoPiGo3(25),"dante.local",10000)
    app.run()

    
