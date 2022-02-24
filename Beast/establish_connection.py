import socket
from subprocess import check_output

class EstablishConnection:
    role = None
    def __init__(self):
        localIP = check_output(['hostname', '-I']).decode().strip(' \n') # getting the local IP address name
        port = 8081
        #initialize and enable braodcast
        b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        b.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        b.bind(("", port))
        #initialize server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((localIP, port))
        #initialize client
        cl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            #send local IP address to broadcast
            b.sendto(localIP.encode(), ('255.255.255.255', port))
            #server listens for connection
            s.listen(1)
            #set timeout for the accept blocking method
            s.settimeout(1)
            try:
                c, cAddr = s.accept()
            except socket.timeout:
                c = None
            #if no connection is detected...
            if c is None:
                #recieve message from broadcast
                data, addr = b.recvfrom(1024)
                print(data.decode())
                #if message from broadcast is not the local IP address of current device...
                if data.decode() != localIP:
                    #connect to that IP address as client and sent a successfully connected message and break loop
                    cl.connect((data.decode(), port))
                    message = "server"
                    cl.send(message.encode())
                    self.role = cl
                    break
            #else connection is detected. Print recieved message and break loop
            else:
                msg = c.recv(1024).decode()
                print(msg)
                self.role = c
                break
        


