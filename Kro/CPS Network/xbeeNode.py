from digi.xbee.devices import *
import json

class XbeeNode:
    # the constructor method initializes and creates a new xbee xbee device object
    def __init__(self):
        self.xbee = XBeeDevice("/dev/ttyUSB0", 9600)
        self.xbee.open()
        self.xbeeAddrs = str(self.xbee.get_64bit_addr())
        timeout = 100000000
        self.xbee.set_sync_ops_timeout(timeout)

    # this method takes an IP address as an argument and sends that IP address to the broadcast of the xbee network
    def xbee_broadcast_addrs(self, ipAddrs):
        addrs = "addr:" + self.xbeeAddrs + ":" + ipAddrs
        self.xbee.send_data_broadcast(addrs)

    # this method takes some telemetry information as an argument and sends it to the broadcast of the xbee network
    def xbee_broadcast_telemetry(self, telemetry):
        t = json.dumps(telemetry)
        msg = "info:" + t
        self.xbee.send_data_broadcast(msg)

    # this method is used to read data from an xbee module
    def xbee_connection_listener(self):
        msg = self.xbee.read_data()
        return msg

    
