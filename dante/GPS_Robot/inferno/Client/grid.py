from vector import *
import heapq
OPEN_SPACE = 0
OBSTACLE = 1
OBSTACLE_BORDER = 2

#This class is used for creating a 2d square grid that implements an a* pathfinding solution.
class Grid:
    def __init__(self, size_x, size_y, node_x, node_y, world_x=0, world_y=0, border_thickness=0, diagonal_default=True):
        #initialize default values
        self.include_diagonals = diagonal_default
        self.grid_size_x = size_x
        self.grid_size_y = size_y
        self.nodes_in_x = node_x
        self.nodes_in_y = node_y
        self.node_length_x = self.grid_size_x / self.nodes_in_x
        self.node_length_y = self.grid_size_y / self.nodes_in_y
        self.border_thickness = border_thickness        #number of nodes a border extends from a obstacle

        #pathfinding waits
        self.non_diagonal_weight = 10.0
        self.diagonal_weight = 14   #the hyptenuse of a 10,10 triangle is roughtly 14

        #set up important count values
        self.__world_bottom_left = Vector(world_x, world_y)              #the base start of the grid, used for returning "true"coordinates
        self.__number_of_nodes = self.nodes_in_x*self.nodes_in_y

        #these sets keep track of obstacles and borders for convenience.
        self.all_obstacles = set()     #List of all obstacles on the map for easy retrieval
        self.all_borders = set()       #List of all borders on the map for easy recalculations.

        #set up the grid
        self.nodes = [[]]            #2d array of coordinates
        self.nodes = [[Node(0,0,0) for y in range(node_y)] for x in range(node_x)]
        self.__create_grid()

    #This method intializes the grid.  It should be run during the constructor and then never again.
    def __create_grid(self):
        #create a blank map
        for x in range(0,self.nodes_in_x):
            for y in range(0,self.nodes_in_y):
                self.nodes[x][y] = Node(x,y,OPEN_SPACE)

        #assign each node its neighbors.
        #NOTE, this should probably be removed and have neigbors be calculated as needed.
        #this uses too much ram as the size increases.
        for x in range(0,self.nodes_in_x):
            for y in range(0,self.nodes_in_y):
                node = self.nodes[x][y]
                neighbors = []
                neighbors_with_diagonals = []
                #for every node, find its neighbors.
                for ix in range(-1,2):
                    for iy in range(-1,2):
                        if ix!=0 or iy!=0:
                            if x +ix >=0 and x + ix < self.nodes_in_x and iy + y >= 0  and y + iy < self.nodes_in_y:
                                neighbors_with_diagonals.append(self.nodes[x+ix][y+iy])
                            else:
                                neighbors_with_diagonals.append(None)
                #this doens't actually work.
                for n in range(len(neighbors_with_diagonals)):
                    if n%2 == 1:
                        neighbors.append(neighbors_with_diagonals[n])
                neighbors = list(filter(None,neighbors))
                neighbors_with_diagonals = list(filter(None,neighbors_with_diagonals))
                node.set_neighbors(neighbors,False)
                node.set_neighbors(neighbors_with_diagonals,True)

    #get the number of nodes
    def get_num_of_nodes(self):
        return self.__number_of_nodes

    #return a node from an x ,y grid point
    def get_node(self,x,y):
        return self.nodes[x][y]

    #return a node from local coordinates.  like node_from_global_coord, but assuming bottom left is 0,0
    def node_from_local_coord(self,coords):
        x = int((coords.x)/ self.node_length_x)
        y = int((coords.y)/ self.node_length_y)
        if coords.x >= 0 and coords.x <= self.nodes_in_x and coords.y >= 0 and coords.y <= self.nodes_in_y:
            temp = self.nodes[x][y]
        else:
            temp = None
        return temp

    #takes a "real world" coordinate converts it into a node that is returned.
    def node_from_global_coord(self,coords):
        x = int((coords.x - self.__world_bottom_left.x)/ self.node_length_x)
        y = int((coords.y - self.__world_bottom_left.y)/ self.node_length_y)
        if coords.x >= 0 and coords.x <= self.nodes_in_x and coords.y >= 0 and coords.y <= self.nodes_in_y:
            temp = self.nodes[x][y]
        else:
            temp = None
        return temp

    #get the center of a coordinate in terms of the local coordinates.
    def get_local_coord_from_node(self,node):
        return Vector(((node.gridPos.x) * self.node_length_x) + (.5 * self.node_length_x),\
                      ((node.gridPos.y) * self.node_length_y) + (.5 * self.node_length_y))


    #returns the center of a node in terms of global coordinates.
    def get_global_coord_from_node(self,node):
        return Vector(((node.gridPos.x + self.__world_bottom_left.x) * self.node_length_x) + (.5 * self.node_length_x),\
                      ((node.gridPos.y + self.__world_bottom_left.y) * self.node_length_y) + (.5 * self.node_length_y))

    #get all the neighbors of a node in any distance.
    def get_neighbors(self,node,recurse=0,diagonals=True):
        neighbors = set()
        new_neighbors = set()

        #get each neighbor
        neighbors.add(node)
        while recurse > 0 and len(neighbors) != 0:
            for neighbor in neighbors:
                #get each of these nieghbor's neighbor if they aren't none.
                if neighbors is not None:
                    for n in neighbor.get_neighbors(diagonals):
                        if n is not None and n.node_type != 1:
                            new_neighbors.add(n)

            #we now have a new set of neighbors to check
            neighbors = neighbors.union(new_neighbors)
            new_neighbors = set()
            recurse-=1
            
        #the start node is not a neighbor to itself
        neighbors.remove(node)

        return neighbors

    #set a node to a given type
    def set_node(self,x,y,node_type):
        node = self.get_node(x,y)
        if node.node_type!=node_type:
            self.set_node_type(node,node_type)
            
    #set a nodes type.
    def set_node_type(self,node,node_type):
        #add border if obstacle otherwise re-calcing borders is neccessary
        old_type = node.node_type
        node.node_type = node_type
        if node_type == OBSTACLE:
            self.spread_border(node,self.border_thickness, self.include_diagonals)
            self.all_obstacles.add(node)
        else:
            if old_type == OBSTACLE:
                self.all_obstacles.remove(node)
            elif old_type == OBSTACLE_BORDER:
                self.all_borders.remove(node)
            self.remake_borders()
            

    #this remakes all borders
    def remake_borders(self):
        self.clear_borders()

        #draw borders for every obstacle
        for obstacle in self.all_obstacles:
            self.spread_border(obstacle,self.border_thickness,self.include_diagonals)

    #remove all borders from the map.
    def clear_borders(self):
        for border in self.all_borders:
            border.node_type = 0
        self.all_borders = set()

    #this adds borders from all obstacles.
    def spread_border(self,node,border_thickness = 0,diagonals=True):

        #recursively get all neighbors and then turn them into borders.
        neighbors = list(self.get_neighbors(node,border_thickness,diagonals))
        for n in neighbors:
            if n.node_type == OPEN_SPACE:
                n.node_type = OBSTACLE_BORDER
                self.all_borders.add(n)

        #if the node wasn't and obstacle before it had better be now.
        node.node_type = OBSTACLE
        return neighbors

    #Uses an A* pathfinding solution inorder to find the shortest route to the destination.
    #it returns a tuple, the full path and a simplified path.
    def find_path(self,start,end):
        #initialize lists
        path = []
        simple_path = []

        #if the pathfinding solution is not worth calculating.
        if end is None or start is None:
            return [],[]
        elif start == end:
            return [],[]
        elif end.node_type != OPEN_SPACE:
            return [],[]
        
        #initialize variables
        open_set = [] 
        closed_set = set()
        current_node = start
        path_success = False

        #let's go
        open_set.append(start)
        while len(open_set) > 0 and current_node != end:

            #get the next node, don't use it again.
            current_node = heapq.heappop(open_set)
            closed_set.add(current_node)

            #if we're Done get the path and break
            if current_node == end:
                path = self.__trace_path(start,end)
                simple_path = self.__simplify_path(path)
                break

            #get paths for all the current neighbors
            neighbor_list = current_node.get_neighbors(self.include_diagonals)
            for neighbor in neighbor_list:

                #if this is a nieghbor worth calculating calculate its cost.
                if neighbor.node_type == OPEN_SPACE and not closed_set.__contains__(neighbor):
                    new_movement_cost = current_node.g_cost + self.__get_distance(current_node,neighbor)

                    #If this is a better route, or this is a new node.
                    if new_movement_cost < neighbor.g_cost or not open_set.__contains__(neighbor):
                        neighbor.g_cost = new_movement_cost
                        neighbor.h_cost = self.__get_distance(neighbor,end)
                        neighbor.parent = current_node

                        #If the node is already going to be calculated, resort it.  otherwise add it to the set.
                        if open_set.__contains__(neighbor):
                            heapq.heapify(open_set)
                        else:
                            heapq.heappush(open_set,neighbor)

        return path,simple_path

    #this simplifies an existing path to only include nodes that cause a direction change
    def __simplify_path(self,path):
        old_dir = Vector(0,0)
        simple_path = []

        # for every member of the path, except the first
        for i in range(1,len(path)):
            #use the previous node to include
            new_dir = Vector(path[i-1].gridPos.x-path[i].gridPos.x,path[i-1].gridPos.y-path[i].gridPos.y)
            if new_dir != old_dir:
                simple_path.append(path[i])
            old_dir = new_dir
            
        #the end destination is also important.
        simple_path.append(path[-1])
        return simple_path

    #calculate the distance, note that this is not a straight line it is by grid movement.
    def __get_distance(self,a,b):
        dst_x = abs(a.gridPos.x - b.gridPos.x)
        dst_y = abs(a.gridPos.y - b.gridPos.y)

        if dst_x > dst_y:
            return self.diagonal_weight * dst_y + self.non_diagonal_weight * ( dst_x - dst_y)
        else:
            return self.diagonal_weight * dst_x + self.non_diagonal_weight * ( dst_y - dst_x)

    #traceback the path of nodes.  NOTE do note send this a garbage start and end otherwise it will continue forever.
    def __trace_path(self,start,end):
        path = []
        current_node = end
        while current_node != start:
            path.append(current_node)
            current_node = current_node.parent

        #this creates the path backwards.
        path.reverse()
        return path

    #this allows saving the saving of this grid to file.  It can also be send back as a string for networking purposes.
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
            if return_as_string:
                return temp

    #this creates a new grid from scratch for use.
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

#this class represents a single point on a node.  
class Node:
    def __init__(self,x,y,node_type):
        self.gridPos = Vector(x,y)
        self.__neighbors = []
        self.__neighbors_with_diagonals = []
        self.node_type = node_type
        self.parent = None
        self.g_cost = 0         #cost to get to this node
        self.h_cost = 0         #cost to get from this node to a destination

    #the total weight of a node
    def f_cost(self):
        return self.g_cost + self.h_cost

    #set these neighbors
    def set_neighbors(self, neighbors, use_diagonals=True):
        if use_diagonals:
            self.__neighbors_with_diagonals = neighbors
        else:
            self.__neighbors = neighbors

    #this returns the nodes neighbors
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

    def __gt__(self, other):
        return self.f_cost() > other.f_cost()
    
    def __key(self):
        return (self.gridPos.x,self.gridPos.y)
    
    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return str(self.gridPos.x) + " " + str(self.gridPos.y)
