from gopigo import *
from time import sleep
from math import sqrt, degrees, atan2
from graphing import *
import os
from gps import *
from threading import Thread

#For right turns, set left wheel to 220, right wheel to 184
#and the time per full 360 degree rotation is 14.9 sec
#Voltage was measured at 10V
#so sleep(14.9) for a full rotation
#After doing a full rotation, Karr ended 5 in to the right from where it started.

#For left turns, set left wheel to 180, right wheel to 224.
#The time per full rotation is 10 sec.
#Voltage was measured at 10V.
#so sleep(10) for a full rotation
#After doing a full rotation, Karr ended about where it started.

#The right turn diameter is about 20 inches more than the left turn diameter.

right_turn = 14.9
left_turn = 10
#os.system("sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock")
global gpsd
gpsd = None
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

#General Set of POints taken at random
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
Points = ["43.45516 -76.53821",
          "43.45501 -76.53821",
          "43.45487 -76.53821",
          "43.45463 -76.53866",
          "43.45516 -76.53821"]

#Points taken starting in between Shineman and Wilbur in the hallway with 2 double doors and many windows while traveling towards Wilbur
#   then turning on the end of the hallway and ending in the middle of the big open area in Wilbur
#Points = ["43.45506 -76.53798",
#          "43.45516 -76.5376",
#          "43.45514 -76.53744",
#          "43.45512 -76.53732",
#          "43.45495 -76.53726"]

global Map
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
#"43.454703 -76.539181"

class GPSCoord(Thread):
    def __init__(self):
        Thread.__init__(self)
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)

    def run(self):
        global gpsd
        global coordRunning
        while coordRunning:
            gpsd.next()

class GPS(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global gpsd
        global coordRunning
        global curr_pos
        global last_pos
        while coordRunning:
            last_pos = curr_pos
            curr_pos = (gpsd.fix.latitude, gpsd.fix.longitude)
            print "Latitude:", curr_pos[0]
            print "Longitude:", curr_pos[1]
            correct_distance(curr_pos)
            correct_angle(last_pos, curr_pos)
            print ""
            sleep(5)

def correct_distance(curr_pos):
    global destination
    global Path
    global coordRunning
    target_dis = distance(curr_pos[0], curr_pos[1], destination[0], destination[1])
    print "Current Target:", destination
    print "Target Distance:", target_dis
    if target_dis < 0.0000275:
        if len(Path) > 1:
            destination = splitCoord(Path[1])
            print "Moving to next Coordinate"
            Path = Path[1:]
        else:
            coordRunning = False
            print "Final Destination Reached"
            stop()
    

def correct_angle(last_pos, curr_pos):
    curr_dir = bearing(last_pos, curr_pos)
    target_dir = bearing(curr_pos, destination)
    print "Target Direction:", target_dir
    print "Current Direction", curr_dir
    if curr_dir != dir:
        angle = (target_dir - curr_dir + 360) % 360
        print "Angle: ", angle
        if angle > 180:  #left turn
            set_left_speed(180)
            set_right_speed(224)
            time = time_left_turn(360-angle)
            print "Moving to the left at time:", time
        else:             #right turn
            set_left_speed(220)
            set_right_speed(184)
            time = time_right_turn(angle)
            print "Moving to the right at time:", time
        fwd()
        sleep(time)
        set_left_speed(200)
        set_right_speed(204)
        fwd()


def set_up_path(Map):
    global Path
    Map = set_distance(Map)
    Path = shortestPath(Map, Points[0], Points[3])
    global destination
    destination = splitCoord(Path[0])

def splitCoord(coord):
    return [float(coord.split()[0]), float(coord.split()[1])]


#Bearing calculation taken from John Machin
#stackoverflow.com/questions/5058617/bearing-between-teo-points
#Bearing is calculated from the perspective of point start towards end
#in a 0 - 360 degree range starting from the positive y axis (north)
#and turning clockwise.
def bearing(end, start):
    angle = degrees(atan2(start[1] - end[1], start[0] - end[0]))
    return (angle + 360) % 360

def distance(x1, y1, x2, y2):
    return sqrt((x2-x1)**2 + (y2-y2)**2)

def set_distance(Map):
    for x in Map:
        for y in Map[x]:
            strX = x.split(" ")
            strY = y.split(" ")
            Map[x][y] = distance(float(strX[0]), float(strX[1]), float(strY[0]), float(strY[1]))
    return Map

def distance_traveled(Map, path):
    total = 0
    for i in range(0, len(path) - 1):
        total = total + Map[path[i]][path[i+1]]
    return total

def time_right_turn(angle):
    return (angle / 360) * right_turn

def time_left_turn(angle):
    return (angle / 360) * left_turn

def followCoords():
    print "running at", volt()
    set_up_path(Map)
    set_left_speed(200)
    set_right_speed(204)
    fwd()
    
    global coordRunning
    coordRunning = True
    gps_coordinates = GPSCoord()
    new_gps = GPS()
    gps_coordinates.start()
    new_gps.start()
    while coordRunning:
        sleep(5)
    coordRunning = False
    gps_coordinates.join()
    new_gps.join()
    stop()

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
    gps_coordinates = GPSCoord()
    new_gps = GPS()
    gps_coordinates.start()
    new_gps.start()
    while coordRunning:
        sleep(5)
    coordRunning = False
    gps_coordinates.join()
    new_gps.join()
    

#followCoords()
