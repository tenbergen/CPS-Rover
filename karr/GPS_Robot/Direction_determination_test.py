from gps import GPS
from gopigo import *
from vector import Vector
destination1 = Vector(2.27,.44)
destination2 = Vector(.36,.18)
destination3 = Vector(.77,1.33)
destination4 = Vector(1.64,.83)
coords = GPS(True,100)
coords.goto_point(destination1)
time.sleep(1)
dst1 = coords.distance(destination1,True)
coords.determine_rotation()
coords.goto_point(destination2)
time.sleep(1)
dst2 = coords.distance(destination2,True)
coords.determine_rotation()
coords.goto_point(destination3)
time.sleep(1)
dst3 = coords.distance(destination3,True)
coords.determine_rotation()
coords.goto_point(destination4)
time.sleep(1)
dst4 = coords.distance(destination4,True)
print "Distance 1: ",dst1
print "Distance 2: ",dst2
print "Distance 3: ",dst3
print "Distance 4: ",dst4
stop()
coords.stop()
