from marvelmind import MarvelmindHedge
import time
import math
from vector import Vector
from threading import Thread

DISTANCE_FROM_CENTER = 0


# This class serves as a wrapper for marvelmind and gopigo movement.
# It uses them together to find its way to destinations
class GPS(Thread):

    # initialize the class
    def __init__(self, front_hedge, rear_hedge, gopigo, speed=300, q=None, debug_mode=False):
        Thread.__init__(self)

        # initialize the gopigo components
        self.gpg = gopigo
        self.distance_sensor = self.gpg.gpg.init_distance_sensor()

        # initialize gps "settings"
        self.__threshold = .06
        self.__command_queue = q
        self.__minimum_distance = 45
        self.__debug = debug_mode
        self.__cancel_early = False
        self.__thread_done = False

        # setup geometry information
        self.__transform = Transform()
        self.__rear_position = Vector()
        self.__speed = speed
        self.gpg.set_speed(speed)
        self.__destination = None

        # setup thread information
        self.path = []

        # start the hedge
        self.__front_hedge = front_hedge
        self.__rear_hedge = rear_hedge
        self.__hedge = MarvelmindHedge(tty="/dev/ttyACM0", recieveUltrasoundPositionCallback=self.position_update)
        self.__hedge.start()

        # setup callbacks
        self.__position_callback = None
        self.__obstacle_callback = None
        self.__reached_point_callback = None
        self.__no_obstacles_callback = None

        # set initial position
        if self.__debug:
            self.__hedge.print_position()

    # used if it is being run like a thread.  Use the queue sent in to add commands to the gps
    def run(self):

        # FOREVER
        while not self.__thread_done:

            # if we have a command
            if not self.__command_queue.empty():
                command = self.__command_queue.get()
                print("point received", command)

                # goto point
                self.__destination = command
                self.goto_point(self.__destination)

            # if we have nothing to do
            else:
                # update where we are and run callbacks
                self.get_position_callback()
                self.check_for_obstacles()
                time.sleep(.1)
        self.stop()

    # A callback sent to the hedge, it changes the position and rotation information every time it receives an update.
    def position_update(self):
        position = self.__hedge.position()
        if position[0] == self.__front_hedge:
            self.__transform.position = self.__convert_hedge_coords(position)
        else:
            self.__rear_position = self.__convert_hedge_coords(position)
        self.__transform.rotation = self.get_angle(self.__transform.position, self.__rear_position)

    # converts a hedge position into a 2D Vector in the transform
    @staticmethod
    def __convert_hedge_coords(position):
        return Vector(position[1], position[2])

    # the following methods set callbacks or get them.
    # If they are getting them, they will do nothing if None is used
    def set_position_callback(self, callback):
        self.__position_callback = callback

    def get_position_callback(self):
        if self.__position_callback is not None:
            self.__position_callback(self.__transform.position)

    def set_obstacle_callback(self, callback):
        self.__obstacle_callback = callback

    def get_obstacle_callback(self, pos):
        if self.__obstacle_callback is not None:
            self.__obstacle_callback(pos)

    def set_reached_point_callback(self, callback):
        self.__reached_point_callback = callback

    def get_reached_point_callback(self):
        if self.__reached_point_callback is not None:
            self.__reached_point_callback(self.__transform.position)
        print("destination reached!")

    def set_no_obstacle_callback(self, callback):
        self.__no_obstacles_callback = callback
        
    def get_no_obstacle_callback(self, positions):
        if self.__no_obstacles_callback is not None:
            self.__no_obstacles_callback(positions)

    def cancel_movement(self):
        self.__cancel_early = True

    def stop_thread(self):
        self.__thread_done = False

    # returns the current distance from the destination
    def distance(self, destination):
        return self.__distance(self.__transform.position, destination)

    # Gets the distance between start and end
    @staticmethod
    def __distance(a, b):
        return pow(pow(a.x - b.x, 2) + pow(a.y - b.y, 2), .5)

    def distance_to_destination(self):
        return self.distance(self.__destination)

    # get the current position of rover
    def get_position(self):
        return self.__transform.position

    # get the current rotation
    def get_rotation(self):
        return self.__transform.rotation

    # this stops the hedge from recording positions
    def stop(self):
        self.__hedge.stop()
        self.gpg.stop()
        self.__cancel_early = True
        self.__thread_done = True

    # get the angle between two points and horizontal axis
    # a is the destination
    # b is the pivot point
    def get_angle(self, a, b):
        # get the angle between vector and horizontal axis
        dx = a.x - b.x
        dy = a.y - b.y
        rot_in_rad = math.atan2(dy, dx)

        # convert to 0-360 degrees
        rotate = math.degrees(rot_in_rad)
        if rotate < 0:
            rotate = 360 + rotate

        # print debug info
        if self.__debug:
            print("get angle returned: ", rotate)

        return rotate

    # travel to a given destination
    def goto_point(self, coord):

        # mark our new destination
        self.__destination = coord

        # default local variables
        sleep_tick = .100
        distance_threshold = self.__threshold
        previous_locations = []

        self.__cancel_early = False

        # if we are already there, don't do anything
        if self.distance_to_destination() <= distance_threshold:
            self.__destination = None
            self.get_reached_point_callback()
            self.gpg.set_speed(self.__speed)
            return

        # prep to move
        self.turn_to_face(coord)
        time.sleep(sleep_tick)
        dst = self.distance_to_destination()
        self.__determine_speed(dst)

        # time to move
        self.gpg.forward()
        time.sleep(sleep_tick)

        # while we haven't found our destination
        while dst >= distance_threshold:

            # if we need to cancel early
            if self.__cancel_early:
                self.gpg.stop()
                self.__cancel_early = False
                self.gpg.set_speed(self.__speed)
                return

            # update distance
            dst = self.distance_to_destination()
            self.get_position_callback()

            # check for obstacles
            self.check_for_obstacles()

            # slow down if needed
            self.__determine_speed(dst)
            time.sleep(sleep_tick)

            # prep for rotation re-evaluation
            previous_locations.append(Vector(self.__transform.position))

            # have we been going straight long enough to determine our own rotation?
            if len(previous_locations) == 2:

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

                # we are going the wrong way and are lost
                elif self.__distance(previous_locations[0], self.__destination) < self.distance_to_destination():

                    # reorient ourselves
                    self.gpg.stop()
                    self.turn_to_face(coord)

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
                print("current position", self.__transform.position)
                print("current rotation", self.__transform.rotation)
                print("destination", coord)
                print("************************")

        # We found the destination do final status update
        self.gpg.stop()
        self.get_position_callback()
        self.get_reached_point_callback()
        self.__destination = None
        self.gpg.set_speed(self.__speed)

    # gps is inaccurate at times, so if we are close we should slowdown to increase fidelity.
    def __determine_speed(self, dst):
        # if we are approaching the destination, slow down for more accuracy
        if dst <= self.__threshold * 10:
            self.gpg.set_speed(self.__speed / 2)
        else:
            self.gpg.set_speed(self.__speed)

    # This method is used to calculate an intercept trajectory with the circle surrounding the destination point.
    # it returns 0 if the trajectory bisects at all (tangents are considered misses)
    # it then return -1 if the current angle is greater, or 1 if it is the opposite
    def __plot_intersection(self):
        direction = self.__transform.position - self.__destination
        vx = math.cos(self.__transform.rotation)
        vy = math.sin(self.__transform.rotation)
        a = pow(vx, 2) + pow(vy, 2)
        b = 2 * (vx * direction.x + vy * direction.y)
        c = pow(direction.x, 2) + pow(direction.y, 2) - pow(self.__threshold / 2, 2)
        det = pow(b, 2) - 4 * a * c

        # if it hits somehow
        if det < 0:
            return 0
        else:
            angle = self.get_angle(self.__transform.position, self.__destination)
            angle -= self.__transform.rotation
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
        tolerable_deviation = 1

        # determine how much we need to rotate
        difference = abs(self.__transform.rotation - angle)

        # show debug info
        if self.__debug:
            print("current rotation: ", self.__transform.rotation)
            print("destination angle: ", angle)
            print("rotation needed: ", difference)

        # if we are outside of our margin for error
        if difference > tolerable_deviation:

            # slow down for higher fidelity
            self.gpg.set_speed(100)

            # if our current angle exceeds the angle we need
            if self.__transform.rotation > angle:

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
                    print("destination angle is greater.")

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
            self.gpg.set_speed(self.__speed)

    # rotate to face a specific point
    def turn_to_face(self, coord):
        angle = self.get_angle(coord, self.__transform.position)
        self.turn_to_angle(angle)

    # checks for an obstacle and reports its position to a callback
    def check_for_obstacles(self):
        # check for obstacle
        self.position_update()
        distance = self.distance_sensor.read()

        # if it was close enough
        if distance <= self.__minimum_distance:
            # get its position and send to callback
            distance += DISTANCE_FROM_CENTER
            distance = distance / 100
            x = (math.cos(math.radians(self.__transform.rotation)) * distance) + self.__transform.position.x
            y = (math.sin(math.radians(self.__transform.rotation)) * distance) + self.__transform.position.y

            pos = Vector(x, y)
            self.get_obstacle_callback(pos)
        else:
            distance = self.__minimum_distance

            # get its position and send to callback
            distance += DISTANCE_FROM_CENTER
            distance = distance / 100
            x = (math.cos(math.radians(self.__transform.rotation)) * distance) + self.__transform.position.x
            y = (math.sin(math.radians(self.__transform.rotation)) * distance) + self.__transform.position.y

            pos = Vector(x, y)
            self.get_no_obstacle_callback(pos)


# This is a little helper class that makes organizing position and rotation a little easier
# It is also is how Unity does which makes me feel a bit more comfortable
class Transform:
    def __init__(self, position=Vector(), rotation=0.0):
        self.position = position
        self.rotation = rotation
