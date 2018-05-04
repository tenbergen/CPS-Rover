#This class serves as a wrapper for marvelmind and gopigo movement.
from gopigo import *
from marvelmind import MarvelmindHedge
from time import sleep
import sys
from math import *
class GPS:
    #initialize the class
    def __init__(self,perform_warmup):
        self.hedge = MarvelmindHedge(tty = "/dev/ttyACM0", adr=10, debug=False)
        self.hedge.start()
        sleep(.1)
        self.hedge.print_position()
        self.hedge.print_position()
        self.__pos = self.convert2D(self.hedge.position())
        print "position",self.hedge.position()
        if perform_warmup:
            self.rotation = self.determine_starting_rotation()
        else:
            self.rotation = 0 # degrees from (1,0)

    #converts an array into a 2D Vector
    def convert2D(self,coord):
        new_coord = [coord[1],coord[2]]
        return new_coord
    def distance(self,destination):
        return self.__distance(self.position(),destination)
        
    #Gets the distance between start and end
    def __distance(self,a,b):
        return pow(pow(a[0]-b[0],2) + pow(a[1] - b[1],2),.5)

    #current position of rover
    def position(self):
        self.__pos= self.convert2D(self.hedge.position())
        return self.__pos
    def update_rotation(self,rot):
        self.rotation = rot
    #determine current rotation
    def determine_starting_rotation(self):
        set_speed(100)
        start_pos = self.position()
        fwd()
        sleep(1)
        stop()
        new_pos = self.position()
        sleep(1)
        bwd()
        sleep(1)
        stop()

        self.rotation = self.getAngle(new_pos,start_pos)
        print "Rotation",self.rotation
        return self.rotation
    def stop(self):
        self.hedge.stop()

    def getAngle(self,a,b):
        #get the angle between vector and horizontal axis
        dx =  a[0] - b[0]
        dy =  a[1] - b[1]
        rot_inRad = atan2(dy,dx)

        rotate = math.degrees(rot_inRad)
        if rotate < 0:
            rotate = 360 + rotate
        return rotate

    def goto_point(self,coord):
        angle_to_point = self.getAngle(coord,self.position())
        print angle_to_point
        angle = angle_to_point - self.rotation
        if angle < 0:
            angle +=360
        angle = angle % 360
        turn_left_wait_for_completion(angle)
        sleep(.5)
        dst = self.distance(coord)
        fwd()
        while dst > .02:
            olddst = dst
            dst = self.distance(coord)
            print "distance",dst
            print "current position", self.__pos
            print "destination", coord
            print "************************"
            if(olddst < dst):
                stop()
                self.determine_starting_rotation()
                self.goto_point(coord)
                break
            sleep(.5)
        stop()

    def turnleft(self,degrees):
        set_speed(50)
        turn_left_wait_for_completion(angle)
        set_speed(100)

    def turn_to_angle(self,angle):
        angle =  angle - self.rotation
        if angle < 0:
            angle +=360
        angle = angle % 360
        turn_left_wait_for_completion(angle)
