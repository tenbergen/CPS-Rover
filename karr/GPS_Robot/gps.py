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
    def __init__(self,perform_warmup,speed=75,debug_mode=False,transform2D=Transform()):
        #initialize the required components
        self.__debug = debug_mode
        self.transform = transform2D
        self.speed = speed
        set_speed(self.speed)
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
    def distance(self,destination,update=False):
        if update:
            self.__update_position()
        return self.__distance(self.transform.position,destination)
        
    #Gets the distance between start and end
    def __distance(self,a,b):
        return pow(pow(a.x-b.x,2) + pow(a.y - b.y,2),.5)

    #get the current position of rover
    def get_position(self):
        return self.tranform.position

    #get the current rotation
    def get_rotation(self):
        return self.transform.rotation


    #determine current rotation
    def determine_rotation(self):
        set_speed(100)

        fwd()
        sleep(1.5)
        stop()
        sleep(1)
        self.__update_position()
        new_pos = Vector(self.transform.position)
        bwd()
        sleep(1.5)
        stop()
        sleep(1)
        self.__update_position()
        start_pos = Vector(self.transform.position)
        self.transform.rotation = self.get_angle(new_pos,start_pos)
        if self.__debug:
            print "determined Rotation: ",self.transform.rotation
        set_speed(self.speed)
            
    def stop(self):
        self.__hedge.stop()

    #get the angle between two points and horizontal axis
    #a is the destination
    #b is the pivot point
    def get_angle(self,b,a):
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
        sleeptick = .100
        count = 0
        distance_threshold = .1
        self.__update_position()
        dst = self.distance(coord)
        if dst <= distance_threshold:
            return
        #rotate to face point
        self.turn_to_face(coord)
        sleep(sleeptick)
        self.__set_encoders()
        fwd()
        sleep(sleeptick)
        while dst >= distance_threshold:
            sleep(sleeptick)
            self.__update_position()
            olddst = dst
            dst = self.distance(coord)
            if self.__debug:
                print"old dst",olddst
                print "distance",dst
                print "current position", self.transform.position
                print "destination", coord
                print "************************"
            if(olddst < dst):
                count +=1
            else:
                count = 0
            if count ==3:
                stop()
                self.determine_rotation()
                self.__update_position()
                self.turn_to_face(coord)
                self.__set_encoders()                       
                fwd()
                count = 0
            self.__balance()
        stop()
        self.__update_position()

    #rotate left by degrees
    def __turn_left(self,degrees):
        if self.__debug:
            print "turning left."
        set_speed(100)
        turn_left_wait_for_completion(degrees)
        set_speed(self.speed)

    #rotate right by degrees
    def __turn_right(self,degrees):
        if self.__debug:
            print "turning right."
        set_speed(100)
        turn_right_wait_for_completion(degrees)
        set_speed(self.speed)

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
                    self.__turn_left(difference)#was left
                else:
                    if self.__debug:
                        print "difference is greater than 180."
                    self.__turn_right(360-difference)
            else:
                if self.__debug:
                    print "destintation angle is greater."
                if(difference<=180):
                    if self.__debug:
                        print "difference is less than 180."
                    self.__turn_right(difference)#was right
                else:
                    if self.__debug:
                        print "difference is greater than 180."
                    self.__turn_left(360-difference)
            self.transform.rotation = angle
        self.determine_rotation()
        if self.__debug:
            print "attenoted deviation:",self.transform.rotation - angle
        if int(abs(self.transform.rotation - angle)) >5:
            self.turn_to_angle(angle)

    #rotate to face a specific point
    def turn_to_face(self,coord):
        angle = self.get_angle(coord,self.transform.position)
        self.turn_to_angle(angle)

    def __balance(self):
        offset = 10
        imbalance = self.__find_imbalance()
        if self.__debug:
            print "imbalance: ",imbalance
        if imbalance == 1:
            set_right_speed(self.speed + offset)
            set_left_speed(self.speed)
        elif imbalance == -1:
            set_right_speed(self.speed)
            set_left_speed(self.speed + offset)
        else:
            set_right_speed(self.speed)
            set_left_speed(self.speed)
        
    def __find_imbalance(self):
        left = enc_read(0)
        right = enc_read(1)
        
        left_dif = left - self.left_enc
        right_dif = right - self.right_enc
        if self.__debug:
            print "encoder differences:",left_dif,right_dif
        if left_dif +5< right_dif:
            return -1
        elif right_dif +5< left_dif:
            return 1
        else:
            return 0
    def __set_encoders(self):
        self.left_enc =enc_read(0)
        self.right_enc = enc_read(1)

        
