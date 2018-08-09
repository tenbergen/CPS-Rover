import pygame
import socket
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
import select
from vector import Vector
import struct
import cv2
import io
import numpy as np
import traceback


# This class handles GUI and controller data being sent over a connection along with responses received from the server.
class Client(QThread):
    # Signal events
    on_rover_position_changed = pyqtSignal(Vector)
    on_destination_reached = pyqtSignal()
    on_node_changed = pyqtSignal(Vector, int)
    on_path_changed = pyqtSignal(list)
    on_simple_path_changed = pyqtSignal(list)
    on_camera_button_pressed = pyqtSignal()
    on_go_home_pressed = pyqtSignal()
    on_auto_switch = pyqtSignal()

    def __init__(self, send_queue):
        QThread.__init__(self)

        # set up controller
        self.joysticks = []
        pygame.display.init()
        pygame.joystick.init()

        # store all connected controllers
        for i in range(0, pygame.joystick.get_count()):
            self.joysticks.append(pygame.joystick.Joystick(i))
            self.joysticks[-1].init()
        self.clock = pygame.time.Clock()

        # start the server
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.can_run = True
        self.remote_on = False
        self.send_queue = send_queue

    # establish a connection to the server
    def connect_to_server(self):
        try:
            self.socket.connect(("dante.local", 10000))
        except Exception as e:
            print(e)

    # loop for thread execution
    def run(self):

        # while we aren't closing the thread
        while self.can_run:

            # get some data from the connection
            r, _, _ = select.select([self.socket], [], [], .1)
            if r:
                # parse the data
                data = self.socket.recv(1024).decode('utf-8').split()
                print(data)
                self.parse_data(data)

            # send data over the connection
            while not self.send_queue.empty():
                data = self.send_queue.get()
                self.send_message(data)

            # if the controller is active, send pygame events
            self.handle_controller_events()

        self.socket.close()

    # this method handles controller events
    # Left analog stick: control movement
    # A:                 turn on eyes/LEDS
    # B:                 stop gpg
    # Y:                 send gpg home
    # X:                 Camera on/off
    # start:             turn auto on/off
    def handle_controller_events(self):
        try:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 7:
                        self.on_auto_switch.emit()
                if self.remote_on:
                    # handle button presses
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 0:
                            self.send_message("LON")
                        elif event.button == 1:
                            self.send_message("S")
                        elif event.button == 2:
                            self.on_camera_button_pressed.emit()
                        elif event.button == 3:
                            self.on_go_home_pressed.emit()

                    # handle axis movement
                    elif event.type == pygame.JOYAXISMOTION:
                        if 0 != self.joysticks[0].get_axis(0) or 0 != self.joysticks[0].get_axis(1):
                            x = float(self.joysticks[0].get_axis(0))
                            y = float(self.joysticks[0].get_axis(1))
                            cur_x = 0
                            cur_y = 0
                            if -0.03 < x < 0.03 and -0.03 < y < 0.03:
                                # stopped
                                cur_x = 0
                                cur_y = 0
                            elif -0.03 < y < 0.03:
                                # turning
                                if x < 0:
                                    cur_x = 0
                                    cur_y = int(y * 250)
                                else:
                                    cur_x = int(x * 250)
                                    cur_y = 0
                            elif -0.03 < x < 0.03:
                                # straight
                                cur_x = int(y * 250)
                                cur_y = int(y * 250)
                            else:
                                # diagonal
                                if x < 0.03 and y < 0.03:
                                    cur_y = - int((abs(x) + abs(y)) * 250)
                                    if cur_y < -250:
                                        cur_y = -250
                                    cur_x = int((x - y) * cur_y)
                                    cur_x = - ((cur_x + cur_y) / 2)
                                elif x < 0.03 < y:
                                    cur_y = int((abs(x) + abs(y)) * 250)
                                    if cur_y > 250:
                                        cur_y = 250
                                    cur_x = int((x + y) * cur_y)
                                    cur_x = ((cur_x + cur_y) / 2)
                                elif x > 0.03 > y:
                                    cur_x = - int((abs(x) + abs(y)) * 250)
                                    if cur_x < -250:
                                        cur_x = -250
                                    cur_y = int((x + y) * 250)
                                    cur_y = ((cur_y - 250) / 2)
                                elif x > 0.03 and y > 0.03:
                                    cur_x = int((abs(x) + abs(y)) * 250)
                                    if cur_x > 250:
                                        cur_x = 250
                                    cur_y = int((y - x) * cur_x)
                                    cur_y = ((cur_y + cur_x) / 2)
                            self.send_message("M " + str(cur_x) + " " + str(cur_y))

                    # handle button release
                    elif event.type == pygame.JOYBUTTONUP:
                        if event.button == 13 or event.button == 14 or event.button == 15 or event.button == 16:
                            self.send_message("S")
                        elif event.button == 0:
                            self.send_message("LOFF")

                    if not self.remote_on:
                        break
        except:
            print(traceback.format_exc())

    # Parses incoming data to send back to the GUI
    def parse_data(self, data):

        while len(data) > 0:
            command = data.pop(0)

            # R- rover position
            if command == 'R':
                x = int(data.pop(0))
                y = int(data.pop(0))

                position = Vector(x, y)
                self.on_rover_position_changed.emit(position)

            # DR - Destination reached
            elif command == 'DR':

                self.on_destination_reached.emit()

            # N  - node information
            elif command == 'N':
                x = int(data.pop(0))
                y = int(data.pop(0))
                node_type = int(data.pop(0))

                position = Vector(x, y)
                self.on_node_changed.emit(position, node_type)

            # SP - simple path
            elif command == 'SP':
                path = []
                e = data.pop(0)
                while e != 'D':
                    x = int(e)
                    y = int(data.pop(0))
                    position = Vector(x, y)
                    path.append(position)
                    e = data.pop(0)

                self.on_simple_path_changed.emit(path)

            # FP - full path
            elif command == 'FP':
                path = []
                e = data.pop(0)
                while e != 'D':
                    x = int(e)
                    y = int(data.pop(0))
                    position = Vector(x, y)
                    path.append(position)
                    e = data.pop(0)

                self.on_path_changed.emit(path)

    # send message through the connection.
    def send_message(self, message):
        # puts a message in the send queue
        self.socket.send((" " + message).encode())

    def __del__(self):
        self.wait()


# this class continually updates the image from the video information being send over.
class VideoStream(QThread):
    changePixmap = pyqtSignal(QImage)

    # setup received connection
    def __init__(self):
        QThread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.can_run = True

    # attempt a connection to the server
    def connect_to_server(self):
        try:
            self.socket.connect(("dante.local", 10001))
        except Exception as e:
            print(e)

    # thread loop
    def run(self):

        # treat the socket connection as a file
        connection = self.socket.makefile('rb')
        cv2.VideoCapture(0)

        # while we are allowed to run
        while self.can_run:

            # start unpacking data
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            image_stream.seek(0)
            file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)

            # convert bytes into an image
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            convert_to_qt_format = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], QImage.Format_RGB888)
            p = convert_to_qt_format.scaled(480, 320, Qt.KeepAspectRatio)

            # if we are allowed to run, update the image
            if self.can_run:
                self.changePixmap.emit(p)
        self.socket.close()
