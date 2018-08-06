import socket
from picamera import PiCamera
import io
from threading import Thread
import struct


# this class maintains a small video server that streams from the camera on a pi
class VideoServer(Thread):

    def __init__(self):
        Thread.__init__(self)

        # get the connection
        print("awaiting camera connection")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("dante.local", 10001))
        self.server.listen(0)
        self.connection = self.server.accept()[0].makefile('wb')
        print("Camera Server connected!")

        # setup the camera
        self.camera = PiCamera()
        self.camera.rotation = 180          # Dante's camera is upside down
        self.camera.resolution = (320,240)
        self.can_run = True

    # Run the thread
    def run(self):

        try:
            # create our IO stream
            stream = io.BytesIO()

            # while we don't want to quit
            while self.can_run:

                # capture EVERY thread from the stream
                for c in self.camera.capture_continuous(stream, 'jpeg', use_video_port=True):

                    # send the info over
                    self.connection.write(struct.pack('<L', stream.tell()))
                    self.connection.flush()
                    stream.seek(0)
                    self.connection.write(stream.read())

                    # prep for the next frame
                    stream.seek(0)
                    stream.truncate()

                # we're done with the package
                self.connection.write(struct.pack('<L', 0))
        except:
            print("Clumsy Exit")
        finally:
            self.connection.flush()
            self.connection.close()
            self.server.close()
