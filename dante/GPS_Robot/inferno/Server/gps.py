from advancedgopigo3 import *
from marvelmind import MarvelmindHedge
import time
import sys
import math
from vector import Vector
from threading import Thread
from queue import Queue

DISTANCE_FROM_CENTER = 15


# This class serves as a wrapper for marvelmind and gopigo movement.
# It uses them together to find its way to destinations
class GPS(Thread):

    # initialize the class
    def __init__(self, q, front_hedge,rear_hedge, gopigo, speed=300, debug_mode=False):
        Thread.__init__(self)

        # initialize the gopigo components
        self.gpg = gopigo
        self.distance_sensor = self.gpg.gpg.init_distance_sensor()

        # initialize gps "settings"
        self.threshold = .06
        self.command_queue = q
        self.minimum_distance = 45
        self.__debug = debug_mode
        self.cancel_early = False
        self.thread_done = False

        # setup geometry information
        self.transform = Transform()
        self.rear_position = Vector()
        self.speed = speed
        self.gpg.set_speed(speed)
        self.destination = None

        # setup thread information
        self.path = []

        # start the hedge
        self.front_hedge = front_hedge
        self.rear_hedge = rear_hedge
        self.__hedge = MarvelmindHedge(tty="/dev/ttyACM0",recieveUltrasoundPositionCallback=self.position_update)
        self.__hedge.start()

        # setup callbacks
        self.__position_callback = None
        self.__obstacle_callback = None
        self.__reached_point_callback = None

        # set initial position
        #time.sleep(.1)
        #self.__update_position()
        if self.__debug:
            self.__hedge.print_position()

        # set initial rotation
        #if perform_warmup:
            #self.determine_rotation()
        #else:
            #self.transform.rotation = 0

        # setup IMU
        self.turn_to_angle(90)
        # self.imu = inertial_measurement_unit.InertialMeasurementUnit()
        # print self.imu.read_euler()

    # used if it is being run like a thread.  Use the queue sent in to add commands to the gps
    def run(self):

        # FOREVER
        while not self.thread_done:

            # if we have a command
            if not self.command_queue.empty():
                command = self.command_queue.get()

                # goto point
                self.destination = command
                self.goto_point(self.destination)

            # if we have nothing to do
            else:
                # update where we are and run callbacks
                #self.__update_position()
                self.get_position_callback()
                self.check_for_obstacles()
                time.sleep(.1)
        self.stop()

    def position_update(self):
        position = self.__hedge.position()
        #print("hedge:",position[0])
        if position[0] == self.front_hedge:
            self.transform.position = self.__convert_hedge_coords(position)
        else:
            self.rear_position = self.__convert_hedge_coords(position)
        self.transform.rotation = self.get_angle(self.transform.position,self.rear_position)

    # converts a hedge position into a 2D Vector in the transform
    def __convert_hedge_coords(self,position):
        return Vector(position[1],position[2])

    # the following methods set callbacks or get them.
    # If they are getting them, they will do nothing if None is used
    def set_position_callback(self, callback):
        self.__position_callback = callback

    def get_position_callback(self):
        if self.__position_callback is not None:
            self.__position_callback(self.transform.position)

    def set_obstacle_callback(self, callback):
        self.__obstacle_callback = callback

    def get_obstacle_callback(self, pos):
        if self.__obstacle_callback is not None:
            self.__obstacle_callback(pos)

    def set_reached_point_callback(self, callback):
        self.__reached_point_callback = callback

    def get_reached_point_callback(self):
        if self.__reached_point_callback is not None:
            self.__reached_point_callback(self.transform.position)
        print("destination reached!")

    # returns the current distance from the destination
    def distance(self, destination, update=False):
        #if update:
            #self.__update_position()
        return self.__distance(self.transform.position, destination)

    # Gets the distance between start and end
    def __distance(self, a, b):
        return pow(pow(a.x - b.x, 2) + pow(a.y - b.y, 2), .5)

    def distance_to_destination(self):
        return self.distance(self.destination, True)

    # get the current position of rover
    def get_position(self):
        return self.tranform.position

    # get the current rotation
    def get_rotation(self):
        return self.transform.rotation

    # determine current rotation
    def determine_rotation(self):
        # ensure speed is constant and equal across wheels
        self.gpg.set_speed(self.speed)
        outcoord = []
        incoord = []
        DISTANCE = 25

        # go forward
        self.gpg.drive_cm(DISTANCE)
        self.gpg.stop()
        time.sleep(1)

        # double check we aren't accidentally at our destination
        if self.destination != None:
            if self.distance_to_destination() <= self.threshold:
                return

        # record positions at that point
        for i in range(0, 10):
            time.sleep(.1)
            self.__update_position()
            outcoord.append(self.transform.position)

        # get the average (new_pos is used first as it indicates the direction we plan to go)
        new_pos = Vector(sum(c.x for c in outcoord) / 10, sum(c.y for c in outcoord) / 10)

        # go back
        self.gpg.drive_cm(-DISTANCE)
        self.gpg.stop()
        time.sleep(1)

        # record positions as this point too
        for i in range(0, 10):
            time.sleep(.1)
            self.__update_position()
            incoord.append(self.transform.position)

        # get the average of these points
        start_pos = Vector(sum(c.x for c in incoord) / 10, sum(c.y for c in incoord) / 10)

        # we have our new rotation
        self.transform.rotation = self.get_angle(new_pos, start_pos)

        # print debug info
        if self.__debug:
            print("determined Rotation: ", self.transform.rotation)

    # this stops the hedge from recording positions
    def stop(self):
        self.__hedge.stop()

    # get the angle between two points and horizontal axis
    # a is the destination
    # b is the pivot point
    def get_angle(self, a, b):
        # get the angle between vector and horizontal axis
        dx = a.x - b.x
        dy = a.y - b.y
        rot_inRad = math.atan2(dy, dx)

        # convert to 0-360 degrees
        rotate = math.degrees(rot_inRad)
        if rotate < 0:
            rotate = 360 + rotate

        # print debug info
        if self.__debug:
            print("getangle returned: ", rotate)

        return rotate

    # travel to a given destination
    def goto_point(self, coord):

        # mark our new destination
        self.destination = coord

        # default local variables
        sleeptick = .100
        count = 0
        distance_threshold = self.threshold
        previous_locations = []

        self.cancel_early = False
        #self.__update_position()

        # if we are alread there, don't do anything
        if self.distance_to_destination() <= distance_threshold:
            self.destination = None
            self.get_reached_point_callback()
            self.gpg.set_speed(self.speed)
            return

        # prep to move
        self.turn_to_face(coord)
        time.sleep(sleeptick)
        dst = self.distance_to_destination()
        self.__determine_speed(dst)

        # time to move
        self.gpg.forward()
        time.sleep(sleeptick)

        # while we haven't found our destination
        while dst >= distance_threshold:

            # if we need to cancel early
            if self.cancel_early:
                self.gpg.stop()
                self.cancel_early = False
                self.gpg.set_speed(self.speed)
                return

            # update distance
            dst = self.distance_to_destination()
            self.get_position_callback()

            # check for obstacles
            self.check_for_obstacles()

            # slow down if needed
            self.__determine_speed(dst)
            time.sleep(sleeptick)

            # prep for rotation re-evaluation
            #self.__update_position()
            previous_locations.append(Vector(self.transform.position))


            # have we been going straight long enough to determine our own rotation?
            if len(previous_locations) == 4:

                # are we on an intercept trajectory?
                corrections = self.__plot_intersection()
                if corrections != 0:

                    # correct rotation
                    self.gpg.stop()
                    self.turn_to_face(coord)

                    # reset
                    self.__determine_speed(dst)
                    self.gpg.forward()
                    previous_locations = []
                
                    # get our rotation
                #self.transform.rotation = self.get_angle(self.transform.position, previous_locations[0])

                # we are going the wrong way and are lost
                elif self.__distance(previous_locations[0], self.destination) < self.distance_to_destination():

                    # reorient ourselves
                    self.gpg.stop()
                    #self.__update_position()
                    #self.determine_rotation()
                    self.turn_to_face(coord)

                    # incase we accidentally arrive
                    #if self.distance_to_destination() < distance_threshold:
                        #break

                    # reset
                    self.__determine_speed(dst)
                    self.gpg.forward()
                    previous_locations = []

                # everything is running fine, remove the oldest position
                else:
                    previous_locations.pop(0)

            # print debug info
            if self.__debug:
                print("distance", dst)
                print("current position", self.transform.position)
                print("current rotation", self.transform.rotation)
                print("destination", coord)
                print("************************")

        # We found the destination do final status update
        self.gpg.stop()
        #self.__update_position()
        self.get_position_callback()
        self.get_reached_point_callback()
        self.destination = None
        self.gpg.set_speed(self.speed)

    # gps is inaccurate at times, so if we are close we should slowdown to increase fidelity.
    def __determine_speed(self, dst):
        # if we are approaching the destination, slow down for more accuracy
        if dst <= self.threshold * 10:
            self.gpg.set_speed(self.speed / 2)
        else:
            self.gpg.set_speed(self.speed)

    # This method is used to calculate an intercept trajectory with the circle surrounding the destination point.
    # it returns 0 if the trajectory bisects at all (tangents are considered misses)
    # it then return -1 if the current angle is greater, or 1 if it is the opposite
    def __plot_intersection(self):
        direction = self.transform.position - self.destination
        vx = math.cos(self.transform.rotation)
        vy = math.sin(self.transform.rotation)
        a = pow(vx, 2) + pow(vy, 2)
        b = 2 * (vx * (direction.x) + vy * (direction.y))
        c = pow(direction.x, 2) + pow(direction.y, 2) - pow(self.threshold / 2, 2)
        det = pow(b, 2) - 4 * a * c

        # if it hits somehow
        if det < 0:
            return 0
        else:
            angle = self.get_angle(self.transform.position, self.destination)
            angle -= self.transform.rotation
            if angle < 0:
                return -1
            else:
                return 1

    # rotate left by degrees
    def __turn_left(self, degrees):

        if self.__debug:
            print("turning left.")
        self.gpg.rotate_left(abs(degrees))

    # rotate right by degrees
    def __turn_right(self, degrees):

        if self.__debug:
            print("turning right.")
        self.gpg.rotate_right(abs(degrees))

    # turn to a specific angle
    def turn_to_angle(self, angle):
        TOLERABLE_DEVIATION = 5

        # determine how much we need to rotate
        difference = abs(self.transform.rotation - angle)

        # show debug info
        if self.__debug:
            print("current rotation: ", self.transform.rotation)
            print("destination angle: ", angle)
            print("rotation needed: ", difference)

        # if we are outside of our margin for error
        if difference > TOLERABLE_DEVIATION:

            # slow down for higher fidelity
            self.gpg.set_speed(100)

            # if our current angle exceeds the angle we need
            if self.transform.rotation > angle:

                # debug info
                if self.__debug:
                    print("current angle is greater.")

                # ensure we aren't about to turn more than halfway around
                if difference <= 180:

                    # print debug info
                    if self.__debug:
                        print("difference is less than 180.")

                    self.__turn_right(difference)

                # we were, let's go the other way
                else:
                    # print debug info
                    if self.__debug:
                        print("difference is greater than 180.")

                    self.__turn_left(360 - difference)

            # the angle we need it greater than our current angle
            else:
                # print debug info
                if self.__debug:
                    print("destintation angle is greater.")

                # ensure we aren't about to turn more than halfway around
                if difference <= 180:

                    # print debug info
                    if self.__debug:
                        print("difference is less than 180.")

                    self.__turn_left(difference)

                # we were, let's go the other way
                else:

                    # print debug info
                    if self.__debug:
                        print("difference is greater than 180.")

                    self.__turn_right(360 - difference)

            # we have an accurate reading now.
            #self.transform.rotation = angle
            self.gpg.set_speed(self.speed)

    # rotate to face a specific point
    def turn_to_face(self, coord):
        angle = self.get_angle(coord, self.transform.position)
        self.turn_to_angle(angle)

    # checks for an obstacle and reports its position to a callback
    def check_for_obstacles(self):
        # check for obstacle
        self.position_update()
        distance = self.distance_sensor.read()
        # print("Distance Sensor Reading: {} cm ".format(distance))
        # if it was close enough
        if distance <= self.minimum_distance:
            # self.__hedge.print_position()
            offset = 0
            # get its position and send to callback
            distance += DISTANCE_FROM_CENTER
            distance = distance / 100
            x = (math.cos(math.radians(self.transform.rotation + offset)) * distance) + self.transform.position.x
            y = (math.sin(math.radians(self.transform.rotation + offset)) * distance) + self.transform.position.y

            pos = Vector(x, y)
            self.get_obstacle_callback(pos)

    # These might be depricated Gopigo3s travel quite straight and
    # forward seems to do something like this any way?
    def __balance(self):
        offset = 15
        imbalance = self.__find_imbalance()
        if self.__debug:
            print("imbalance: ", imbalance)
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
            print("encoder differences:", left_dif, right_dif)
        if left_dif + 5 < right_dif:
            return -1
        elif right_dif + 5 < left_dif:
            return 1
        else:
            return 0

    def __set_encoders(self):
        self.left_enc = enc_read(0)
        self.right_enc = enc_read(1)


# This is a little helper class that makes organizing position and rotation a little easier
# It is also is how Unity does which makes me feel a bit more comfortable
class Transform:
    def __init__(self, position=Vector(), rotation=0.0):
        self.position = position
        self.rotation = rotation
