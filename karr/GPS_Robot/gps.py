#This class serves as a wrapper for marvelmind and gopigo movement.
from gopigo import *
from marvelmind import MarvelmindHedge
from time import sleep
import sys
from math import *
from transform import Transform
from vector import Vector
class GPS:
    #initialize the class
    def __init__(self,perform_warmup,debug_mode=False,transform2D=Transform()):
        #initialize the required components
        self.__debug = debug_mode
        self.transform = transform2D

        #start the hedge
        self.__hedge = MarvelmindHedge(tty = "/dev/ttyACM0", adr=10, debug=False)
        self.__hedge.start()
        sleep(.1)
                   
        #set initial position
        self.__update_position()
        if self.__debug:
            self.__hedge.print_position()

        #set initial rotation
        if perform_warmup:
            self.determine_rotation()
        else:
            self.transform.rotation = 0

    #converts a hedge position into a 2D Vector in the transform
    def __update_position(self):
        pos = self.__hedge.position()
        self.transform.position.x = pos[1]
        self.transform.position.y = pos[2]

    #returns the current distance from the destination    
    def distance(self,destination):
        return self.__distance(self.transform.position(),destination)
        
    #Gets the distance between start and end
    def __distance(self,a,b):
        return pow(pow(a[0]-b[0],2) + pow(a[1] - b[1],2),.5)

    #get the current position of rover
    def get_position(self):
        return self.tranform.position

    #get the current rotation
    def get_rotation(self):
        return self.transform.rotation


    #determine current rotation
    def determine_rotation(self):
        set_speed(100)
        start_pos = Vector(self.transform.position)
        fwd()
        sleep(1)
        stop()
        sleep(1)
        self.__update_position()
        new_pos = Vector(self.transform.position)
        bwd()
        sleep(1)
        stop()

        self.transform.rotation = self.getAngle(new_pos,start_pos)
        if self.__debug:
            print "determined Rotation: ",self.transform.rotation
            
    def stop(self):
        self.__hedge.stop()

    #get the angle between two points and horizontal axis
    #a is the destination
    #b is the pivot point
    def getAngle(self,a,b):
        #get the angle between vector and horizontal axis
        dx =  a.x - b.x
        dy =  a.y - b.y
        rot_inRad = atan2(dy,dx)

        rotate = math.degrees(rot_inRad)
        if rotate <0:
            rotate = 360 + rotate
        if self.__debug:
            print "getangle returned: ",rotate
        return rotate

    #travel to a given destination
    def goto_point(self,coord):
        #rotate to face point
        self.turn_to_face(coord)
##        #probably needs rewrite
##        angle_to_point = self.getAngle(coord,self.transform.position)
##        angle = angle_to_point - self.transform.rotation
##        if angle < 0:
##            angle +=360
##        angle = angle % 360
##        turn_left_wait_for_completion(angle)

        
        sleep(.5)
        dst = self.distance(coord)
        fwd()
        while dst > .02:
            self.__update_position()
            olddst = dst
            dst = self.distance(coord)
            if self.__debug:
                print "distance",dst
                print "current position", self.__pos
                print "destination", coord
                print "************************"
            if(olddst < dst):
                stop()
                self.determine_rotation()
                self.goto_point(coord)
                break
            sleep(.5)
        stop()

    #rotate left by degrees
    def __turn_left(self,degrees):
        if self.__debug:
            print "turning left."
        set_speed(50)
        turn_left_wait_for_completion(degrees)
        set_speed(100)

    #rotate right by degrees
    def __turn_right(self,degrees):
        if self.__debug:
            print "turning right."
        set_speed(50)
        turn_right_wait_for_completion(degrees)
        set_speed(100)

    #turn to a specific angle
    def turn_to_angle(self,angle):
        difference = int(abs(self.transform.rotation - angle))
        if self.__debug:
            print "current rotation: ",self.transform.rotation
            print "destination angle: ",angle
            print "rotation needed: ",difference
        
        if difference != 0:
            if self.transform.rotation > angle:
                if self.__debug:
                    print "current angle is greater."
                if(difference<=180):
                    if self.__debug:
                        print "difference is less than 180."
                    self.__turn_left(difference)
                else:
                    if self.__debug:
                        print "difference is greater than 180."
                    self.__turn_right(difference-180)
            else:
                if self.__debug:
                    print "desintation angle is greater."
                if(difference<=180):
                    if self.__debug:
                        print "difference is less than 180."
                    self.__turn_right(difference)
                else:
                    if self.__debug:
                        print "difference is greater than 180."
                    self.__turn_left(difference-180)
            self.transform.rotation = angle

    #rotate to face a specific point
    def turn_to_face(self,coord):
        angle = self.get_angle(coord,self.transform.position)
        self.turn_to_angle(angle)
