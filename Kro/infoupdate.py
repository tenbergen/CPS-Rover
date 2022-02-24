import socket
import pickle
from marvelmind import MarvelmindHedge
from establish_connection import EstablishConnection


class InfoUpdate:
    con = EstablishConnection() #establishing the TCP/IP connection
    hedge = MarvelmindHedge(tty = "/dev/ttyACM0", adr = 10, debug = False) # establishing the hedge. The adr may be modified depending on the adr listed on your map.
    position = None
    otherPos = None
    
    # the constructor starts the hedge so that the location telemetry of the hedge can be retrieved
    def __init__(self):
        self.hedge.start()
       
    # the getUpdatedPosition method gets the position of the hedge if the position is updated and sends 
    # it to the other hedge via the TCP/IP connection that was already established and then returns the position    
    def getUpdatedPosition(self):
        if (self.hedge.positionUpdated):
            self.position = self.hedge.position()
        pos = pickle.dumps(self.position)
        self.con.role.send(pos)
        return self.position
    
    # the getOtherUpdatedPos method tries to recieve location telemetry from the other hedge via their TCP/IP connection
    # if an information is recieved before the timeout, decode the information using pickle.loads and set it to the 
    # otherPos variable. Else meaning that there is no information recieved so the otherPos variable is set to None.
    def getOtherUpdatedPos(self):
        self.con.role.settimeout(1)
        try:
            self.otherPos = self.con.role.recv(1024)
        except socket.timeout:
            self.otherPos = None
        if self.otherPos is not None:
            self.otherPos = pickle.loads(self.otherPos)
        return self.otherPos
    
    # getDistances method simply calls the distances method from the marvelmind library to get the distances between the
    # hedge and other hedges or beacons in the map.
    def getDistances(self):
        return self.hedge.distances()
