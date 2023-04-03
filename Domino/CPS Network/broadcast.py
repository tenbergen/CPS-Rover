import socket

class Broadcast:
    # the constructor method that takes port number as an argument
    def __init__(self, port):
        self.port = port
        # socket that is used for broadcasting
        self.broadcaster = self.broadcast_socket()
        # socket used to receive message from boradcast
        self.broadcastReceiver = self.broadcast_socket()
        self.broadcastReceiver.bind(('',self.port))

    # creating a broadcast socket
    def broadcast_socket(self):
        # Initialize socket
        b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Enable broadcast mode
        b.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return b

    # send to broadcast method
    def send_to_broadcast(self, message):
        broadcastIP = '<broadcast>'
        self.broadcaster.sendto(message.encode(), (broadcastIP, self.port))

    # receive from braodcast method
    def read_from_broadcast(self):
        data, addr = self.broadcastReceiver.recvfrom(1024)
        return data, addr