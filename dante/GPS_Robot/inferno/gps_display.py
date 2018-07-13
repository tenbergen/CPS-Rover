import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QPushButton,QGroupBox,QGridLayout,QHBoxLayout,QVBoxLayout,QRadioButton,QInputDialog,QLineEdit,QFileDialog
from PyQt5.QtCore import Qt,QRect
from PyQt5.QtGui import QIcon
from grid import *
from gps import *
import time
from vector import *
from advancedgopigo3 import *
from queue import Queue
from server import Server
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
        self.border_thickness = 1
        self.use_diagonals = True
        self.grid = Grid(self.grid_width,self.grid_height ,self.grid_x,self.grid_y,self.offset_x,self.offset_y,self.border_thickness,self.use_diagonals)

        #create the gps and related variables
        self.queue = Queue()
        gpg = AdvancedGoPiGo3(25)
        self.gps = GPS(self.queue,True,gpg,debug_mode=False)
        self.rover_position = self.grid.get_node(0,0)
        self.current_destination = None
        self.home = self.grid.get_node(1,1)
        self.current_path = []
        self.simple_path = []

        #setup server
        #self.server = Server(gpg,"dante.local",10000)
        
        #create the actual GUI
        self.initUI()

        #prep and run threads
        self.gps.set_position_callback(self.rover_pos_changed)
        self.gps.set_reached_point_callback(self.on_point_reached)
        self.gps.set_obstacle_callback(self.on_obstacle_found)
        self.gps.minimum_distance = 45
        self.gps.start()
        
        #self.server.start()
        #self.server.can_run(False)

    #actually builds the GUI
    def initUI(self):

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
        self.show()

    #when the window closes
    def closeEvent(self,event):
        print("program closing")

        #close the gps
        self.gps.cancel_early = True
        self.gps.thread_done = True
        self.gps.join()

        #close the server
        #self.server.join(.1)
        self.gps.gpg.stop()

    #allows us to change the window color
    def set_color(self,color):
        p = self.palette()
        p.setColor(self.backgroundRole(),color)
        self.setPalette(p)

    #get the mouse mode      
    def get_mouse_mode(self):
        return self.MOUSE_MODE

    #factory for button click events.
    def on_click_event(self,vector,button,grd):
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
            node.node_type = 1

            #TODO have it use new grid methods
            #we need to spread the grid.
            self.grid.all_obstacles.add(node)
            border = self.grid.spread_border(node,self.grid.border_thickness,self.grid.include_diagonals)

            #IF there is a destination in play and it is hit by the border, it needs to be cleared.
            if self.current_destination is not None:
                if border.__contains__(self.current_destination):
                    self.current_destination = None
                    self.current_path = []
                    self.simple_path = []

                #if there is something in the way of our current path.
                if not set(self.current_path).isdisjoint(border) and not self.current_path.__contains(node):
                    #we need a new path     
                    self.find_path()
                    self.gps.cancel_early = True

                    #if we are currently in motion.  let's go!
                    if self.start_stop_button.Text() == "Stop" and len(self.current_path)>0:
                        destination = self.grid.get_global_coord_from_node(self.current_path.pop(0))
                        self.queue.put(True)
                        self.queue.put(destination)
            return True
        return False
    
    #if an obstacle was removed from the map we need to recalculate our path and borders.
    def on_obstacle_removed(self,node):
        if node.node_type ==1:
            #TODO use new set methods
            node.node_type = 0
            self.grid.all_obstacles.remove(node)
            self.grid.remake_borders()
            self.find_path()
            return True
        return False

    #if a destination was placed somewhere on the map    
    def on_destination_added(self,node):
        if node.node_type == 0 and node != self.rover_position:
            self.current_destination = node
            self.find_path()
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
        button = self.start_stop_button
        #TODO consider adding a boolean toggle so there are less string comparisons.
        if button.text() == "Start":
            #if we have a path, we should toggle
            if len(self.current_path)>0:
                destination = self.grid.get_global_coord_from_node(self.current_path.pop(0))
                self.queue.put(True)
                self.queue.put(destination)
                button.setText("Stop")
        else:
            #stop moving and reset
            button.setText("Start")
            self.queue.queue.clear()
            self.queue.put(False)
            self.gps.cancel_early = True

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
            self.grid_panel.redraw_grid()

    #when auto/manual is toggled.        
    def on_autodrive_clicked(self):

        #TODO consider using a boolean for auto drive.
        button = self.autodrive_button
        if button.text() == "Switch To Manual":
            button.setText("Switch To Automatic")
            #self.server.can_run(True)
            self.start_stop_button.hide()
        else:
            button.setText("Switch To Manual")
            if self.start_stop_button.text() == "Stop":
                on_start_stop_clicked()
            #self.server.can_run(False)
            self.start_stop_button.show()

    #When the user tells the robot to go home.  drop everything and go home.        
    def on_go_home_clicked(self):
        if self.home is not None:
            #set the current destination
            self.current_destination = self.home
            self.find_path()

            #if we aren't in automatic and going, we need to be.
            go_button = self.start_stop_button
            auto_button = self.autodrive_button
            if auto_button.text() == "Switch To Automatic":
                self.on_autodrive_clicked()
            if go_button.text() == "Start":
                self.on_start_stop_clicked()
            self.grid_panel.redraw_grid()

    #this is a callback to signify that we have made it to a destination.    
    def on_point_reached(self,pos):
        print("callback-point reached")

        #send the next point to the gps
        self.send_point_to_gps()

        #if we are at our final destination, we are done.
        if len(self.current_path) == 0:
            self.start_stop_button.setText("Start")
            self.queue.put(False)

    #This is a callback for when the gps finds an obstacle.        
    def on_obstacle_found(self,position):

        #TODO remove magic numbers
        #We only care about it if it is in the grid.
        if position.x > 0 and position.y > 0 and position.x <= 2.5 and position.y <= 3.5:
            node = self.grid.node_from_global_coord(position)
            print("callback-obstacle found")

            #if it changes something we need to redraw the grid.
            if self.on_obstacle_added(node):
                self.grid_panel.redraw_grid()

    #a callback for when the rover's new position is sent.            
    def rover_pos_changed(self,position):
        #TODO remove magic numbers
        #We only care about it if it is in the grid.
        if position.x > 0 and position.y > 0 and position.x <= 2.5 and position.y <= 3.5:
        node = self.grid.node_from_global_coord(position)

        #we still only care if it moves it to a new node.
        if node != self.rover_position:
            print("callback-rover position changed")
            self.rover_position = node
            #if we arrived at a destination we are done.
            if self.current_destination is not None and node == self.current_destination:
                self.current_destination = None
                self.current_path = []
                #TODO turn off automatic pathfinding

            #we need a new full route.
            self.current_path,_ = self.grid.find_path(self.rover_position,self.current_destination)

    #Send nodes to the gps to go there!        
    def send_point_to_gps(self):

         #if we actually have somewhere to go
         if len(self.simple_path)>0:
             node = self.simple_path.pop(0)
             if node == self.rover_position:
                 node = self.simple_path.pop(0)
             destination = self.grid.get_global_coord_from_node(node)
             self.queue.put(destination)
    #has the grid perform pathfinding on a destination.  This often requires a redraw.         
    def find_path(self,redraw = True):
        if self.current_destination is not None:
            self.current_path,self.simple_path = self.grid.find_path(self.rover_position,self.current_destination)
        if redraw:
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
                temp.clicked.connect(parent.on_click_event(Vector(i,j),temp,self.grid))
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
    sys.exit(app.exec_())
