import socket
from picamera import PiCamera
import io
#import cv2
import numpy as np
from threading import Thread
import struct
import time

class VideoServer(Thread):

    def __init__(self):
        Thread.__init__(self)
        print("awaiting camera connection")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("dante.local",10001))
        self.server.listen(0)
        print("Camera Server connected!")
        self.connection = self.server.accept()[0].makefile('wb')

        self.camera = PiCamera()
        self.camera.rotation = 180
        self.camera.resolution = (320,240)
        #self.camera.framerate = 24
        self.can_run = True

    def run(self):
        try:
            #self.camera.start_recording(self.connection,"h264")
            start = time.time()
            stream = io.BytesIO()
            while self.can_run:
                #print("starting Capture")
                for c in self.camera.capture_continuous(stream,'jpeg',use_video_port=True):
                    #print("capture")
                    self.connection.write(struct.pack('<L',stream.tell()))
                    self.connection.flush()
                    stream.seek(0)
                    self.connection.write(stream.read())

                    stream.seek(0)
                    stream.truncate()
                self.connection.write(struct.pack('<L',0))
        finally:
            #self.camera.stop_recording()
            self.connection.flush()
            self.connection.close()
            self.server.close()
