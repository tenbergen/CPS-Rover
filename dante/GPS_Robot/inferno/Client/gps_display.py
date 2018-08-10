from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QGroupBox, QGridLayout, QHBoxLayout, QVBoxLayout, \
    QRadioButton, \
    QFileDialog, QLabel
from PyQt5.QtCore import Qt, QRect, pyqtSlot
from PyQt5.QtGui import QPixmap
from grid import *
from queue import Queue
from client import *
import sys
import traceback
import time
from vector import Vector

# TODO client should have send messages for different types of data.
# TODO add rover status on GUI
# TODO add controller control scheme to the GUI
# TODO add legend to grid.
# TODO change the way grids save/load.  Add protocol to send over socket.
# TODO change grid_panel to function using mouse location and painting squares

# Mouse states
MOUSE_MODE = 1
ADD_OBSTACLE = 1
REMOVE_OBSTACLE = 2
ADD_DESTINATION = 3
ADD_HOME = 4

# Simulation States
SIM_MODE = 1
WAIT = 1
GO_BACK = 2
CONTINUE = 3
GO_HOME = 4

# Map Colors
OPEN_SPACE = Qt.gray
BORDER_SPACE = Qt.darkGray
OBSTACLE = Qt.black
DESTINATION = Qt.green
PATH = Qt.blue
ROVER_AUTO = Qt.cyan
ROVER_MAN = Qt.magenta
ROVER_SIM = Qt.red
HOME = Qt.yellow
SIMPLE_PATH = Qt.darkBlue
FUTURE_DESTINATION = Qt.darkGreen

# Modes
AUTO = 0
SIM = 1
MANUAL = 2


def sim_state(button):
    global SIM_MODE
    if button.text() == "Wait":
        SIM_MODE = WAIT
    elif button.text() == "Go To Previous Points":
        SIM_MODE = GO_BACK
    elif button.text() == "Continue With Waypoints":
        SIM_MODE = CONTINUE
    elif button.text() == "Go Home":
        SIM_MODE = GO_HOME


# This helps switch mouse modes for the GUI
def btnstate(button):
    global MOUSE_MODE
    if button.text() == "Add Obstacle":
        MOUSE_MODE = ADD_OBSTACLE
    elif button.text() == "Remove Obstacle":
        MOUSE_MODE = REMOVE_OBSTACLE
    elif button.text() == "Add Destination":
        MOUSE_MODE = ADD_DESTINATION
    elif button.text() == "Create/Move Home":
        MOUSE_MODE = ADD_HOME


# This class creates and maintains a GUI that sends instructions to the rover.

class App(QMainWindow):

    # create the default instance
    # noinspection PyArgumentList
    def __init__(self):
        super().__init__()

        # GUI default values
        self.title = "GPS Robot-Inferno"
        self.left = 10
        self.top = 100
        self.width = 1300
        self.height = 800

        # create the grid
        self.grid_width = 2.5
        self.grid_height = 3.5
        self.grid_x = 20
        self.grid_y = 28
        self.offset_x = 0
        self.offset_y = 0
        self.border_thickness = 1
        self.use_diagonals = True
        self.grid = Grid(self.grid_width, self.grid_height, self.grid_x, self.grid_y, self.offset_x, self.offset_y,
                         self.border_thickness, self.use_diagonals)

        # create the important point variables
        self.rover_position = self.grid.get_node(0, 0)
        self.rover_actual_position = Vector()
        self.destinations = []
        self.home = self.grid.get_node(1, 1)
        self.current_path = []
        self.simple_path = []
        self.in_motion = False
        self.mode = AUTO
        self.rover_status = 0

        # setup client and signals
        self.send_queue = Queue()
        self.client = Client(self.send_queue)
        self.client.on_rover_position_changed.connect(self.rover_pos_changed)
        self.client.on_rover_actual_position_changed.connect(self.on_actual_position_updated)
        self.client.on_destination_reached.connect(self.on_point_reached)
        self.client.on_destination_update.connect(self.on_destinations_updated)
        self.client.on_rover_status_changed.connect(self.on_rover_status_update)
        self.client.on_node_changed.connect(self.on_node_changed)
        self.client.on_simple_path_changed.connect(self.on_simple_path_changed)
        self.client.on_path_changed.connect(self.on_path_changed)
        self.client.on_camera_button_pressed.connect(self.on_cam_on_off_clicked)
        self.client.on_go_home_pressed.connect(self.on_go_home_clicked)
        self.client.on_auto_switch.connect(self.on_autodrive_clicked)

        self.remote_on = False

        # create the actual GUI
        self.init_ui()

        # start the video stream
        self.stream = VideoStream()
        self.stream.changePixmap.connect(self.set_image)

    # actually builds the GUI
    # noinspection PyArgumentList
    def init_ui(self):

        # base effects
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.set_color(Qt.white)

        # layouts
        self.grid_panel = GridPanel(self, self.grid)
        self.button_panel = QVBoxLayout()
        self.mouse_layout = QGroupBox(self)
        self.simulate_panel = QGroupBox(self)

        # set up for simulation modes
        self.simulate_panel.setTitle("Simulation Mode")
        self.simulate_panel.setFixedSize(200, 125)
        self.simulate_panel.move(990, 15)

        # layout for simulation
        grid_s = QGridLayout(self.simulate_panel)

        # wait
        self.sim_wait_button = QRadioButton(self)
        self.sim_wait_button.setText("Wait")
        self.sim_wait_button.setChecked(True)
        self.sim_wait_button.toggled.connect(lambda: sim_state(self.sim_wait_button))

        # Go back
        self.sim_back_button = QRadioButton(self)
        self.sim_back_button.setText("Wait")
        self.sim_back_button.toggled.connect(lambda: sim_state(self.sim_back_button))

        # Continue
        self.sim_cont_button = QRadioButton(self)
        self.sim_cont_button.setText("Continue")
        self.sim_cont_button.toggled.connect(lambda: sim_state(self.sim_cont_button))

        # Continue
        self.sim_home_button = QRadioButton(self)
        self.sim_home_button.setText("Home")
        self.sim_home_button.toggled.connect(lambda: sim_state(self.sim_home_button))

        # simulate network disconnect button
        self.sim_button = QPushButton(self)
        self.sim_button.setText("Start Simulation")
        self.sim_button.clicked.connect(self.on_sim_start)

        # add simulation buttons to layout
        grid_s.setSpacing(10)
        grid_s.addWidget(self.sim_wait_button, 0, 0)
        grid_s.addWidget(self.sim_back_button, 0, 1)
        grid_s.addWidget(self.sim_cont_button, 1, 0)
        grid_s.addWidget(self.sim_home_button, 1, 1)
        grid_s.addWidget(self.sim_button, 2, 0)
        self.simulate_panel.setEnabled(False)

        # set up for mouse actions
        self.mouse_layout.setTitle("On Click")
        self.mouse_layout.resize(350, 100)
        self.mouse_layout.setFixedSize(350, 100)

        # layout for mouse actions
        gridl = QGridLayout(self.mouse_layout)

        # add obstacle
        self.add_obstacle_button = QRadioButton(self)
        self.add_obstacle_button.setText("Add Obstacle")
        self.add_obstacle_button.setChecked(True)
        self.add_obstacle_button.toggled.connect(lambda: btnstate(self.add_obstacle_button))

        # remove obstacle
        self.remove_obstacle_button = QRadioButton(self)
        self.remove_obstacle_button.setText("Remove Obstacle")
        self.remove_obstacle_button.toggled.connect(lambda: btnstate(self.remove_obstacle_button))

        # add destination
        self.add_destination_button = QRadioButton(self)
        self.add_destination_button.setText("Add Destination")
        self.add_destination_button.toggled.connect(lambda: btnstate(self.add_destination_button))

        # remove destination
        self.add_home_button = QRadioButton(self)
        self.add_home_button.setText("Create/Move Home")
        self.add_home_button.toggled.connect(lambda: btnstate(self.add_home_button))

        # configure mouse action layout
        gridl.setSpacing(10)
        gridl.addWidget(self.add_obstacle_button, 0, 0)
        gridl.addWidget(self.remove_obstacle_button, 0, 1)
        gridl.addWidget(self.add_destination_button, 1, 0)
        gridl.addWidget(self.add_home_button, 1, 1)
        self.mouse_layout.setLayout(gridl)
        self.mouse_layout.setEnabled(False)
        self.button_panel.addWidget(self.mouse_layout)

        # clear destination button
        self.clear_destination_button = QPushButton(self)
        self.clear_destination_button.setText("Clear Destinations")
        self.clear_destination_button.clicked.connect(self.on_clear_destination_clicked)
        self.button_panel.addWidget(self.clear_destination_button)
        self.clear_destination_button.setEnabled(False)

        # clear obstacles
        self.clear_obstacles_button = QPushButton(self)
        self.clear_obstacles_button.setText("Clear All Obstacles")
        self.clear_obstacles_button.clicked.connect(self.on_clear_obstacles)
        self.button_panel.addWidget(self.clear_obstacles_button)
        self.clear_obstacles_button.setEnabled(False)

        # save and load buttons
        # self.save_button = QPushButton(self)
        # self.load_button = QPushButton(self)
        # self.save_button.setText("Save")
        # self.save_button.clicked.connect(self.save)
        # self.load_button.setText("Load")
        # self.load_button.clicked.connect(self.load)
        # self.save_load_layout = QHBoxLayout()
        # self.save_load_layout.addWidget(self.save_button)
        # self.save_load_layout.addWidget(self.load_button)
        # self.button_panel.addLayout(self.save_load_layout)

        # connect button
        self.connect_button = QPushButton(self)
        self.connect_button.setText("Connect")
        self.connect_button.clicked.connect(self.on_connect)
        self.button_panel.addWidget(self.connect_button)

        # turn cam on/off button
        self.cam_on_button = QPushButton(self)
        self.cam_on_button.setText("Turn Video Off")
        self.cam_on_button.clicked.connect(self.on_cam_on_off_clicked)
        self.button_panel.addWidget(self.cam_on_button)
        self.cam_on_button.setEnabled(False)

        # autodrive Button
        self.autodrive_button = QPushButton(self)
        self.autodrive_button.setText("Switch To Manual")
        self.autodrive_button.clicked.connect(self.on_autodrive_clicked)
        self.button_panel.addWidget(self.autodrive_button)
        self.autodrive_button.setEnabled(False)

        # go home Button
        self.go_home_button = QPushButton(self)
        self.go_home_button.setText("Go Home")
        self.go_home_button.clicked.connect(self.on_go_home_clicked)
        self.button_panel.addWidget(self.go_home_button)
        self.go_home_button.setEnabled(False)

        # Start/Stop Button
        self.start_stop_button = QPushButton(self)
        self.start_stop_button.setText("Start")
        self.start_stop_button.clicked.connect(self.on_start_stop_clicked)
        self.button_panel.addWidget(self.start_stop_button)
        self.start_stop_button.setEnabled(False)

        # create camera stream
        self.video_layout = QGroupBox(self)
        self.video_layout.setTitle("Video Stream")
        temp = QGridLayout(self.video_layout)
        self.video = QLabel(self)
        temp.addWidget(self.video)
        temp.setSpacing(0)
        self.video_layout.setLayout(temp)
        self.video_layout.setFixedSize(440, 320)
        self.video.resize(480, 320)
        self.button_panel.addWidget(self.video_layout)
        self.video_layout.setAlignment(Qt.AlignVCenter)

        # move panel to position!
        self.button_panel.setGeometry(QRect(525, 5, 440, 700))

    def on_connect(self):
        try:
            self.client.connect_to_server()
            self.stream.connect_to_server()
        except Exception as e:
            print(e)
        finally:
            self.client.start()
            self.stream.start()
            self.mouse_layout.setEnabled(True)
            self.clear_destination_button.setEnabled(True)
            self.clear_obstacles_button.setEnabled(True)
            self.cam_on_button.setEnabled(True)
            self.autodrive_button.setEnabled(True)
            self.start_stop_button.setEnabled(True)
            self.go_home_button.setEnabled(True)
            self.simulate_panel.setEnabled(True)

    # when the window closes
    def closeEvent(self, event):
        print("program closing")

        # close the client
        self.send_queue.put("Q")
        self.client.can_run = False
        self.stream.can_run = False
        time.sleep(1)
        self.client.quit()
        self.client.quit()

    # allows us to change the window color
    def set_color(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

    # get the mouse mode
    def get_mouse_mode(self):
        return self.MOUSE_MODE

    def on_sim_start(self):
        if self.sim_button.text() == "Start Simulation":
            self.send_queue.put("SIM " + str(SIM_MODE))
            self.send_queue.put("MODE 1")
            self.sim_button.setText("Stop Simulation")
            self.start_stop_button.hide()
            self.autodrive_button.hide()
            self.video.hide()
            self.mode = SIM
        else:
            self.send_queue.put("MODE 0")
            self.sim_button.setText("Start Simulation")
            self.autodrive_button.show()
            self.video.show()
            if not self.client.remote_on:
                self.start_stop_button.show()
                self.mode = AUTO
            else:
                self.mode = MANUAL

    # when all the obstacles need to be cleared
    def on_clear_obstacles(self):
        temp = list(self.grid.all_obstacles)
        while len(temp) > 0:
            self.on_obstacle_removed(temp.pop(0))
        self.grid_panel.redraw_grid()

    # noinspection PyArgumentList
    @pyqtSlot(QImage)
    def set_image(self, image):
        self.video.setPixmap(QPixmap.fromImage(image))

    # updates the simple path
    # noinspection PyArgumentList
    @pyqtSlot(list)
    def on_simple_path_changed(self, path):
        temp = []
        for p in path:
            temp.append(self.grid.get_node(p.x, p.y))
        self.simple_path = temp
        self.grid_panel.redraw_grid()

    # updates the path
    # noinspection PyArgumentList
    @pyqtSlot(list)
    def on_path_changed(self, path):
        temp = []
        for p in path:
            temp.append(self.grid.get_node(p.x, p.y))
        self.current_path = temp
        self.grid_panel.redraw_grid()

    # when a node changes
    # noinspection PyArgumentList
    @pyqtSlot(Vector, int)
    def on_node_changed(self, node, node_type):
        self.grid.set_node(node.x, node.y, node_type)
        print(node.x, node.y, node_type)
        self.grid_panel.redraw_grid()
        if node_type == 1:
            self.validate_destinations(self.grid.get_node(node.x, node.y))

    # when the destinations have changed server side
    # noinspection PyArgumentList
    @pyqtSlot(list)
    def on_destinations_updated(self, positions):
        self.destinations = positions
        self.grid_panel.redraw_grid()

    # noinspection PyArgumentList
    @pyqtSlot(Vector)
    def on_actual_position_updated(self, position):
        self.rover_actual_position = position
        # TODO add label that displays this information.

    def on_rover_status_update(self, status):
        self.rover_status = status

    # factory for button click events.
    def on_click_event(self, vector):
        grid = self.grid

        # creates a click event for each button on the grid.
        def click_event():
            x = vector.x
            y = vector.y
            node = grid.nodes[x][y]
            something_happened = False
            print("My name is " + node.gridPos.x.__str__() + " " + node.gridPos.y.__str__())
            print("My node Type is: " + node.node_type.__str__())
            print(int(MOUSE_MODE).__str__())

            # use the proper mouse event based on the obstacle
            if MOUSE_MODE == ADD_OBSTACLE:
                something_happened = self.on_obstacle_added(node)
            elif MOUSE_MODE == REMOVE_OBSTACLE:
                something_happened = self.on_obstacle_removed(node)
            elif MOUSE_MODE == ADD_DESTINATION:
                something_happened = self.on_destination_added(node)
            elif MOUSE_MODE == ADD_HOME:
                something_happened = self.on_home_added(node)

            # if there was a change in the grid, redraw it.
            if something_happened:
                self.grid_panel.redraw_grid()

        return click_event

    # if an obstacle is added to the grid we need to ensure pathfinding and drawing aren't distrupted.
    def on_obstacle_added(self, node):

        # if we have a valid node to work with.
        if node.node_type != 1 and node != self.rover_position:

            # we need to spread the grid.
            self.grid.set_node_type(node, 1)
            self.validate_destinations(node)
            return True
        return False

    def validate_destinations(self, node):
        border = self.grid.all_borders
        # IF there is a destination in play and it is hit by the border, it needs to be cleared.
        if len(self.destinations) > 0:
            if border.__contains__(self.destinations[0]) or node == self.destinations[0]:
                self.destinations.pop(0)

                if len(self.destinations) > 0:
                    self.send_queue.put(
                        "D " + str(self.destinations[0].gridPos.x) + " " + str(self.destinations[0].gridPos.y))
                else:
                    self.current_path = []
                    self.simple_path = []
                    self.send_queue.put("D -1 -1")

                self.send_queue.put("N " + str(node.gridPos.x) + " " + str(node.gridPos.y) + " " + str(1))

    # if an obstacle was removed from the map we need to recalculate our path and borders.
    def on_obstacle_removed(self, node):
        if node.node_type == 1:
            self.grid.set_node_type(node, 0)
            self.send_queue.put("N " + str(node.gridPos.x) + " " + str(node.gridPos.y) + " " + str(0))
            return True
        return False

    # if a destination was placed somewhere on the map
    def on_destination_added(self, node):
        print("adding destination")
        if node.node_type == 0 and node != self.rover_position and not self.destinations.__contains__(node):
            self.destinations.append(node)
            if len(self.destinations) == 1:
                self.send_queue.put("D " + str(node.gridPos.x) + " " + str(node.gridPos.y))
            return True
        return False

    # if a "home" was placed on the map.
    def on_home_added(self, node):
        if self.home != node:
            self.home = node
            self.send_queue.put("H " + str(node.gridPos.x) + " " + str(node.gridPos.y))
            return True
        return False

    # If the start/stop button was pressed.
    def on_start_stop_clicked(self):
        self.toggle_in_motion()

    # switches the in_motion variable from true to false and vice versa.
    # It also changes the text of the start/stop button

    def toggle_in_motion(self):
        self.in_motion = not self.in_motion
        if self.in_motion:
            self.start_stop_button.setText("Stop")
            if len(self.simple_path) > 0:
                self.send_queue.put("GO")
        else:
            self.start_stop_button.setText("Start")
            self.send_queue.put("S")

    # noinspection PyArgumentList
    @pyqtSlot()
    def on_cam_on_off_clicked(self):
        button = self.cam_on_button
        if button.text() == "Turn Video On":
            button.setText("Turn Video Off")
            self.video.show()
        else:
            button.setText("Turn Video On")
            self.video.hide()

    # When the user wants to remove the destination
    def on_clear_destination_clicked(self):
        print("clearing destinations")
        if len(self.destinations) > 0:
            for d in self.destinations:
                self.remove_destination(d)
            self.destinations = []
            self.current_path = []
            self.simple_path = []
            self.send_queue.put("D -1 -1")
            self.grid_panel.redraw_grid()
            if self.in_motion:
                self.toggle_in_motion()

    def remove_destination(self, node):
        count = 0
        while self.grid_panel.buttons[count].node != node:
            count += 1
        self.grid_panel.buttons[count].setText("")

    # when auto/manual is toggled.
    # noinspection PyArgumentList
    @pyqtSlot()
    def on_autodrive_clicked(self):

        button = self.autodrive_button
        if button.text() == "Switch To Manual":
            button.setText("Switch To Automatic")
            self.client.remote_on = True
            self.start_stop_button.hide()
            self.send_queue.put("MODE 2")
            self.mode = MANUAL
        else:
            button.setText("Switch To Manual")
            if self.in_motion:
                self.on_start_stop_clicked()
            self.client.remote_on = False
            self.send_queue.put("S")
            self.start_stop_button.show()
            self.send_queue.put("MODE 0")
            self.mode = AUTO

    # When the user tells the robot to go home.  drop everything and go home.
    # noinspection PyArgumentList
    @pyqtSlot()
    def on_go_home_clicked(self):
        if self.home is not None and self.rover_position != self.home:
            # set the current destination
            self.on_clear_destination_clicked()
            self.destinations.append(self.home)
            node = self.home
            self.send_queue.put("D " + str(node.gridPos.x) + " " + str(node.gridPos.y))
            self.send_queue.put("GO")
            # if we aren't in automatic and going, we need to be.
            auto_button = self.autodrive_button
            if auto_button.text() == "Switch To Automatic":
                self.on_autodrive_clicked()
            if not self.in_motion:
                self.on_start_stop_clicked()
            self.grid_panel.redraw_grid()

    # this is a callback to signify that we have made it to a destination.
    # noinspection PyArgumentList
    @pyqtSlot()
    def on_point_reached(self):
        print(self.destinations)
        print("point reached - received from server")
        # if we are at our final destination, we are done.
        if len(self.destinations) > 0 and self.rover_position == self.destinations[0]:
            if len(self.destinations) > 0:
                self.destinations.pop(0)

            if len(self.destinations) > 0:
                print("Destination reached, going to next destination")
                self.send_queue.put(
                    "D " + str(self.destinations[0].gridPos.x) + " " + str(self.destinations[0].gridPos.y))
                self.send_queue.put("GO")
            else:
                print("final destination reached")
                self.send_queue.put("S")
                if self.in_motion:
                    self.toggle_in_motion()

    # a callback for when the rover's new position is sent.
    # noinspection PyArgumentList
    @pyqtSlot(Vector)
    def rover_pos_changed(self, position):
        node = self.grid.get_node(position.x, position.y)

        # we still only care if it moves it to a new node.
        if node != self.rover_position:
            print("rover position changed - Received from server")
            self.rover_position = node

        self.grid_panel.redraw_grid()

    # opens a save dialog for the grid.
    def save(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Grid", "", "All Files (*);;Text Files (*.txt)",
                                                   options=options)
        if file_name:
            print(file_name)

        self.grid.save(file_name)

    # opens a load dialog.
    def load(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Grid", "", "All Files (*);;Python Files (*.py)",
                                                   options=options)
        self.grid = Grid.load(file_name)
        self.grid_panel.setParent(None)
        self.grid_panel = None
        self.grid_panel = GridPanel(self, self.grid)
        self.grid_panel.show()


# this handles the visual appearance of the grid.
class GridPanel(QGroupBox):

    # initialize class
    def __init__(self, parent, grid):
        super().__init__(parent)

        # default settings
        self.current_color = None
        self.setTitle("Physical Context Map")
        self.grid = grid
        self.buttons = []
        self.par = parent

        # prep the layout to have no empty space
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)

        # bind every button to a node.
        for i in range(0, self.grid.nodes_in_x):
            for j in range(0, self.grid.nodes_in_y):
                temp = GridButton(self, self.grid.get_node(i, j))
                temp.x = j
                temp.y = self.grid.nodes_in_y - i
                temp.clicked.connect(parent.on_click_event(Vector(i, j)))
                # noinspection PyArgumentList
                layout.addWidget(temp, self.grid.nodes_in_y - j, i)
                self.buttons.append(temp)

        # set the grid up.
        self.setLayout(layout)
        self.move(10, 15)
        self.setFixedSize(500, 650)
        self.setAutoFillBackground(True)
        self.set_color(Qt.white)

        # redraw
        self.redraw_grid()

    # this lets us change the color of the panel
    def set_color(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)
        self.current_color = color

    # this allows us to redraw each button.
    def redraw_grid(self):

        # for every button, determine what its node is, then set its color
        # the ordering of the if statements determine the the "z-layer" from highest to lowest.
        for b in self.buttons:
            b.determine_type()
            if b.node == self.par.rover_position:
                if self.par.mode == AUTO:
                    b.set_color(ROVER_AUTO)
                elif self.par.mode == MANUAL:
                    b.set_color(ROVER_MAN)
                elif self.par.mode == SIM:
                    b.set_color(ROVER_SIM)

            elif b.node == self.par.home:
                b.set_color(HOME)

            elif len(self.par.destinations) > 0 and b.node == self.par.destinations[0]:
                b.set_color(DESTINATION)
                b.setText("")

            elif len(self.par.destinations) > 1 and self.par.destinations.__contains__(b.node):
                b.set_color(FUTURE_DESTINATION)
                b.setText(str(self.par.destinations.index(b.node)))

            elif self.par.simple_path.__contains__(b.node) and not self.par.remote_on:
                b.set_color(SIMPLE_PATH)

            elif self.par.current_path.__contains__(b.node):
                b.set_color(PATH)


# This is a button on a grid.  it has some expanded features involving nodes.
class GridButton(QPushButton):

    # init button
    def __init__(self, parent, node):
        super().__init__(parent)

        # set default values.
        self.node = node
        self.default_color = OPEN_SPACE
        self.current_color = self.default_color
        self.setFlat(True)
        self.setAutoFillBackground(True)
        self.set_color(self.default_color)
        self.resize(10, 10)

    # determine if we are an open space, border or obstacle.
    def determine_type(self):
        if self.node.node_type == 0:
            self.default_color = OPEN_SPACE
        elif self.node.node_type == 1:
            self.default_color = OBSTACLE
        elif self.node.node_type == 2:
            self.default_color = BORDER_SPACE
        self.current_color = self.default_color
        self.set_color(self.current_color)

    # this allows us to change the color
    def set_color(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)
        self.current_color = color


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        ex = App()
        ex.show()
        sys.exit(app.exec_())
    except Exception as ex:
        traceback.print_exc()
