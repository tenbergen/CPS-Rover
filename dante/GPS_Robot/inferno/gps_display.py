import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QPushButton,QGroupBox,QGridLayout,QHBoxLayout,QVBoxLayout,QRadioButton
from PyQt5.QtCore import Qt,QRect
from grid import *

#Mouse states
MOUSE_MODE = 1
ADD_OBSTACLE = 1
REMOVE_OBSTACLE = 2
ADD_DESTINATION = 3
REMOVE_DESTINATION = 4

#Map Colors
OPEN_SPACE = Qt.gray
BORDER_SPACE = Qt.darkGray
OBSTACLE = Qt.black
DESTINATION = Qt.green
PATH = Qt.blue
ROVER = Qt.red

def btnstate(button):
    global MOUSE_MODE
    if button.text() == "Add Obstacle":
        MOUSE_MODE = ADD_OBSTACLE
    elif button.text() == "Remove Obstacle":
        MOUSE_MODE = REMOVE_OBSTACLE
    elif button.text() == "Add Destination":
        MOUSE_MODE = ADD_DESTINATION
    elif button.text() == "Remove Destination":
        MOUSE_MODE = REMOVE_DESTINATION

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "GPS Robot-Inferno"
        self.left = 10
        self.top = 100
        self.width = 1000
        self.height = 800
        self.grid_width = 2.5
        self.grid_height = 3.5
        self.grid_x = 20
        self.grid_y = 28
        self.offset_x = 0
        self.offset_y = 0
        self.border_thickness = 2
        self.use_diagonals = True
        self.grid = Grid(self.grid_width,self.grid_height ,self.grid_x,self.grid_y,self.offset_x,self.offset_y,self.border_thickness,self.use_diagonals)

        self.init_ui()

    #actually builds the GUI
    def init_ui(self):

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
        self.mouse_layout.resize(300,100)
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
        self.add_destination_button.setText("Add Destination")
        self.add_destination_button.toggled.connect(lambda:btnstate(self.add_destination_button))

        #remove destination
        self.remove_destination_button = QRadioButton(self)
        self.remove_destination_button.setText("Remove Destination")
        self.remove_destination_button.toggled.connect(lambda:btnstate(self.remove_destination_button))

        #configure mouse action layout
        gridl.setSpacing(10)
        gridl.addWidget(self.add_obstacle_button,0,0)
        gridl.addWidget(self.remove_obstacle_button,1,0)
        gridl.addWidget(self.add_destination_button,0,1)
        gridl.addWidget(self.remove_destination_button,1,1)
        self.mouse_layout.setLayout(gridl)

        # save and load buttons
        self.save_button = QPushButton(self)
        self.load_button = QPushButton(self)
        self.save_button.setText("Save")
        self.load_button.setText("Load")
        self.save_load_layout = QHBoxLayout()
        self.save_load_layout.addWidget(self.save_button)
        self.save_load_layout.addWidget(self.load_button)
        self.button_panel.addLayout(self.save_load_layout)
        self.button_panel.setGeometry(QRect(600, 150, 300, 100))
        self.show()



    def set_color(self,color):
        p = self.palette()
        p.setColor(self.backgroundRole(),color)
        self.setPalette(p)
    def get_mouse_mode(self):
        return self.MOUSE_MODE


class GridPanel(QGroupBox):
    def __init__(self,parent,grid):
        super().__init__(parent)
        self.setTitle("Grid")
        self.grid = grid
        self.current_destination = None
        self.buttons = []
        self.rover_position = self.grid.get_node(0,0)
        self.current_path = []
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(0)
        for i in range (0,self.grid.nodes_in_x):   #this will eventually be dependent on the grid.
            for j in range(0,self.grid.nodes_in_y):
                temp = GridButton(self,self.grid.get_node(i,j))
                temp.x = j
                temp.y =self.grid.nodes_in_y - i
                temp.clicked.connect(self.on_click_event(Vector(i,j),temp,self.grid))
                layout.addWidget(temp,self.grid.nodes_in_y- j,i)
                self.buttons.append(temp)
        self.setLayout(layout)
        self.move(20,20)
        self.resize(500,700)
        self.setAutoFillBackground(True)
        self.set_color(Qt.white)
        self.redraw_grid()

    def set_color(self,color):
        p = self.palette()
        p.setColor(self.backgroundRole(),color)
        self.setPalette(p)
    #put click event here with button and coord as parameters?
    def on_click_event(self,vector,button,grd):
        grid = grd
        def click_event():
            x = vector.x
            y = vector.y
            node = grid.nodes[x][y]
            something_happened = False
            print("My name is "+node.gridPos.x.__str__() +" "+ node.gridPos.y.__str__())
            print("My node Type is: "+node.node_type.__str__())
            print(int(MOUSE_MODE).__str__())
            #global ADD_OBSTACLE
            if MOUSE_MODE == ADD_OBSTACLE:
                if node.node_type != 1 or button.current_color != DESTINATION or button.current_color != ROVER:
                    something_happened = True
                    node.node_type = 1
                    button.default_color = OBSTACLE
                    button.current_color = OBSTACLE
                    button.set_color(OBSTACLE)
                    grid.all_obstacles.add(node)
                    border = grid.spread_border(node,grid.border_thickness,grid.include_diagonals)
                    #TODO if a path was interrupted call event to recalculate path
                    if self.current_destination is not None:
                        if border.__contains__(self.current_destination):
                            self.current_destination = None
                            self.current_path = []
                        elif not set(self.current_path).isdisjoint(border):
                            self.find_path()
            elif MOUSE_MODE == REMOVE_OBSTACLE:
                if node.node_type ==1:
                    something_happened = True
                    node.node_type = 0
                    self.grid.all_obstacles.remove(node)
                    button.default_color = OPEN_SPACE
                    button.current_color = OPEN_SPACE
                    button.set_color(OPEN_SPACE)
                    self.grid.remake_borders()
                    self.find_path()

            elif MOUSE_MODE == ADD_DESTINATION:
                if node.node_type == 0 and node != self.rover_position:
                    something_happened = True
                    self.current_destination = node
                    button.current_color = DESTINATION
                    button.set_color(DESTINATION)
                    self.find_path()

            elif MOUSE_MODE == REMOVE_DESTINATION:
                if self.current_destination is not None and node == self.current_destination:
                    something_happened = True
                    self.current_destination = None
                    self.current_path = []

            if something_happened:
                self.redraw_grid()

        return click_event

    def redraw_grid(self):
        for b in self.buttons:
            b.determine_type()
            if self.current_destination is not None and b.node == self.current_destination:
                if self.current_destination.node_type != 0:
                    self.current_destination = None
                else:
                    b.set_color(DESTINATION)
                    b.current_color = DESTINATION
            elif b.node == self.rover_position:
                b.set_color(ROVER)
                b.current_color = ROVER

            elif self.current_path.__contains__(b.node):
                b.set_color(PATH)
                b.current_color = PATH
            #if they are on the path or are destination or rover

    def find_path(self):
        if self.current_destination is not None:
            self.current_path = self.grid.find_path(self.rover_position,self.current_destination)

    def rover_pos_changed(self,position):
        if position.x >= 0 and position.y > 0 and position.x <= 2.5 and position.y <= 3.5:
            node = self.grid.node_from_global_coord(position)

            if node != self.rover_position:
                self.rover_position = node
                self.redraw_grid()

    def on_path_changed(self):
        if self.current_path is not None and len(self.current_path) > 0:
            self.current_path.pop(0)
            self.redraw_grid()

    def on_obstacle_found(self,position):
        if position.x >= 0 and position.y > 0 and position.x <= 2.5 and position.y <= 3.5:
            node = self.grid.node_from_global_coord(position)
            node.node_type = 1
            self.grid.all_obstacles.add(node)
            border = self.grid.spread_border(node, self.grid.border_thickness, self.grid.include_diagonals)
            # TODO if a path was interrupted call event to recalculate path
            if self.current_destination is not None:
                if border.__contains__(self.current_destination):
                    self.current_destination = None
                    self.current_path = []
                elif not set(self.current_path).isdisjoint(border):
                    self.find_path()
class GridButton(QPushButton):
    def __init__(self,parent,node):
        super().__init__(parent)
        self.node = node
        self.default_color = OPEN_SPACE
        self.current_color = self.default_color
        self.setFlat(True)
        self.setAutoFillBackground(True)
        self.set_color(self.default_color)
        self.resize(10,10)
    def determine_type(self):
        if self.node.node_type == 0:
            self.default_color = OPEN_SPACE
        elif self.node.node_type == 1:
            self.default_color = OBSTACLE
        elif self.node.node_type == 2:
            self.default_color = BORDER_SPACE
        self.current_color = self.default_color
        self.set_color(self.current_color)

    def set_color(self,color):
        p = self.palette()
        p.setColor(self.backgroundRole(),color)
        self.setPalette(p)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
