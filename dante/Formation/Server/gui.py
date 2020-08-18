from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from form import Ui_guijunior
import sys
from server import Server
from time import sleep
import pygame
import traceback


class GUI(QMainWindow, Ui_guijunior):
    def __init__(self):
        super(GUI, self).__init__()

        # Set up the user interface from Designer.
        self.setupUi(self)

        # set up GUI signals
        self.start_button.clicked.connect(self.on_start)
        self.reboot_button.clicked.connect(self.on_reboot)
        self.reboot_button.setEnabled(False)
        self.apply_formation.clicked.connect(self.send_formation_message)
        self.stop_all_robots.clicked.connect(self.stop_robots)
        self.switch_to_manual.clicked.connect(self.on_manual)
        self.switch_to_automatic.clicked.connect(self.on_auto)

        # set up server
        self.server = Server(10000)
        self.server.tcp_connected.connect(self.on_tcp_connected)
        self.server.tcp_disconnected.connect(self.on_tcp_disconnected)
        self.server.handle_controller.connect(self.handle_controller_events)

        # set up controller
        pygame.init()
        self.joysticks = []
        pygame.display.init()
        pygame.joystick.init()
        self.last_control_msg = None
        # store all connected controllers
        for i in range(0, pygame.joystick.get_count()):
            self.joysticks.append(pygame.joystick.Joystick(i))
            self.joysticks[-1].init()
        self.clock = pygame.time.Clock()

    def on_start(self):
        pygame.init()
        self.server.start()
        self.start_button.setEnabled(False)
        self.reboot_button.setEnabled(True)

    def on_reboot(self):
        buttonReply = QMessageBox.warning(self, '', "Warning, rebooting mesh network will lose connection briefly",
                                          QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if buttonReply == QMessageBox.Yes:
            self.server.q_to_send.put("!REBOOT")
            self.start_button.setStyleSheet("color: rgb(255, 35, 15);")
            self.start_button.setText("Disconnected!\nReconnecting...")
            self.reboot_server()
        else:
            pass

    def reboot_server(self):
        print("rebooting server")
        self.server.stopped = True
        self.server.quit()
        sleep(1)
        self.server.stopped = False
        self.on_start()

    def send_formation_message(self):
        if self.line_formation_snake.isChecked():
            self.server.q_to_send.put("!SNAKE")
        elif self.line_formation_horizontal.isChecked():
            self.server.q_to_send.put("!HORI")
        elif self.trangle_formation.isChecked():
            self.server.q_to_send.put("!TRI")
        else:
            pass

    def stop_robots(self):
        self.server.q_to_send.put("!STOP")

    def on_tcp_connected(self):
        print("[GUI] tcp connected")
        self.start_button.setStyleSheet("color: rgb(0, 230, 0);")
        self.start_button.setText("Connected!")

    def on_tcp_disconnected(self):
        print("[GUI] tcp disconnected")
        self.start_button.setStyleSheet("color: rgb(255, 35, 15);")
        self.start_button.setText("Disconnected!\nReconnecting...")

    def on_manual(self):
        self.server.enable_manual = True
        self.switch_to_manual.setFocus()

    def on_auto(self):
        self.server.enable_manual = False
        self.switch_to_automatic.setFocus()
        self.server.q_to_send.put("!AUTO,1,1")

    # JohnZ - on macOS pygame must be running from main thread
    # only for sending controller events
    def send_control_message(self, message):
        # puts a message in the send queue
        self.server.q_to_send.put(message)
        # self.socket.send((" " + message).encode())

    def handle_controller_events(self):
        DEADZONE = 0.8
        try:
            for event in pygame.event.get():
                # handle axis movement
                if event.type == pygame.JOYAXISMOTION:
                    print("joymoton")
                    if 0 != self.joysticks[0].get_axis(0) or 0 != self.joysticks[0].get_axis(1):
                        x = float(self.joysticks[0].get_axis(0))
                        y = float(self.joysticks[0].get_axis(1))
                        print(x, y)
                        cur_x = 0
                        cur_y = 0
                        if -DEADZONE < x < DEADZONE and -DEADZONE < y < DEADZONE:
                            # stopped
                            cur_x = 0
                            cur_y = 0
                        elif -DEADZONE < y < DEADZONE:
                            # turning
                            if x < 0:
                                cur_x = 0
                                cur_y = int(y * 250)
                            else:
                                cur_x = int(x * 250)
                                cur_y = 0
                        elif -DEADZONE < x < DEADZONE:
                            # straight
                            cur_x = int(y * 250)
                            cur_y = int(y * 250)
                        else:
                            # diagonal
                            if x < DEADZONE and y < DEADZONE:
                                cur_y = - int((abs(x) + abs(y)) * 250)
                                if cur_y < -250:
                                    cur_y = -250
                                cur_x = int((x - y) * cur_y)
                                cur_x = - ((cur_x + cur_y) / 2)
                            elif x < DEADZONE < y:
                                cur_y = int((abs(x) + abs(y)) * 250)
                                if cur_y > 250:
                                    cur_y = 250
                                cur_x = int((x + y) * cur_y)
                                cur_x = ((cur_x + cur_y) / 2)
                            elif x > DEADZONE > y:
                                cur_x = - int((abs(x) + abs(y)) * 250)
                                if cur_x < -250:
                                    cur_x = -250
                                cur_y = int((x + y) * 250)
                                cur_y = ((cur_y - 250) / 2)
                            elif x > DEADZONE and y > DEADZONE:
                                cur_x = int((abs(x) + abs(y)) * 250)
                                if cur_x > 250:
                                    cur_x = 250
                                cur_y = int((y - x) * cur_x)
                                cur_y = ((cur_y + cur_x) / 2)

                        self.send_control_message("!MANUAL," + str(cur_x) + "," + str(cur_y) + ",")

                # handle button release
                elif event.type == pygame.JOYBUTTONUP:
                    self.send_control_message("!STOP")
        except:
            print(traceback.format_exc())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())
