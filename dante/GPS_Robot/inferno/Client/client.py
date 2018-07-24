import pygame
import socket
from PyQt5.QtCore import QThread,pyqtSignal,Qt
from PyQt5.QtGui import QImage
import select
from vector import Vector
import struct
import cv2
import io
import numpy as np
import time

class Client(QThread):
    on_rover_position_changed = pyqtSignal(Vector)
    on_destination_reached = pyqtSignal()
    on_node_changed = pyqtSignal(Vector, int)
    on_path_changed = pyqtSignal(list)
    on_simple_path_changed = pyqtSignal(list)

    def __init__(self, send_queue):
        QThread.__init__(self)

        #set up controller
        self.joysticks = []
        pygame.display.init()
        pygame.joystick.init()
        # stores all connected controllers
        for i in range(0, pygame.joystick.get_count()):
            self.joysticks.append(pygame.joystick.Joystick(i))
            self.joysticks[-1].init()
        self.clock = pygame.time.Clock()

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.can_run = True
        self.remote_on = False
        self.send_queue = send_queue
        #self.socket.connect(("dante.local", 10000))


    def connect_to_server(self, host, port):
        try:
            self.socket.connect(("dante.local", 10000))
        except Exception as e:
            print(e)

    def run(self):
        self.socket.connect(("dante.local", 10000))
        while self.can_run:
            r, _, _ = select.select([self.socket], [], [], .1)
            if r:
                data = self.socket.recv(1024).decode('utf-8').split()
                print(data)
                self.parse_data(data)

            while not self.send_queue.empty():
                data = self.send_queue.get()
                self.send_message(data)

            if self.remote_on:
                self.handle_controller_events()
        self.socket.close()

    def handle_controller_events(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.send_message("LON")
                elif event.button == 6:
                    running = False #TODO this should quit the GUI client at some point
                # elif event.button == 8:
                # send_message("Home")
                elif event.button == 11:
                    self.send_message("S")
            elif event.type == pygame.JOYAXISMOTION:
                if 0 != self.joysticks[0].get_axis(0) or 0 != self.joysticks[0].get_axis(1):
                    x = float(self.joysticks[0].get_axis(0))
                    y = float(self.joysticks[0].get_axis(1))
                    if -0.03 < x < 0.03 and -0.03 < y < 0.03:
                        # stopped
                        curx = 0
                        cury = 0
                    elif -0.03 < y < 0.03:
                        # turning
                        if x < 0:
                            curx = 0
                            cury = int(x * 250)
                        else:
                            curx = int(x * 250)
                            cury = 0
                    elif -0.03 < x < 0.03:
                        # straight
                        curx = int(y * 250)
                        cury = int(y * 250)
                    else:
                        # diagonal
                        if x < 0.03 and y < 0.03:
                            cury = - int((abs(x) + abs(y)) * 250)
                            if cury < -250:
                                cury = -250
                            curx = int((x - y) * cury)
                            curx = - ((curx + cury) / 2)
                        elif x < 0.03 and y > 0.03:
                            cury = int((abs(x) + abs(y)) * 250)
                            if cury > 250:
                                cury = 250
                            curx = int((x + y) * cury)
                            curx = ((curx + cury) / 2)
                        elif x > 0.03 and y < 0.03:
                            curx = - int((abs(x) + abs(y)) * 250)
                            if curx < -250:
                                curx = -250
                            cury = int((x + y) * 250)
                            cury = ((cury - 250) / 2)
                        elif x > 0.03 and y > 0.03:
                            curx = int((abs(x) + abs(y)) * 250)
                            if curx > 250:
                                curx = 250
                            cury = int((y - x) * curx)
                            cury = ((cury + curx) / 2)
                    self.send_message("M " + str(curx) + " " + str(cury))

            elif event.type == pygame.JOYBUTTONUP:
                if event.button == 13 or event.button == 14 or event.button == 15 or event.button == 16:
                    self.send_message("S")
                elif event.button == 0:
                    self.send_message("LOFF")

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

    def send_message(self, message):
        # puts a message in the send queue
        self.socket.send((" " + message).encode())

    def __del__(self):
        self.wait()


class VideoStream(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self):
        QThread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.can_run = True

    def run(self):
        self.socket.connect(("dante.local", 10001))
        connection = self.socket.makefile('rb')
        cap = cv2.VideoCapture(0)
        while self.can_run:
            time.sleep(1./25)
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]

            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            image_stream.seek(0)
            file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes,cv2.IMREAD_COLOR)
            rgbImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            convertToQtFormat = QImage(rgbImage.data, rgbImage.shape[1], rgbImage.shape[0], QImage.Format_RGB888)
            p = convertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
            self.changePixmap.emit(p)
        self.socket.close()