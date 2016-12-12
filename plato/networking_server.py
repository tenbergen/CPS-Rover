#!/usr/bin/python           # This is server.py file

import socket               # Import socket module
import gopigo
from Intersection import *

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
turnList = [Intersection(True, False, False, False), Intersection(False, True, False, False), Intersection(True, False, False, False)]
port = 12345                # Reserve a port for your service.
s.bind(('192.168.1.109', port))        # Bind to the port
print(host)

s.listen(5)                 # Now wait for client connection.
while True:
   c, addr = s.accept()     # Establish connection with client.
   print 'Got connection from', addr
   c.send(turnList)
   c.close()
