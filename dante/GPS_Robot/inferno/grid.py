from vector import *
import heapq
OPEN_SPACE = 0
OBSTACLE = 1
OBSTACLE_BORDER = 2
class Grid:
    def __init__(self, size_x, size_y, node_x, node_y, world_x=0, world_y=0, border_thickness=0, diagonal_default=True):
        self.include_diagonals = diagonal_default
        self.grid_size_x = size_x
        self.grid_size_y = size_y
        self.nodes_in_x = node_x
        self.nodes_in_y = node_y
        self.node_length_x = self.grid_size_x / self.nodes_in_x
        self.node_length_y = self.grid_size_y / self.nodes_in_y
        self.__world_bottom_left = Vector(world_x, world_y)              #the base start of the grid, used for returning "true"coordinates
        self.__number_of_nodes = self.nodes_in_x*self.nodes_in_y
        self.border_thickness = border_thickness                      #number of nodes a border extends from a obstacle
        self.nodes = [[]]            #2d array of coordinates
        self.nodes = [[Node(0,0,0) for y in range(node_y)] for x in range(node_x)]
        self.non_diagonal_weight = 10.0
        self.diagonal_weight = 14
        self.all_obstacles = set()     #List of all obstacles on the map for easy retrieval
        self.all_borders = set()       #List of all borders on the map for easy recalculations.
        self.__create_grid()

    def __create_grid(self):
        #TODO complete
        for x in range(0,self.nodes_in_x):
            for y in range(0,self.nodes_in_y):
                self.nodes[x][y] = Node(x,y,OPEN_SPACE)

        for x in range(0,self.nodes_in_x):
            for y in range(0,self.nodes_in_y):
                node = self.nodes[x][y]
                neighbors = []
                neighbors_with_diagonals = []
                for ix in range(-1,2):
                    for iy in range(-1,2):
                        if ix!=0 or iy!=0:
                            if x +ix >=0 and x + ix < self.nodes_in_x and iy + y >= 0  and y + iy < self.nodes_in_y:
                                neighbors_with_diagonals.append(self.nodes[x+ix][y+iy])
                            else:
                                neighbors_with_diagonals.append(None)
                for n in range(len(neighbors_with_diagonals)):
                    if n%2 == 1:
                        neighbors.append(neighbors_with_diagonals[n])
                neighbors = list(filter(None,neighbors))
                neighbors_with_diagonals = list(filter(None,neighbors_with_diagonals))
                node.set_neighbors(neighbors,False)
                node.set_neighbors(neighbors_with_diagonals,True)

    def get_num_of_nodes(self):
        return self.__number_of_nodes

    def get_node(self,x,y):
        return self.nodes[x][y]

    def node_from_local_coord(self,coords):
        # TODO add methods for insuring coord exists.
        # noinspection PyBroadException
        try:
            temp = self.nodes[coords.x,coords.y]
            return temp
        except:
            print("error")

    def node_from_global_coord(self,coords):
        # TODO add methods for insuring coord exists.
        # noinspection PyBroadException
        coords.x = int((coords.x - self.__world_bottom_left.x)/ self.node_length_x)
        coords.y = int((coords.y - self.__world_bottom_left.y)/ self.node_length_y)
        if coords.x >= 0 and coords.x <= self.nodes_in_x and coords.y >= 0 and coords.y <= self.nodes_in_y:
            temp = self.nodes[coords.x][coords.y]
        else:
            temp = self.nodes[0][0]
        return temp
    def get_global_coord_from_node(self,node):
        return Vector(((node.gridPos.x + self.__world_bottom_left.x) * self.node_length_x) + (.5 * self.node_length_x),\
                      ((node.gridPos.y + self.__world_bottom_left.y) * self.node_length_y) + (.5 * self.node_length_y))
    def get_neighbors(self,node,recurse=0,diagonals=True):
        neighbors = set()
        new_neighbors = set()
        #old_neighbors = []
        #old_neighbors.append(node)
        neighbors.add(node)
        while recurse > 0 and len(neighbors) != 0:
            for neighbor in neighbors:
                if neighbors is not None:
                    for n in neighbor.get_neighbors(diagonals):
                        if n is not None and n.node_type != 1:
                            new_neighbors.add(n)

            neighbors = neighbors.union(new_neighbors)
            new_neighbors = set()
            recurse-=1
        neighbors.remove(node)

        return neighbors
    def set_node(self,x,y,type):
        node = self.get_node(x,y)
        self.set_node(node,type)

    def set_node(self,node,type):
        node.node_type = type
        #TODO add border if obstacle

    def remake_borders(self):
        self.clear_borders()
        for obstacle in self.all_obstacles:
            self.spread_border(obstacle,self.border_thickness,self.include_diagonals)
    def clear_borders(self):
        for border in self.all_borders:
            border.node_type = 0
        self.all_borders = set()

    def spread_border(self,node,border_thickness = 0,diagonals=True):
        #TODO add override for border thickness

        neighbors = list(self.get_neighbors(node,border_thickness,diagonals))
        for n in neighbors:
            n.node_type = OBSTACLE_BORDER
            self.all_borders.add(n)

        node.node_type = OBSTACLE
        return neighbors

    def find_path(self,start,end):
        try:
            if start == end:
                return []
            elif end.node_type != OPEN_SPACE:
                return []

            open_set = [] #needs to be priority queue
            closed_set = set()
            current_node = start
            path_success = False
            path = []
            open_set.append(start)

            while len(open_set) > 0 and current_node != end:
                current_node = heapq.heappop(open_set)
                closed_set.add(current_node)
                if current_node == end:
                    path_success = True

                neighbor_list = current_node.get_neighbors(self.include_diagonals)
                for neighbor in neighbor_list:
                    if neighbor.node_type == OPEN_SPACE and not closed_set.__contains__(neighbor):
                        new_movement_cost = current_node.g_cost + self.__get_distance(current_node,neighbor)

                        if new_movement_cost < neighbor.g_cost or not open_set.__contains__(neighbor):
                            neighbor.g_cost = new_movement_cost
                            neighbor.h_cost = self.__get_distance(neighbor,end)
                            neighbor.parent = current_node
                            if open_set.__contains__(neighbor):
                                heapq.heapify(open_set)
                            else:
                                heapq.heappush(open_set,neighbor)

                if path_success:
                    path = self.__trace_path(start,end)
                    break
        except Exception as ex:
            print(ex)
        return path

    def __get_distance(self,a,b):
        dst_x = abs(a.gridPos.x - b.gridPos.x)
        dst_y = abs(a.gridPos.y - b.gridPos.y)

        if dst_x > dst_y:
            return self.diagonal_weight * dst_y + self.non_diagonal_weight * ( dst_x - dst_y)
        else:
            return self.diagonal_weight * dst_x + self.non_diagonal_weight * ( dst_y - dst_x)

    def __trace_path(self,start,end):
        path = []
        current_node = end
        while current_node != start:
            path.append(current_node)
            current_node = current_node.parent
        #path.remove(start)
        path.reverse()
        return path

    def save(self, filename, return_as_string=False):
        try:
            file = open(filename,'w')
            temp = ""+self.grid_size_x.__str__() +"\n" + self.grid_size_y.__str__() +"\n"
            temp +=   self.nodes_in_x.__str__() + "\n" + self.nodes_in_y.__str__() + "\n"
            temp +=   self.__world_bottom_left.x.__str__() + "\n" + self.__world_bottom_left.y.__str__() + "\n"
            temp +=   self.border_thickness.__str__() + "\n" + self.include_diagonals.__str__()
            
            for x in range(0,self.nodes_in_x):
                for y in range(0,self.nodes_in_y):
                    temp += "\n" + self.nodes[x][y].node_type.__str__()

            
            file.write(temp)
            
        except Exception as ex:
            print(ex)
        finally:
            file.close()
    @staticmethod
    def load(filename):
        try:
            file = open(filename,'r')
            data = file.readlines()
            size_x = float(data.pop(0))
            size_y = float(data.pop(0))
            nodes_x = int(data.pop(0))
            nodes_y = int(data.pop(0))
            world_x = float(data.pop(0))
            world_y = int(data.pop(0))
            thickeness = int(data.pop(0))
            diagonals = bool(data.pop(0))
            grid = Grid(size_x,size_y,nodes_x,nodes_y,world_x,world_y,thickeness,diagonals)
            for x in range(0,nodes_x):
                for y in range(0,nodes_y):
                    grid.get_node(x,y).node_type = int(data.pop(0))

        except Exception as ex:
            print(ex)
        finally:
            file.close()
        return grid
class Node:
    def __init__(self,x,y,node_type):
        self.gridPos = Vector(x,y)
        self.__neighbors = []
        self.__neighbors_with_diagonals = []
        self.node_type = node_type
        self.parent = None
        self.g_cost = 0
        self.h_cost = 0
    def f_cost(self):
        return self.g_cost + self.h_cost

    def set_neighbors(self, neighbors, use_diagonals=True):
        if use_diagonals:
            self.__neighbors_with_diagonals = neighbors
        else:
            self.__neighbors = neighbors

    def get_neighbors(self,use_diagonals=True):
        if use_diagonals:
            return self.__neighbors_with_diagonals
        else:
            return self.__neighbors

    def __eq__(self, other):
        return self.gridPos.x == other.gridPos.x and self.gridPos.y == other.gridPos.y

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.f_cost() < other.f_cost()
        #return self.g_cost < other.g_cost

    def __gt__(self, other):
        return self.f_cost() > other.f_cost()
        #return self.g_cost < other.g_cost
    def __key(self):
        return (self.gridPos.x,self.gridPos.y)
    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return str(self.gridPos.x + " " + self.gridPos.y)
