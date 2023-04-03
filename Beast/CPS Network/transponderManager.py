from broadcast import Broadcast
from tcpIPNode import TCP_IP_Node
from xbeeNode import XbeeNode
from subprocess import check_output
from queue import Queue
from digi.xbee.devices import *
import time
import threading
import socket
import json

# a threading function that takes a Broadcast object and a port number as its arguments and broadcast the port number every second
def broadcasting(broadcast, port):
    while True:
        msg = str(port)
        broadcast.send_to_broadcast(msg)
        time.sleep(1)

# a threading function that creates TCP/IP connections with other devices on the network that are not already connected by finding the devices on the network via braodcast
# the function takes the following arguments: lock (the lock from the threading module), broadcast (a Broadcsat object), port (a port number), tcpIpConnectionList (a list), and collectionOfTelemetryInfo (a list)
def establish_tcp_ip_connection(lock, broadcast, port, tcpIpConnectionList, collectionOfTelemetryInfo):
    while True:
        msg, addrs = broadcast.read_from_broadcast()
        connectingIPAddrs = addrs[0]
        connectingPort = int(msg.decode())
        tcpIPNode = TCP_IP_Node(port)
        if (tcpIPNode.IPAddrs != connectingIPAddrs) and (connectingIPAddrs not in tcpIpConnectionList):
            try:
                tcpIPNode.tcp_ip_connect(connectingIPAddrs, connectingPort)
                lock.acquire()
                tcpIpConnectionList.append(connectingIPAddrs)
                lock.release()
                print("(TCP/IP) Connected to: " + connectingIPAddrs)
                print("(TCP/IP) Number of connected device: " + str(len(tcpIpConnectionList)))
                sendThread = threading.Thread(target=telemetry_send_via_tcp_ip, args=(tcpIPNode.tcpSocket, connectingIPAddrs, tcpIpConnectionList, collectionOfTelemetryInfo, ))
                receiveThread = threading.Thread(target=telemetry_receive_via_tcp_ip, args=(lock, tcpIPNode.tcpSocket, tcpIPNode.IPAddrs, connectingIPAddrs, tcpIpConnectionList, collectionOfTelemetryInfo, ))
                sendThread.start()
                receiveThread.start()
            except ConnectionRefusedError:
                print("(TCP/IP) Connection Refused From " + connectingIPAddrs)
        time.sleep(0.1)

# a threading function that acts as a server that listens for connections and accepts connections from clients that are not yet already connected via TCP/IP
# the function takes the following arguments: lock (the lock from the threading module), port (a port number), tcpIpConnectionList (a list), and collectionOfTelemetryInfo (a list)
def tcp_ip_connection_listener(lock, port, tcpIpConnectionList, collectionOfTelemetryInfo):
    tcpIPNode = TCP_IP_Node(port)
    tcpIPNode.tcp_ip_bind()
    while True:
        client, clientAddrs = tcpIPNode.tcp_ip_accept()
        clientIPAddrs = clientAddrs[0]
        if clientIPAddrs not in tcpIpConnectionList:
            lock.acquire()
            tcpIpConnectionList.append(clientIPAddrs)
            lock.release()
            print("(TCP/IP) Connected to: " + clientIPAddrs)
            print("(TCP/IP) Number of connected device: " + str(len(tcpIpConnectionList)))
            sendThread = threading.Thread(target=telemetry_send_via_tcp_ip, args=(client, clientIPAddrs, tcpIpConnectionList, collectionOfTelemetryInfo, ))
            receiveThread = threading.Thread(target=telemetry_receive_via_tcp_ip, args=(lock, client, tcpIPNode.IPAddrs, clientIPAddrs, tcpIpConnectionList, collectionOfTelemetryInfo, ))
            sendThread.start()
            receiveThread.start()
        else:
            client.close()
        time.sleep(0.1)

# a threading function that send telemetry information to a given IP address every half a second via TCP/IP while the device of the IP address is still connected to the network
# the function takes the following arguments: tcpIpNode (a TCP_IP_Node object), clientIp (IP address of the connecting device), tcpIpConnectionList (a list), and collectionOfTelemetryInfo (a list)
def telemetry_send_via_tcp_ip(tcpIpNode, clientIp, tcpIpConnectionList, collectionOfTelemetryInfo):
    while clientIp in tcpIpConnectionList:
        msg = json.dumps(collectionOfTelemetryInfo)
        try:
            tcpIpNode.send(msg.encode())
        except (ConnectionResetError, BrokenPipeError, socket.timeout):
            break
        time.sleep(0.5)
    
# a threading function that listens for and receives telemetry information from a connected device on the network via TCP/IP
# the thread stops when no information is recieved from the connected device within 5 seconds, signaling a disconnection
# the function takes the following arguments: lock (the lock from the threading module), tcpIpNode (a TCP_IP_Node object), selfIp (IP address of the local device), ipAddrs (IP address of the connecting device), tcpIpConnectionList (a list), and collectionOfTelemetryInfo (a list)
def telemetry_receive_via_tcp_ip(lock, tcpIpNode, selfIp, ipAddrs, tcpIpConnectionList, collectionOfTelemetryInfo):
    while ipAddrs in tcpIpConnectionList:
        tcpIpNode.settimeout(5)
        try:
            data = tcpIpNode.recv(1024)
            if not data:
                break
            data = data.decode().split('}', 1)[0] + '}'
            data = json.loads(data)
            for k, v in data.items():
                if k != selfIp:
                    lock.acquire()
                    collectionOfTelemetryInfo[k] = v
                    lock.release()
        except (ConnectionResetError, BrokenPipeError, socket.timeout):
            break
    lock.acquire()
    tcpIpConnectionList.remove(ipAddrs)
    lock.release()
    print("(TCP/IP) Disconnected from: " + ipAddrs)
    print("(TCP/IP) Number of connected device: " + str(len(tcpIpConnectionList)))

# a threading function that takes the an XbeeNode object and an IP address as its parameters and broadcasts the IP address every second via XBee
def xbee_broadcast(xbeeNode, ipAddrs):
    time.sleep(2)
    while True:
        xbeeNode.xbee_broadcast_addrs(ipAddrs)
        time.sleep(1)

# a threading function that listens for and recieves message from the XBee module. If the message is an IP address, form a connection with device of the IP address if not already connected
# the function takes the following arguments: lock (the lock from the threading module), xbeeNode (an XbeeNode object), xbeeConnectionList (a list), tcpIpConnectionList (a list), q (a Queue object), collectionOfTelemetryInfo (a list), and selfIp (IP address of the local device)
def xbee_connection_maker(lock, xbeeNode, xbeeConnectionList, tcpIpConnectionList, q, collectionOfTelemetryInfo, selfIp):
    time.sleep(2)
    while True:
        msg = xbeeNode.xbee_connection_listener()
        if msg is not None:
            msg = msg.data.decode()
            key = "addr:"
            addrs = msg[len(key):len(msg)]
            separation = addrs.index(":")
            addrs64Bit = addrs[0:separation]
            IPAddrs = addrs[(separation + 1):len(addrs)]
            if (msg[0:len(key)] == key) and (IPAddrs not in xbeeConnectionList) and (IPAddrs not in tcpIpConnectionList):
                lock.acquire()
                xbeeConnectionList.append(IPAddrs)
                lock.release()
                print("(Xbee) Connected to: " + IPAddrs)
                print("(Xbee) Number of connected device: " + str(len(xbeeConnectionList)))
                xbeeThreadedConnection = threading.Thread(target=xbee_connection, args=(lock, xbeeNode, addrs64Bit, selfIp, IPAddrs, tcpIpConnectionList, xbeeConnectionList, q, collectionOfTelemetryInfo, ))
                xbeeThreadedConnection.start()
        time.sleep(0.5)

# the threading function that establishes a connection with another device discovered on the network. While connected the function also listens for and receives telemetry information from the connected XBee device
# the thread stops when the connection stopped or some sort of disconnection signal was received
# the function takes the following arguments: lock (the lock from the threading module), xbeeNode (an XbeeNode object), addrs64Bit (64 bit local XBee address), selfIp (IP address of the local device), IPAddrs (IP address of the connecting device), tcpIpConnectionList (a list), xbeeConnectionList (a list), q (a Queue object), and collectionOfTelemetryInfo (a list)
def xbee_connection(lock, xbeeNode, addrs64Bit, selfIp, IPAddrs, tcpIpConnectionList, xbeeConnectionList, q, collectionOfTelemetryInfo):
    remote = RemoteXBeeDevice(xbeeNode.xbee, XBee64BitAddress.from_hex_string(addrs64Bit))
    timeout = 5
    while (IPAddrs not in tcpIpConnectionList):
        try:
            msg = xbeeNode.xbee.read_data_from(remote, timeout)
            # read message received that is not broadcasted address. Broadcasted address always begins with "0013A2004"
            if msg is not None:
                lock.acquire()
                if q.full():
                    q.get()
                    q.put(msg.remote_device)
                    if remote not in q.queue:
                        lock.release()
                        break
                else:
                    q.put(msg.remote_device)
                    
                msg = msg.data.decode()
                key = "info:"
                if msg[0:len(key)] == key:
                    d = msg[len(key):len(msg)]
                    data = json.loads(d)
                    #combining the telemetry info received with locally known telemetry info
                    for k, v in data.items():
                        if k != selfIp:
                            collectionOfTelemetryInfo[k] = v
                lock.release()
        except Exception as e:
            print(e)
            break
        time.sleep(0.1)
    lock.acquire()
    xbeeConnectionList.remove(IPAddrs)
    lock.release()
    print("(Xbee) Threaded connection with " + IPAddrs + " stopped.")
    print("(Xbee) List of connected device: " + str(xbeeConnectionList))

# a threading function that takes the an XbeeNode object and a collectionOfTelemetryInfo (a list) as its parameters and broadcasts the collectionOfTelemetryInfo every second via XBee
def xbee_broadcast_telemetry(xbeeNode, collectionOfTelemetryInfo):
    time.sleep(2)
    while True:
        xbeeNode.xbee_broadcast_telemetry(collectionOfTelemetryInfo)
        time.sleep(1)

# a threading function that the user can interact with when prompt for a command
# Here are the list of commands and the kind of response the user receives:
# "data" - outputs a list of telemetry information of the connected devices in the network
# "tcpip" - outputs a list of IP addresses of the connected devices in the network that are communicating via TCP/IP
# "xbee" - outputs a list of IP addresses of the connected devices in the network that are communicating via XBee
# "help" - outputs the list of commands to use
def user_prompt(collectionOfTelemetryInfo, tcpIpConnectionList, xbeeConnectionList):
    time.sleep(2)
    while True:
        userInput = input("Please enter a command: ")
        print(userInput)
        if userInput == 'data':
            print(collectionOfTelemetryInfo)
        elif userInput == "tcpip":
            print(tcpIpConnectionList)
        elif userInput == "xbee":
            print(xbeeConnectionList)
        elif userInput == "help":
            print("Here are the commands to use:\n data\n tcpip\n xbee\n")
        else:
            print("Sorry this is not a valid command. Try again.")

# a temporary threading function that generate fake telemetry information (used for testing purposes). The correct telemetry information should be obtained from the marvelmind devices. This function shall be changed or removed in the future!!!!!!
def counter(lock, collectionOfTelemetryInfo, ipAddrs):
    i = 0
    while True:
        lock.acquire()
        collectionOfTelemetryInfo[ipAddrs] = str(i)
        lock.release()
        i+=1
        time.sleep(5)

# a function that starts all the thraeding functions
def start():
    broadcastPort = 8025
    tcpIpPort = 8026
    IPAddrs = check_output(['hostname', '-I']).decode().strip(' \n')
    lock = threading.Lock()
    b = Broadcast(broadcastPort)
    x = XbeeNode()
    queueSize = 10
    q = Queue(queueSize)
    tcpIpConnectionList = []
    xbeeConnectionList = []
    collectionOfTelemetryInfo = {}
    broadcastingThread = threading.Thread(target=broadcasting, args=(b, tcpIpPort, ))
    establishTcpIpConnectionThread = threading.Thread(target=establish_tcp_ip_connection, args=(lock, b, tcpIpPort, tcpIpConnectionList, collectionOfTelemetryInfo, ))
    tcpIpConnectionListenerThread = threading.Thread(target=tcp_ip_connection_listener, args=(lock, tcpIpPort, tcpIpConnectionList, collectionOfTelemetryInfo, ))
    xbeeBroadcastingThread = threading.Thread(target=xbee_broadcast, args=(x, IPAddrs, ))
    xbeeConnectionMakerThread = threading.Thread(target=xbee_connection_maker, args=(lock, x, xbeeConnectionList, tcpIpConnectionList, q, collectionOfTelemetryInfo, IPAddrs, ))
    xbeeBroadcastTelemetryThread = threading.Thread(target=xbee_broadcast_telemetry, args=(x, collectionOfTelemetryInfo, ))
    counterThread = threading.Thread(target=counter, args=(lock, collectionOfTelemetryInfo, IPAddrs))
    userPromptThread = threading.Thread(target=user_prompt, args=(collectionOfTelemetryInfo, tcpIpConnectionList, xbeeConnectionList, ))
    print("Local IP Address: " + IPAddrs)
    print("Establishing connections...")
    broadcastingThread.start()
    establishTcpIpConnectionThread.start()
    tcpIpConnectionListenerThread.start()
    xbeeBroadcastingThread.start()
    xbeeConnectionMakerThread.start()
    xbeeBroadcastTelemetryThread.start()
    counterThread.start()
    userPromptThread.start()
    

start()