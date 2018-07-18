from PyQt5.QtWidgets import QApplication,QMainWindow,QPushButton,QGroupBox,QGridLayout,QHBoxLayout,QVBoxLayout,QRadioButton, \
    QFileDialog
from PyQt5.QtCore import Qt,QRect,pyqtSlot
from grid import *
from vector import *
from queue import Queue
from client import Client
import sys
import traceback

#Mouse states
MOUSE_MODE = 1
ADD_OBSTACLE = 1
REMOVE_OBSTACLE = 2
ADD_DESTINATION = 3
ADD_HOME = 4

#Map Colors
OPEN_SPACE = Qt.gray
BORDER_SPACE = Qt.darkGray
OBSTACLE = Qt.black
DESTINATION = Qt.green
PATH = Qt.blue
ROVER = Qt.red
HOME = Qt.yellow
SIMPLE_PATH = Qt.darkBlue

#This helps switch mouse modes for the GUI
def btnstate(button):
    global MOUSE_MODE
    if button.text() == "Add Obstacle":
        MOUSE_MODE = ADD_OBSTACLE
    elif button.text() == "Remove Obstacle":
        MOUSE_MODE = REMOVE_OBSTACLE
    elif button.text() == "Create/Move Destination":
        MOUSE_MODE = ADD_DESTINATION
    elif button.text() == "Create/Move Home":
        MOUSE_MODE = ADD_HOME

#This class creates and maintains a GUI that sends instructions to the rover.
class App(QMainWindow):

    #create the default instance
    def __init__(self):
        super().__init__()
        
        #GUI default values
        self.title = "GPS Robot-Inferno"
        self.left = 10
        self.top = 100
        self.width = 1000
        self.height = 800

        #create the grid
        self.grid_width = 2.5
        self.grid_height = 3.5
        self.grid_x = 20
        self.grid_y = 28
        self.offset_x = 0
        self.offset_y = 0
        self.border_thickness = 2
        self.use_diagonals = True
        self.grid = Grid(self.grid_width,self.grid_height ,self.grid_x,self.grid_y,self.offset_x,self.offset_y,self.border_thickness,self.use_diagonals)

        #create the important point variables
        self.rover_position = self.grid.get_node(0,0)
        self.current_destination = None
        self.home = self.grid.get_node(1,1)
        self.current_path = []
        self.simple_path = []
        self.in_motion = False

        #setup client and signals
        self.send_queue = Queue()
        self.client = Client(self.send_queue)
        self.client.on_rover_position_changed.connect(self.rover_pos_changed)
        self.client.on_destination_reached.connect(self.on_point_reached)
        self.client.on_node_changed.connect(self.on_node_changed)
        self.client.on_simple_path_changed.connect(self.on_simple_path_changed)
        self.client.on_path_changed.connect(self.on_path_changed)
        self.remote_on = False      #TODO use this for when remote control is re-implemented.



        #create the actual GUI
        self.initUI()


    #actually builds the GUI
    def initUI(self):
        #TODO add button that appears only when there currently isn't a connection
        #base effects
        self.setWindowTitle(self.title)
        self.setGeometry(self.left,self.top,self.width,self.height)
        self.set_color(Qt.white)

        #layouts
        self.grid_panel = GridPanel(self,self.grid)
        self.button_panel = QVBoxLayout()
        self.mouse_layout = QGroupBox(self)

        #set up for mouse actions
        self.mouse_layout.setTitle("On Click")
        self.mouse_layout.resize(350,100)
        self.mouse_layout.move(600,50)

        #layout for mouse actions
        gridl = QGridLayout(self.mouse_layout)

        #add obstscle
        self.add_obstacle_button = QRadioButton(self)
        self.add_obstacle_button.setText("Add Obstacle")
        self.add_obstacle_button.setChecked(True)
        self.add_obstacle_button.toggled.connect(lambda:btnstate(self.add_obstacle_button))

        #remove obstacle
        self.remove_obstacle_button = QRadioButton(self)
        self.remove_obstacle_button.setText("Remove Obstacle")
        self.remove_obstacle_button.toggled.connect(lambda:btnstate(self.remove_obstacle_button))

        #add destination
        self.add_destination_button = QRadioButton(self)
        self.add_destination_button.setText("Create/Move Destination")
        self.add_destination_button.toggled.connect(lambda:btnstate(self.add_destination_button))

        #remove destination
        self.add_home_button = QRadioButton(self)
        self.add_home_button.setText("Create/Move Home")
        self.add_home_button.toggled.connect(lambda:btnstate(self.add_home_button))

        #configure mouse action layout
        gridl.setSpacing(10)
        gridl.addWidget(self.add_obstacle_button,0,0)
        gridl.addWidget(self.remove_obstacle_button,0,1)
        gridl.addWidget(self.add_destination_button,1,0)
        gridl.addWidget(self.add_home_button,1,1)
        self.mouse_layout.setLayout(gridl)

        #clear buttons
        self.clear_destination_button = QPushButton(self)
        self.clear_destination_button.setText("Clear Destination")
        self.clear_destination_button.clicked.connect(self.on_clear_destination_clicked)
        self.button_panel.addWidget(self.clear_destination_button)
        
        # save and load buttons
        self.save_button = QPushButton(self)
        self.load_button = QPushButton(self)
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.save)
        self.load_button.setText("Load")
        self.load_button.clicked.connect(self.load)
        self.save_load_layout = QHBoxLayout()
        self.save_load_layout.addWidget(self.save_button)
        self.save_load_layout.addWidget(self.load_button)
        self.button_panel.addLayout(self.save_load_layout)

        #connect button
        self.connect_button = QPushButton(self)
        self.connect_button.setText("Connect")
        self.connect_button.clicked.connect(self.client.connect_to_server)
        self.button_panel.addWidget(self.connect_button)
        
        #turn cam on/off button
        self.cam_on_button = QPushButton(self)
        self.cam_on_button.setText("Turn Video On")
        self.cam_on_button.clicked.connect(self.on_cam_on_off_clicked)
        self.button_panel.addWidget(self.cam_on_button)

        #autodrive Button
        self.autodrive_button = QPushButton(self)
        self.autodrive_button.setText("Switch To Manual")
        self.autodrive_button.clicked.connect(self.on_autodrive_clicked)
        self.button_panel.addWidget(self.autodrive_button)

        #go home Button
        self.go_home_button = QPushButton(self)
        self.go_home_button.setText("Go Home")
        self.go_home_button.clicked.connect(self.on_go_home_clicked)
        self.button_panel.addWidget(self.go_home_button)

        #Start/Stop Button
        self.start_stop_button = QPushButton(self)
        self.start_stop_button.setText("Start")
        self.start_stop_button.clicked.connect(self.on_start_stop_clicked)
        self.button_panel.addWidget(self.start_stop_button)
        
        #move panel to position!
        self.button_panel.setGeometry(QRect(600, 150, 300, 200))
        
    #when the window closes
    def closeEvent(self,event):
        print("program closing")

        #close the client
        self.client.can_run = False
        self.client.quit()

    #allows us to change the window color
    def set_color(self,color):
        p = self.palette()
        p.setColor(self.backgroundRole(),color)
        self.setPalette(p)

    #get the mouse mode      
    def get_mouse_mode(self):
        return self.MOUSE_MODE

    #updates the simple path
    @pyqtSlot(list)
    def on_simple_path_changed(self,path):
        temp = []
        for p in path:
            temp.append(self.grid.get_node(p.x,p.y))
        self.simple_path = temp
        self.grid_panel.redraw_grid()

    #updates the path
    @pyqtSlot(list)
    def on_path_changed(self, path):
        temp = []
        for p in path:
            temp.append(self.grid.get_node(p.x,p.y))
        self.current_path = temp
        self.grid_panel.redraw_grid()

    #when a node changes
    @pyqtSlot(Vector,int)
    def on_node_changed(self,node,node_type):
        try:
            self.grid.set_node(node.x,node.y,node_type)
            self.grid_panel.redraw_grid()
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

    #factory for button click events.
    def on_click_event(self,vector):
        grid = self.grid

        #creates a click event for each button on the grid.
        def click_event():
            try:
                x = vector.x
                y = vector.y
                node = grid.nodes[x][y]
                something_happened = False
                print("My name is "+node.gridPos.x.__str__() +" "+ node.gridPos.y.__str__())
                print("My node Type is: "+node.node_type.__str__())
                print(int(MOUSE_MODE).__str__())

                #use the proper mouse event based on the obstacle
                if MOUSE_MODE == ADD_OBSTACLE:
                    something_happened = self.on_obstacle_added(node)
                elif MOUSE_MODE == REMOVE_OBSTACLE:
                    something_happened = self.on_obstacle_removed(node)
                elif MOUSE_MODE == ADD_DESTINATION:
                    something_happened = self.on_destination_added(node)
                elif MOUSE_MODE == ADD_HOME:
                    something_happened = self.on_home_added(node)
                    
                #if there was a change in the grid, redraw it.
                if something_happened:
                    self.grid_panel.redraw_grid()
            except Exception as ex:
                print(ex)

        return click_event


    #if an obstacle is added to the grid we need to ensure pathfinding and drawing aren't distrupted.
    def on_obstacle_added(self,node):

        #if we have a valid node to work with.
        if node.node_type != 1 and node != self.rover_position:

            #we need to spread the grid.
            self.grid.set_node_type(node,1)
            border = self.grid.all_borders

            #IF there is a destination in play and it is hit by the border, it needs to be cleared.
            if self.current_destination is not None:
                if border.__contains__(self.current_destination):
                    self.current_destination = None
                    self.current_path = []
                    self.simple_path = []
                    self.send_queue.put("D -1 -1")

            self.send_queue.put("N " + str(node.gridPos.x) + " " + str(node.gridPos.y) + " " + str(1))
            return True
        return False
    
    #if an obstacle was removed from the map we need to recalculate our path and borders.
    def on_obstacle_removed(self,node):
        if node.node_type ==1:
            self.grid.set_node_type(node,0)
            self.send_queue.put("N " + str(node.gridPos.x) + " " + str(node.gridPos.y) + " " + str(0))
            return True
        return False

    #if a destination was placed somewhere on the map    
    def on_destination_added(self,node):
        if node.node_type == 0 and node != self.rover_position:
            self.current_destination = node
            self.send_queue.put("D " + str(node.gridPos.x) + " " + str(node.gridPos.y))
            return True
        return False

    #if a "home" was placed on the map.    
    def on_home_added(self,node):
        if self.home != node:
            self.home = node
            return True
        return False

    #If the start/stop button was pressed.
    def on_start_stop_clicked(self):
        self.toggle_in_motion()



    #switches the in_motion variable from true to false and vice versa.  It also changes the text of the start/stop button
    def toggle_in_motion(self):
        self.in_motion = not self.in_motion
        if self.in_motion:
            self.start_stop_button.setText("Stop")
            if len(self.simple_path)>0:
                self.send_queue.put("GO")
        else:
            self.start_stop_button.setText("Start")
            self.send_queue.put("S")

    #TODO implement camera        
    def on_cam_on_off_clicked(self):
        button = self.cam_on_button
        if button.text() == "Turn Video On":
            button.setText("Turn Video Off")
        else:
            button.setText("Turn Video On")

    #When the user wants to remove the destination        
    def on_clear_destination_clicked(self):
        if self.current_destination is not None:
            self.current_destination=None
            self.current_path=[]
            self.simple_path = []
            self.send_queue.put("D -1 -1")
            self.grid_panel.redraw_grid()
            if self.in_motion:
                self.toggle_in_motion()

    #when auto/manual is toggled.        
    def on_autodrive_clicked(self):

        #TODO consider using a boolean for auto drive.
        button = self.autodrive_button
        if button.text() == "Switch To Manual":
            button.setText("Switch To Automatic")
            self.client.remote_on = True
            self.start_stop_button.hide()
        else:
            button.setText("Switch To Manual")
            if self.in_motion:
                self.on_start_stop_clicked()
                self.client.remote_on = False
            self.start_stop_button.show()

    #When the user tells the robot to go home.  drop everything and go home.        
    def on_go_home_clicked(self):
        if self.home is not None:
            #set the current destination
            self.current_destination = self.home
            node = self.home
            self.send_queue.put("D " + str(node.gridPos.x) + " " + str(node.gridPos.y))
            #if we aren't in automatic and going, we need to be.
            auto_button = self.autodrive_button
            if auto_button.text() == "Switch To Automatic":
                self.on_autodrive_clicked()
            if not self.in_motion:
                self.on_start_stop_clicked()
            self.grid_panel.redraw_grid()

    #this is a callback to signify that we have made it to a destination.
    @pyqtSlot()
    def on_point_reached(self):
        print("point reached - received from server")

        #if we are at our final destination, we are done.
        if len(self.current_path) == 0 or len(self.simple_path) == 0 or (self.current_destination is not None and self.current_destination == self.rover_position):
            print("final destination reached")
            if self.in_motion:
                self.toggle_in_motion()

    #a callback for when the rover's new position is sent.
    @pyqtSlot(Vector)
    def rover_pos_changed(self,position):
        try:
            node = self.grid.get_node(position.x,position.y)

            #we still only care if it moves it to a new node.
            if node != self.rover_position:
                print("rover position changed - Received from server")
                self.rover_position = node
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())

        self.grid_panel.redraw_grid()

    #opens a save dialog for the grid.        
    def save(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save Grid","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            print(fileName)
        realfilename = "your grid.grid"
        self.grid.save(realfilename)

    #opens a load dialog.
    def load(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Load Grid", "","All Files (*);;Python Files (*.py)", options=options)
        self.grid = Grid.load(fileName)
        self.grid_panel.setParent(None)
        self.grid_panel = None
        self.grid_panel = GridPanel(self,self.grid)
        self.grid_panel.show()


#this handles the visual appearence of the grid.
class GridPanel(QGroupBox):

    #initialize class
    def __init__(self,parent,grid):
        super().__init__(parent)

        #default settings
        self.setTitle("Grid")
        self.grid = grid
        self.buttons = []
        self.par = parent

        #prep the layout to have no empty space
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)

        #bind every button to a node.
        for i in range (0,self.grid.nodes_in_x):   
            for j in range(0,self.grid.nodes_in_y):
                temp = GridButton(self,self.grid.get_node(i,j))
                temp.x = j
                temp.y =self.grid.nodes_in_y - i
                temp.clicked.connect(parent.on_click_event(Vector(i,j)))
                layout.addWidget(temp,self.grid.nodes_in_y- j,i)
                self.buttons.append(temp)
                
        #set the grid up.
        self.setLayout(layout)
        self.move(20,20)
        self.resize(500,700)
        self.setAutoFillBackground(True)
        self.set_color(Qt.white)

        #redraw
        self.redraw_grid()

    #this lets us change the color of the panel
    def set_color(self,color):
        p = self.palette()
        p.setColor(self.backgroundRole(),color)
        self.setPalette(p)
        self.current_color = color

    #this allows us to redraw each button.
    def redraw_grid(self):

        #for every button, determine what its node is, then set its color
        for b in self.buttons:
            b.determine_type()
            if self.par.current_destination is not None and b.node == self.par.current_destination:
                #don't allow an invalid node to be a destination.
                if self.par.current_destination.node_type != 0:
                    self.par.current_destination = None
                else:
                    b.set_color(DESTINATION)
            elif b.node == self.par.rover_position:
                b.set_color(ROVER)

            elif b.node == self.par.home:
                b.set_color(HOME)

            elif self.par.simple_path.__contains__(b.node) and not self.par.remote_on:
                b.set_color(SIMPLE_PATH)

            elif self.par.current_path.__contains__(b.node):
                b.set_color(PATH)

#This is a button on a grid.  it has some expanded features involving nodes.        
class GridButton(QPushButton):

    #init button
    def __init__(self,parent,node):
        super().__init__(parent)

        #set default values.
        self.node = node
        self.default_color = OPEN_SPACE
        self.current_color = self.default_color
        self.setFlat(True)
        self.setAutoFillBackground(True)
        self.set_color(self.default_color)
        self.resize(10,10)

    #determine if we are an open space, border or obstacle.
    def determine_type(self):
        if self.node.node_type == 0:
            self.default_color = OPEN_SPACE
        elif self.node.node_type == 1:
            self.default_color = OBSTACLE
        elif self.node.node_type == 2:
            self.default_color = BORDER_SPACE
        self.current_color = self.default_color
        self.set_color(self.current_color)

    #this allows us to change the color
    def set_color(self,color):
        p = self.palette()
        p.setColor(self.backgroundRole(),color)
        self.setPalette(p)
        self.current_color = color





if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    ex.client.start()
    sys.exit(app.exec_())
