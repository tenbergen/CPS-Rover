from digi.xbee.devices import XBeeDevice
import threading
import queue
import time


class XbeeMesh(threading.Thread):

    def __init__(self, name, port, baud_rate):
        super(XbeeMesh, self).__init__()
        self._stop_event = threading.Event()

        self._name = name
        self._port = port
        self._baud_rate = baud_rate

        self._robotList = []
        self._macInt_list = []  # store int value of mac address of all robots in the network
        self._commandQueue = queue.Queue()
        self.discover_done = False

        # start up xbee
        self._device = XBeeDevice(self._port, self._baud_rate)
        self._device.open()

        # store local address into list for later comparison
        self._localMac = str(self._device.get_64bit_addr())
        self.localMac_int = int(self._localMac, 16)
        self._robotList.append([self._name, self.localMac_int])
        self._macInt_list.append(self.localMac_int)

        self.discover_broadcastMsg = "BC," + self._name + "," + self._localMac

        self.q_to_pop = queue.Queue()
        self.bc_q = queue.Queue()
        self.formation_q = queue.Queue()

    def _mac_to_int(self, address):
        return int(str(address), 16)

    def _data_parser(self, xbee_message):
        data = xbee_message.data.decode("utf-8")
        comma_list = data.split(",")
        # semicolon_list = data.split(";")

        if comma_list[0] == "BC":
            robotName = comma_list[1]
            mac_addr = comma_list[2]
            mac_addr_int = self._mac_to_int(mac_addr)

            self._robotList.append([robotName, mac_addr_int]) if [robotName,
                                                                  mac_addr_int] not in self._robotList else self._robotList
            self._macInt_list.append(mac_addr_int) if mac_addr_int not in self._macInt_list else self._macInt_list
        elif comma_list[0] == "UPDATE":
            self.formation_q.put(data)
        else:  # command is not for us, dont store this command and pass
            self.q_to_pop.put(data)

    def check_master(self):
        if max(self._macInt_list) == self.localMac_int:
            return True

    def get_robot_list(self):
        return self._robotList

    def broadCast(self, msg):
        try:
            self._device.send_data_broadcast(msg)
        except Exception as e:
            print(e)
            pass

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):

        while not self.stopped():

            while not self.discover_done:
                try:
                    self.broadCast(self.discover_broadcastMsg)
                    print("\n[Discoverd robots:]", self.get_robot_list())
                    data = self._device.read_data(2)
                    self._data_parser(data)
                    time.sleep(2)
                except Exception as e:
                    # print(e)
                    pass
            # print("xbee discover done")

            try:
                while not self.bc_q.empty():
                    self.broadCast(self.bc_q.get())
                    time.sleep(0.05)
                data = self._device.read_data()
                self._data_parser(data)
            except Exception as e:
                # print(e)
                pass

        print("XBee thread stopped")

        # Tests:
        # self._device.add_data_received_callback(self._data_parser)
        # while not self.stopped():
        #     try:
        #         self._device.send_data_broadcast(self._broadcastMsg)
        #     except Exception:
        #         pass
        #
        #     # print("broadcast sent")
        #     # print(self._robotList)
        #     # print(self._macInt_list)
        #     # if self._check_master():
        #     #     print("          "+self._name+ " is the master")
        #     # else:
        #     #     print("          "+self._name+" is not the master")
        #
        # print("XbeeMesh thread stopped")
