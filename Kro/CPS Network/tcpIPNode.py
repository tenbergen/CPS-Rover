import socket
from subprocess import check_output

class TCP_IP_Node:
    # the contructor method takes port number as an argument and intializes the port, IPAddrs and tcpSocket attributes.
    def __init__(self, port):
        self.port = port
        self.IPAddrs = check_output(['hostname', '-I']).decode().strip(' \n') # the IPAddrs attribute is bind IP address of the local device
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # creates a new socket object using the TCP protocol for network communication

    # method that makes the tcp socket a client that connects to the server of a given IP address and port number
    def tcp_ip_connect(self, IPAddrs, port):
        self.tcpSocket.connect((IPAddrs, port))

    # method that enables the tcp socket to listen to and accept connections. In other words, making the tcp socket a server socket that listens for incoming connections from clients
    def tcp_ip_accept(self):
        self.tcpSocket.listen(1)
        client, clientAddrs = self.tcpSocket.accept()
        return client, clientAddrs

    # method that binds an IP address and port to the tcp socket before the socket can listen and accept connections
    def tcp_ip_bind(self):
        self.tcpSocket.bind((self.IPAddrs, self.port))