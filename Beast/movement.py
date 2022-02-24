from time import sleep
from easygopigo3 import EasyGoPiGo3
from di_sensors.easy_distance_sensor import EasyDistanceSensor
from infoupdate import InfoUpdate
import threading
import random
import math

gpg = EasyGoPiGo3()
distance_sensor = EasyDistanceSensor()
iu = InfoUpdate()
INT_MAX = 10000
start = True

def onSegment(p:tuple, q:tuple, r:tuple) -> bool:
    if ((q[0] <= max(p[0], r[0])) &
        (q[0] >= min(p[0], r[0])) &
        (q[1] <= max(p[1], r[1])) &
        (q[1] >= min(p[1], r[1]))):
        return True
    else:
        return False
    
def orientation(p:tuple, q:tuple, r:tuple) -> int:
    val = (((q[1]-p[1])*(r[0]-q[0]))-((q[0]-p[0])*(r[1]-q[1])))
    if val == 0:
        return 0
    elif val > 0:
        return 1
    else:
        return 2
    
def doIntersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)
    
    if (o1 != o2) and (o3 != o4):
        return True
    elif (o1 == 0) and (onSegment(p1, p2, q1)):
        return True
    elif (o2 == 0) and (onSegment(p1, q2, q1)):
        return True  
    elif (o3 == 0) and (onSegment(p2, p1, q2)):
        return True
    elif (o4 == 0) and (onSegment(p2, q1, q2)):
        return True
    else:
        return False

def is_inside_polygon(points:list, p:tuple) -> bool:
    n = len(points)
    #this condition checks of the shape is a polygon. A polygon has to have at least 3 vertices
    if n < 3:
        return False
    
    extreme = (INT_MAX, p[1])
    count = i = 0
    
    while True:
        next = (i+1) % n
        if (doIntersect(points[i], points[next], p, extreme)):
            if orientation(points[i], p, points[next]) == 0:
                return onSegment(points[i], p, points[next])
            count += 1
        i = next
        
        if (i == 0):
            break
        
    return ((count % 2) == 1)

def not_in_polygon(s1, s2, boundaries):
    iu.onEdge = True
    gpg.stop()
    sleep(1)
    gpg.turn_degrees(180, blocking = False)
    sleep(4)
    gpg.stop()
    while not is_inside_polygon(points = s1, p = (position[1], position[2])):
        distance = distance_sensor.read()
        collisionCond2 = possible_collision2(boundaries)
        if possible_collision():
            collision_action_when_not_in_polygon(s2, boundaries)
        elif collisionCond2:
            collision_action2(collisionCond2, s2, boundaries)
        elif (distance < 15):
            collision_action3()
        elif start == False:
            gpg.stop()
            break
        else:
            gpg.forward()
    iu.onEdge = False
        
def possible_collision():
    xDis = abs(otherPos[1] - position[1])
    yDis = abs(otherPos[2] - position[2])
    box_len = 0.6                              
    if (xDis < box_len) and (yDis < box_len):
        return True
    else:
        return False

# check for possible collision with stationary beacons
def possible_collision2(boundaries):
    stationaryBs = boundaries[2]
    box_len = 0.4                     
    for sbpos in stationaryBs:
        b = sbpos
        x = b[0]
        y = b[1]
        xDis = abs(position[1] - x)
        yDis = abs(position[2] - y)
        if (xDis < box_len) and (yDis < box_len):
            return b
    return False

def collision_action(s2, boundaries):
    iu.onEdge = False
    xDis = abs(otherPos[1] - position[1])
    yDis = abs(otherPos[2] - position[2])
    box_len = 0.6                              
    if (xDis < box_len) and (yDis < box_len):
        gpg.stop()
        sleep(3)
        r1 = random.randint(110,180)
        r2 = random.randint(-180,-110)
        r = random.choice([r1, r2])
        if (otherPos[1] > position[1]) and (otherPos[2] > position[2]):
            if (position[4] >= 2250) or (position[4] <= 450):
                gpg.turn_degrees(r, blocking = False)
                sleep(4)
                gpg.stop()

        elif (otherPos[1] < position[1]) and (otherPos[2] > position[2]):
            if (position[4] <= 1350) or (position[4] >= 3150):
                gpg.turn_degrees(r, blocking = False)
                sleep(4)
                gpg.stop()

        elif (otherPos[1] < position[1]) and (otherPos[2] < position[2]):
            if (position[4] >= 450) and (position[4] <= 2250):
                gpg.turn_degrees(r, blocking = False)
                sleep(4)
                gpg.stop()
                
        else:
            if (position[4] >= 1350) and (position[4] <= 3150):
                gpg.turn_degrees(r, blocking = False)
                sleep(4)
                gpg.stop()

        while (xDis < box_len) and (yDis < box_len):
            xDis = abs(otherPos[1] - position[1])
            yDis = abs(otherPos[2] - position[2])
            distance = distance_sensor.read()
            collisionCond2 = possible_collision2(boundaries)
            if not is_inside_polygon(points = s2, p = (position[1], position[2])):
                gpg.stop()
                iu.onEdge = True
            elif collisionCond2:
                collision_action2(collisionCond2, s2, boundaries)
            elif (distance < 15):
                collision_action3()
            elif start == False:
                gpg.stop()
                break
            else:
                gpg.forward()
    else:
        gpg.forward()
        
# collision action that handles possible collsion with stationary beacons
def collision_action2(SBpos, s2, boundaries):
    iu.onEdge = False
    SBposition = SBpos
    gpg.stop()
    sleep(3)
    r1 = random.randint(110,180)
    r2 = random.randint(-180,-110)
    r = random.choice([r1, r2])
    if (SBposition[0] > position[1]) and (SBposition[1] > position[2]):
        if (position[4] >= 2250) or (position[4] <= 450):
            gpg.turn_degrees(r, blocking = False)
            sleep(4)
            gpg.stop()

    elif (SBposition[0] < position[1]) and (SBposition[1] > position[2]):
        if (position[4] <= 1350) or (position[4] >= 3150):
            gpg.turn_degrees(r, blocking = False)
            sleep(4)
            gpg.stop()

    elif (SBposition[0] < position[1]) and (SBposition[1] < position[2]):
        if (position[4] >= 450) and (position[4] <= 2250):
            gpg.turn_degrees(r, blocking = False)
            sleep(4)
            gpg.stop()
                
    else:
        if (position[4] >= 1350) and (position[4] <= 3150):
            gpg.turn_degrees(r, blocking = False)
            sleep(4)
            gpg.stop()
    
    xDis = abs(position[1] - SBposition[0])
    yDis = abs(position[2] - SBposition[1])
    box_len = 0.4                           
    
    while (xDis < box_len) and (yDis < box_len):
        xDis = abs(position[1] - SBposition[0])
        yDis = abs(position[2] - SBposition[1])
        distance = distance_sensor.read()
        if possible_collision():
            collision_action(s2, boundaries)
        elif not is_inside_polygon(points = s2, p = (position[1], position[2])):
            gpg.stop()
            iu.onEdge = True
        elif (distance < 15):
            collision_action3()
        elif start == False:
            gpg.stop()
            break
        else:
            gpg.forward()

# collision detection from sensor
def collision_action3():
    iu.onEdge = False
    gpg.stop()
    sleep(1)
    r1 = random.randint(90,135)
    r2 = random.randint(-135,-90)
    r = random.choice([r1, r2])
    gpg.turn_degrees(r, blocking = False)
    sleep(4)
    gpg.stop()

def collision_action_when_not_in_polygon(s2, boundaries):
    xDis = abs(otherPos[1] - position[1])
    yDis = abs(otherPos[2] - position[2])
    box_len = 0.6                          
    cantMove = False
    if (otherPos[1] > position[1]) and (otherPos[2] > position[2]):
        if (position[4] >= 2250) or (position[4] <= 450):
            gpg.stop()
            iu.onEdge = True
            cantMove = True

    elif (otherPos[1] < position[1]) and (otherPos[2] > position[2]):
        if (position[4] <= 1350) or (position[4] >= 3150):
            gpg.stop()
            iu.onEdge = True
            cantMove = True

    elif (otherPos[1] < position[1]) and (otherPos[2] < position[2]):
        if (position[4] >= 450) and (position[4] <= 2250):
            gpg.stop()
            iu.onEdge = True
            cantMove = True
            
    else:
        if (position[4] >= 1350) and (position[4] <= 3150):
            gpg.stop()
            iu.onEdge = True
            cantMove = True
    
    while (xDis < box_len) and (yDis < box_len):
        xDis = abs(otherPos[1] - position[1])
        yDis = abs(otherPos[2] - position[2])
        distance = distance_sensor.read()
        collisionCond2 = possible_collision2(boundaries)
        if cantMove == True:
            gpg.stop()
        elif collisionCond2:
            collision_action2(collisionCond2, s2, boundaries)
        elif not is_inside_polygon(points = s2, p = (position[1], position[2])):
            gpg.stop()
            iu.onEdge = True
        elif (distance < 15):
            collision_action3()
        elif start == False:
            gpg.stop()
            break
        else:
            gpg.forward()
    
    
def positionupdate():
    global position
    global otherPos
    while start:
        position = iu.getUpdatedPosition()
        temp = iu.getOtherUpdatedPos()
        if temp is not None:
            otherPos = temp


def calculate_point(b1, b2, b3, d1, d2, d3):
    a = b1[0]**2 + b1[1]**2 - d1**2
    b = b2[0]**2 + b2[1]**2 - d2**2
    c = b3[0]**2 + b3[1]**2 - d3**2
    x21 = b2[0] - b1[0]
    x13 = b1[0] - b3[0]
    x32 = b3[0] - b2[0]
    y21 = b2[1] - b1[1]
    y13 = b1[1] - b3[1]
    y32 = b3[1] - b2[1]
    
    x = (a * y32 + b * y13 + c * y21)/(2.0*(b1[0]*y32 + b2[0]*y13 + b3[0]*y21))
    y = (a * x32 + b * x13 + c * x21)/(2.0*(b1[1]*x32 + b2[1]*x13 + b3[1]*x21))
    
    dilationFactor = 1.2                             
    reductionFactor = 0.8                           
    point = (x, y)
    outerPoint = (x*dilationFactor, y*dilationFactor)
    innerPoint = (x*reductionFactor, y*reductionFactor)
    return [point, outerPoint, innerPoint]

def calculate_pair_beacon_pos(pos):
    p = pos
    d = p[4]/10
    disBtwPairB = 0.095
    if (d >= 0 and d < 90):
        xdif = disBtwPairB * math.sin(math.radians(d))
        ydif = disBtwPairB * math.cos(math.radians(d))
        x = p[1] + xdif
        y = p[2] - ydif
        return (x,y)
    elif (d >= 90 and d < 180):
        d = d - 90
        xdif = disBtwPairB * math.cos(math.radians(d))
        ydif = disBtwPairB * math.sin(math.radians(d))
        x = p[1] + xdif
        y = p[2] + ydif
        return (x,y)
    elif (d >= 180 and d < 270):
        d = d - 180
        xdif = disBtwPairB * math.sin(math.radians(d))
        ydif = disBtwPairB * math.cos(math.radians(d))
        x = p[1] - xdif
        y = p[2] + ydif
        return (x,y)
    else:
        d = d - 270
        xdif = disBtwPairB * math.cos(math.radians(d))
        ydif = disBtwPairB * math.sin(math.radians(d))
        x = p[1] - xdif
        y = p[2] - ydif
        return (x,y)
    
def centroid(vertices):
    xList = [vertex [0] for vertex in vertices]
    yList = [vertex [1] for vertex in vertices]
    l = len(vertices)
    x = sum(xList)/l
    y = sum(yList)/l
    return (x, y)
    
    
def getSBeaconPos():
    p = position
    o = otherPos
    b5 = (p[1],p[2])
    b6 = calculate_pair_beacon_pos(p)
    b10 = (o[1],o[2])
    b5Dis = None
    b6Dis = None
    b10Dis = None
    arrayOfSB = [5,6,10]
    midBound = []
    outerBound = []
    innerBound = []
    while len(arrayOfSB) > 0:
        dis = iu.getDistances()
        if dis[0] == 5 and (5 in arrayOfSB):
            b5Dis = dis
            arrayOfSB.remove(5)
        elif dis[0] == 6 and (6 in arrayOfSB):
            b6Dis = dis
            arrayOfSB.remove(6)
        elif dis[0] == 10 and (10 in arrayOfSB):
            b10Dis = dis
            arrayOfSB.remove(10)

    i = 2
    while i < len(b5Dis):
        p = calculate_point(b5, b6, b10, b5Dis[i], b6Dis[i], b10Dis[i])
        midBound.append(p[0])
        outerBound.append(p[1])
        innerBound.append(p[2])
        i += 2
    
    MBCenteroid = centroid(midBound)
    OBCenteroid = centroid(outerBound)
    IBCenteroid = centroid(innerBound)
    
    MBandOBxDif = OBCenteroid[0] - MBCenteroid[0]
    MBandOByDif = OBCenteroid[1] - MBCenteroid[1]
    IBandMBxDif = MBCenteroid[0] - IBCenteroid[0]
    IBandMByDif = MBCenteroid[1] - IBCenteroid[1]
    
    OB = []
    IB = []
    for point in outerBound:
        x = point[0] - MBandOBxDif
        y = point[1] - MBandOByDif
        OB.append((x,y))
        
    for point in innerBound:
        x = point[0] + IBandMBxDif
        y = point[1] + IBandMByDif
        IB.append((x,y))
    
    return [OB, IB, midBound]

def movement(boundaries):
    gpg.set_speed(random.randint(100,150))
    while start:
        s1 = boundaries[1]
        s2 = boundaries[0]
        collisionCond2 = possible_collision2(boundaries)
        distance = distance_sensor.read()
        if possible_collision():
            collision_action(s2, boundaries)
        elif collisionCond2:
            collision_action2(collisionCond2, s2, boundaries)
        elif (distance < 15):
            collision_action3()
        elif not is_inside_polygon(points = s2, p = (position[1], position[2])):
            not_in_polygon(s1, s2, boundaries)
        elif is_inside_polygon(points = s2, p = (position[1], position[2])) and (not is_inside_polygon(points = s1, p = (position[1], position[2]))):
            iu.onEdge = True
            gpg.stop()
            sleep(1)
            r1 = random.randint(110,180)
            r2 = random.randint(-180,-110)
            r = random.choice([r1, r2])
            gpg.turn_degrees(r, blocking = False)
            sleep(4)
            gpg.stop()
            while not is_inside_polygon(points = s1, p = (position[1], position[2])) and (not is_inside_polygon(points = s1, p = (position[1], position[2]))):
                collisionCond2 = possible_collision2(boundaries)
                distance = distance_sensor.read()
                if possible_collision():
                    collision_action_when_not_in_polygon(s2, boundaries)
                elif collisionCond2:
                    collision_action2(collisionCond2, s2, boundaries)
                elif (distance < 15):
                    collision_action3()
                elif not is_inside_polygon(points = s2, p = (position[1], position[2])):
                    not_in_polygon(s1, s2, boundaries)
                elif start == False:
                    gpg.stop()
                    break
                else:
                    gpg.forward()
            iu.onEdge = False
        else:
            gpg.forward()

def main():
    sleep(2)
    boundaries = getSBeaconPos()
    print(boundaries[2])
    userInput = input("Enter 1 to start: ")
    while userInput != "1":
        userInput = input("Enter 1 to start: ")
    else:
        t3 = threading.Thread(target = stop)
        t3.start()
        movement(boundaries)
        t3.join()
        
def stop():
    userInput = input("Enter 2 to stop: ")
    while userInput != "2":
        userInput = input("Enter 2 to stop: ")
    else:
        global start
        start = False
        

t1 = threading.Thread(target = positionupdate)
t2 = threading.Thread(target = main)
t1.start()
t2.start()
t1.join()
t2.join()
gpg.stop()
print("stopped")
    