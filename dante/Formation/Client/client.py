from xbee_node import XbeeMesh
from gps import GPS
from advancedgopigo3 import *
import socket
import threading
import queue
from time import sleep
from vector import Vector

from formation import Formation


class Client(threading.Thread):

    def __init__(self):
        super(Client, self).__init__()
        self._stop_event = threading.Event()

        # User parameters
        # xbee & socket
        self.name = "Kro"  # change to name of the robot
        self.ip_port = 10000
        self.xbee_dev_port = "/dev/ttyUSB0"
        self.baud_rate = 9600

        # MarvelMind gps
        self.marvelMind_dev_port = "/dev/ttyACM0"
        self.front_hedge = 10
        self.rear_hedge = 12

        # Client
        self.is_master = False
        self.xbee_discover_done = False
        self.connected = False
        self.formation_q = queue.Queue()
        self.unparsed_queue = queue.Queue()
        self.gps_queue = queue.Queue()
        self.sckt = None

        # init all threads/ classes
        self.xbee_node = XbeeMesh(self.name, self.xbee_dev_port, self.baud_rate)
        self.gpg = AdvancedGoPiGo3()
        self.gps = GPS(self.front_hedge, self.rear_hedge, self.gpg, self.marvelMind_dev_port, q=self.gps_queue,
                       debug_mode=False)
        self.formation = Formation(self.front_hedge, self.rear_hedge, self.gpg, self.marvelMind_dev_port,
                                   self.formation_q, self.xbee_node)

        # init gps
        self.gps.set_min_distance(50)
        self.gpg.set_speed(200)

        # start all threads
        self.xbee_node.start()
        self.gps.start()
        self.formation.start()

    def stop(self):
        self._stop_event.set()
        self.xbee_node.stop()
        self.gps.stop()
        print("\nclient thread stopped")

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            # print("\n[Discoverd robots:]",self.xbee_node.get_robot_list())
            if input("press 'ENTER' to start or any key to rescan") == "":
                self.xbee_discover_done = True
                self.xbee_node.discover_done = True
                self.formation_q.put(self.xbee_node.get_robot_list())
                break

        while not self.stopped():
            counter = 0
            while not self.xbee_discover_done:
                # print("\n[Discoverd robots:]",self.xbee_node.get_robot_list())
                sleep(1)
                counter = counter + 1
                if counter == 5:
                    self.xbee_discover_done = True
                    self.xbee_node.discover_done = True
                    self.formation_q.put(self.xbee_node.get_robot_list())

            if not self.connected:
                if self.xbee_node.check_master():
                    self.is_master = True
                    self.formation_q.put("!MASTER")
                    self.receive_UDP_broadcast()
                else:
                    pass

            if self.is_master:
                self.manage_master_commands()
            else:
                self.manage_slave_commands()

        self.stop()

    def receive_UDP_broadcast(self):
        broadcast_UDP_Recvr = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
        broadcast_UDP_Recvr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        broadcast_UDP_Recvr.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_UDP_Recvr.bind(("", self.ip_port))
        while True:
            print("\nWe are master. Waitting for UDP broadcast")
            try:
                dataTCP, addr = broadcast_UDP_Recvr.recvfrom(1024)
                print("UDP received, switching to TCP " + str(dataTCP))
                break
            except socket.timeout:
                pass
        time.sleep(1)
        broadcast_UDP_Recvr.close()
        print("broadcast receiver closed")

        while True:  # in case server port is closed we will get ConnectionRedusedError, try again
            try:
                self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sckt.connect((dataTCP, self.ip_port))
                print("\nTCP connected")
                self.connected = True
                self.sckt.setblocking(False)
                break
            except ConnectionRefusedError as e:
                time.sleep(1)
                print(e)
                pass

    # clear queue + parse data
    def manage_master_commands(self):
        try:
            if not self.unparsed_queue.empty():
                serverData = self.unparsed_queue.get()
                # self.xbee_node.broadCast(serverData) # master to slaves via xbee
                self.xbee_node.bc_q.put(serverData)
                self.parse_data(serverData)

            msg = self.sckt.recv(1024).decode()
            if len(msg) == 0:
                self.connected = False
                print("\nConnection to server has dropped!")
            else:
                self.unparsed_queue.put(msg)
        except IOError:
            pass

    def manage_slave_commands(self):
        try:
            if not self.unparsed_queue.empty():
                self.parse_data(self.unparsed_queue.get())
            if not self.xbee_node.q_to_pop.empty():
                self.unparsed_queue.put(self.xbee_node.q_to_pop.get())
        except IOError:
            pass

    def parse_data(self, data):
        data_list = data.split(",")
        command = data_list[0]

        if command == "!STOP":
            print("gpg stop")
            self.gpg.stop()
        elif command == "!TRI":
            print("tri")
            self.formation_q.put(command)
        elif command == "!SNAKE":
            print("snake")
            self.formation_q.put(command)
        elif command == "!HORI":
            print("hori")
            self.formation_q.put(command)
        elif command == "!MANUAL":
            print("MANUAL")
            # the numbers coming in should be integers, but aren't always
            x_speed = int(float(data_list[1]))
            y_speed = int(float(data_list[2]))
            # adjust to proper speeds
            if x_speed == 0 and y_speed == 0:
                self.gpg.stop()
            elif x_speed == 0:
                self.gpg.rotate_right_forever()
            elif y_speed == 0:
                self.gpg.rotate_left_forever()
            else:
                self.gpg.set_left_wheel(abs(x_speed))
                self.gpg.set_right_wheel(abs(y_speed))
                if y_speed > 25 and x_speed > 25:
                    self.gpg.backward()
                else:
                    self.gpg.forward()
        elif command == "!REBOOT":
            try:
                print("rebooting")
                if self.is_master:
                    self.sckt.close()
                self.is_master = False
                self.formation_q.put("!NOT_MASTER")
                self.xbee_discover_done = False
                self.xbee_node.discover_done = False
                self.connected = False
            except Exception as e:
                print(e)
                pass
        elif command == "!AUTO":
            # Test code
            self.gpg.drive_cm(30, True)
            self.gpg.rotate_left(360, True)
            self.gpg.drive_cm(-30, True)

            # self.gpg.drive_cm(30, True)
            # self.gpg.rotate_left(90, True)
            # self.gpg.drive_cm(30, True)
            # self.gpg.rotate_right(270, True)
            # self.gpg.drive_cm(40, True)

            # x = float(data_list[1])
            # y = float(data_list[2])
            # coord = Vector(x, y)
            # self.gps.goto_point(coord)
        else:
            print("[UNDEFINED] ", data)


if __name__ == '__main__':
    client = Client()
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()
