from gopigo import *
from time import sleep
from math import sqrt, degrees, atan2
from graphing import *
import os
from gps import *
from threading import Thread
from collections import deque

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
This program will allow Karr to run autonomously.
Karr will follow a set of GPS coordinates, moving from
  coordinate to coordinate until it reaches the last one.
Karr can follow its predetermined path or return home to
  the controller.
Karr will stop when it reaches the last coordinate.

Note: Karr's left wheel is stronger than the right wheel by about 2%.
To compensate, add 2% wheel speed to the right wheel.

This table represents the measured time it takes Karr to make a full rotation.
Each column is represented as Direction/Wheel Affected.
Direction: the direction that Karr is turning
       L - Left turn
       R - Right turn
       S - Straight
Wheel Affected - wheel speed
       L - left wheel
       R - right wheel
   L/L     L/R     R/L     R/R     S/L     S/R     Left Rotation Time      Right Rotation Time
   90      112     110     92      100     102           33.6                   57.2
   180     224     220     184     200     204           10                     14.9
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

#measured time for a full 360 degree turn
right_turn = 57.2
left_turn = 33.6

#turns on GPS module
#os.system("sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock")

gpsd = gps(mode=WATCH_ENABLE)
global coordRunning
coordRunning = False
global destination
destination = None
global curr_dir
curr_dir = None
global curr_pos
curr_pos = [0,0]
global last_pos
last_pos = [0,0]

#General Set of Points taken at random
#Points = ["43.4551583 -76.537198",
#          "43.454563021154755 -76.53915904462337",
#          "43.4552055064844 -76.53920212",
#          "43.45526629843700 -76.53871983289800",
#          "43.45526629843780 -76.53871983289750"]

#Points taken starting on the road in between Shineman and Marano, traveling north on the road, then turning left directly before the parking lot
#Points = ["43.45438488184355 -76.53919145443069",
#          "43.45488117153791 -76.53921827652084",
#          "43.45529394663544 -76.53924241640198",
#          "43.45530952299904 -76.53958573915588",
#          "43.45526668798945 -76.53989151098358"]

#Points taken on the 4th floor Shineman starting in front of Doug Lea's office, turning at the end of the hall, then ending at the end of that hall
#Points = ["43.45516 -76.53821",
#          "43.45501 -76.53821",
#          "43.45487 -76.53821",
#          "43.45463 -76.53866",
#          "43.45516 -76.53821"]

#Points taken starting in between Shineman and Wilbur in the hallway with 2 double doors and many windows while traveling towards Wilbur
#   then turning on the end of the hallway and ending in the middle of the big open area in Wilbur
Points = ["43.455106 -76.537838",
          "43.45516 -76.5376",
          "43.45514 -76.53744",
          "43.45512 -76.53732",
          "43.45495 -76.53726"]

global Map
#Map connected in a straight line
Map = {Points[0]: {Points[1]: 1},
       Points[1]: {Points[0]: 1, Points[2]: 1},
        Points[2]: {Points[1]: 1, Points[3]: 1},
        Points[3]: {Points[2]: 1, Points[4]: 1},
        Points[4]: {Points[3]: 1}}

#General Map of Points connected at random
#Map = {Points[0]: {Points[1]: 1, Points[3]: 1},
#       Points[1]: {Points[0]: 1, Points[2]: 1, Points[4]: 1},
#        Points[2]: {Points[1]: 1, Points[3]: 1},
#        Points[3]: {Points[0]: 1, Points[2]: 1},
#        Points[4]: {Points[1]: 1}}


class GPSCoord(Thread):
    #stores GPS coordinates every 0.2 seconds
    #calculates average of last 5 GPS cooridinates
    #will not use coordinates with less than 5 decimal places
    
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global gpsd
        global coordRunning
        global coord_queue
        global curr_pos
        global last_pos
        coord_queue = deque(maxlen=5)
        while coordRunning:
            coord = [gpsd.fix.latitude, gpsd.fix.longitude]
            if decimal_length(coord[0]) > 4 and decimal_length(coord[1]) > 4:
                coord_queue.append(coord)
                last_pos = curr_pos
                curr_pos = average_coordinates(list(coord_queue))
            else:
                if coord_queue.size() > 0:
                    coord_queue.pop()
            sleep(0.2)

class GPSBuffer(Thread):
    #clears the GPS reading buffer
    
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global gpsd
        global coordRunning
        while coordRunning:
            gpsd.next()

class GPS(Thread):
    #checks distance to target coordinate every 3 seconds
    #moves to next coordinate when within 30ft
    #stops when last destination reached
    
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global gpsd
        global coordRunning
        global coord_queue
        sleep(1)
        while coordRunning:
            if correct_distance():
                return
            print ""
            sleep(3)

class Turning(Thread):
    #turns based on difference in bearing
    #checks every second
    
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global coordRunning
        global curr_pos
        while coordRunning:
            print "Latitude:", curr_pos[0]
            print "Longitude:", curr_pos[1]
            correct_angle()

#returns the number of decimals in a number
def decimal_length(num):
    num = abs(num)
    return len(str(num - int(num))) - 1

#calculates distance to target coordinate
#moves to next coordinate if within 30 feet
#Karr is stopped if last coordinate is reached
def correct_distance():
    global destination
    global Path
    global coordRunning
    global curr_pos
    target_dis = convert_gps_to_feet(distance(curr_pos[0], curr_pos[1], destination[0], destination[1]))
    print "Current Target:", destination
    print "Target Distance:", target_dis, "feet"
    if target_dis < 30:
        if len(Path) > 1:
            destination = splitCoord(Path[1])
            print "Moving to next Coordinate"
            Path = Path[1:]
        else:
            coordRunning = False
            print "Final Destination Reached"
            stop()
            return True
    return False
    
#calculates bearing from last position to current position
#turns accordingly
#checks every 1 second
def correct_angle():
    global curr_pos
    global last_pos
    curr_dir = bearing(last_pos, curr_pos)
    target_dir = bearing(curr_pos, destination)
    print "Target Direction:", target_dir
    print "Current Direction", curr_dir
    if curr_dir != dir:
        angle = (target_dir - curr_dir + 360) % 360
        print "Angle: ", angle
        if angle > 180:  #left turn
            set_left_speed(90)
            set_right_speed(112)
            time = time_left_turn(360-angle)
            print "Moving to the left at time:", time
        else:             #right turn
            set_left_speed(110)
            set_right_speed(92)
            time = time_right_turn(angle)
            print "Moving to the right at time:", time
        fwd()
        print ""
        if time >= 1:
            sleep(1)
        else:
            sleep(time)
            set_left_speed(100)
            set_right_speed(102)
            fwd()
            sleep(1 - time)

#returns average coordinate of all measured coordinates
#max of 5 coordinates are stored at a time
def average_coordinates(coords):
    count = [0,0]
    for x in coords:
        count[0] += x[0]
        count[1] += x[1]
    return [count[0] / len(coords), count[1] / len(coords)]

#sets up shortest path and sets next destination
def set_up_path(Map, start, end):
    global Path
    Map = set_distance(Map)
    Path = shortestPath(Map, Points[start], Points[end])
    global destination
    destination = splitCoord(Path[0])

#converts coordinate from a string to a tuple of floats
def splitCoord(coord):
    return [float(coord.split()[0]), float(coord.split()[1])]


#Bearing calculation taken from John Machin
#stackoverflow.com/questions/5058617/bearing-between-teo-points
#Bearing is calculated from the perspective of staring point towards end point
#in a 0 - 360 degree range starting from the positive y axis (north)
#and turning clockwise.
def bearing(end, start):
    angle = degrees(atan2(start[1] - end[1], start[0] - end[0]))
    return (angle + 360) % 360

#Latitude is measured as 364,000 feet per degree.
#Longitude is measured as 288,200 feet per degree.
#The 1.2630118 converts longitude to working latitude.
#This information is taken from the USGS website.
def distance(x1, y1, x2, y2):
    return sqrt((x2-x1)**2 + ((y2-y1) * 1.2630118)**2)

#converts GPS degrees to feet
def convert_gps_to_feet(distance):
    return int(distance * 364000)

#initializes map to store distance between coordinates
def set_distance(Map):
    for x in Map:
        for y in Map[x]:
            strX = x.split(" ")
            strY = y.split(" ")
            Map[x][y] = distance(float(strX[0]), float(strX[1]), float(strY[0]), float(strY[1]))
    return Map

#calculates total distance to final destination
def distance_traveled(Map, path):
    total = 0
    for i in range(0, len(path) - 1):
        total = total + Map[path[i]][path[i+1]]
    return total

#calculates time tatken to make a right turn
def time_right_turn(angle):
    return (angle / 360) * right_turn

#calculates time tatken to make a left turn
def time_left_turn(angle):
    return (angle / 360) * left_turn

#follows the complete path of coordinates until final destination is reached
def followCoords():
    print "running at", volt()
    set_up_path(Map, 0, 4)
    set_left_speed(100)
    set_right_speed(102)
    fwd()
    
    global coordRunning
    coordRunning = True
    gps_buffer = GPSBuffer()
    gps_coordinates = GPSCoord()
    new_gps = GPS()
    turn = Turning()
    gps_buffer.start()
    gps_coordinates.start()
    new_gps.start()
    turn.start()
    while coordRunning:
        sleep(2)
    coordRunning = False
    gps_buffer.join()
    gps_coordinates.join()
    new_gps.join()
    turn.join()
    stop()

#travels to the home coordinate
#home coordinate is taken when controller is connected
def goHome(coord):
    print "Attempting to go home to coordinate"
    print coord[0]
    print coord[1]
    global destination
    global coordRunning
    global Path
    destination = coord
    Path = []
    stop()
    
    coordRunning = True
    gps_buffer = GPSBuffer()
    gps_coordinates = GPSCoord()
    new_gps = GPS()
    turn = Turning()
    gps_buffer.start()
    gps_coordinates.start()
    new_gps.start()
    turn.start()
    gps_coordinates = GPSCoord()
    new_gps = GPS()
    gps_coordinates.start()
    new_gps.start()
    while coordRunning:
        sleep(5)
        
    coordRunning = False
    gps_buffer.join()
    gps_coordinates.join()
    new_gps.join()
    turn.join()
    stop()
    
#uncomment to allow Karr to run without the controller
#followCoords()
