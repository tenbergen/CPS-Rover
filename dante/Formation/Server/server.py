import socket
import time
import subprocess
import re
import queue

from PyQt5.QtCore import *


class Server(QThread):
    tcp_connected = pyqtSignal()
    tcp_disconnected = pyqtSignal()
    handle_controller = pyqtSignal()

    def __init__(self, ip_port):
        QThread.__init__(self)

        self.ip_port = ip_port
        self.ip_addr = ""

        self.sckt = None
        self.broadcast = None

        self.client_sock = None
        self.q_to_send = queue.Queue()

        self.stopped = False
        self.enable_manual = False

    def get_ip_addr(self):
        pattern = r'inet (?:addr:)?(?!127\.0\.0\.1)((?:\d+\.){3}\d+)'
        p = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE)
        self.ip_addr = re.search(pattern, p.stdout.read().decode()).group(1)
        print("server ip", self.ip_addr)

    def set_up_tcp(self):
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sckt.settimeout(0.5)
        self.sckt.bind((self.ip_addr, self.ip_port))
        self.sckt.listen(5)

    def broadcast_udp(self):
        self.broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast.sendto(bytes(self.ip_addr, encoding='utf-8'), ("<broadcast>", self.ip_port))
        print("UDP broadcast sent!")

    def connected(self):
        self.broadcast.close()
        self.client_sock.setblocking(False)

    # def stop(self):
    #     self._stop_event.set()
    #     print("Stopping server thread...")
    #
    # def stopped(self):
    #     return self._stop_event.is_set()

    def run(self):
        self.get_ip_addr()
        self.set_up_tcp()
        while not self.stopped:

            while True:
                self.broadcast_udp()
                time.sleep(1)
                try:
                    self.client_sock, _ = self.sckt.accept()
                    print("\nA client has connected!")
                    break
                except socket.timeout:
                    print("socket timeout")
                    pass
            self.connected()
            # print(self.client_sock.getpeername()[0])
            self.tcp_connected.emit()
            print("Switched to TCP")

            while True:
                if self.enable_manual:
                    self.handle_controller.emit()
                try:
                    time.sleep(0.01)
                    if self.q_to_send.empty():
                        pass
                    else:
                        msg = self.q_to_send.get()
                        self.client_sock.send(bytes(msg, "utf8"))
                        print("'" + msg + "'" + " sent")
                    if self.stopped:
                        break
                except socket.error:
                    print("\nClient disconnected! Now broadcasting UDP")
                    self.tcp_disconnected.emit()
                    break
