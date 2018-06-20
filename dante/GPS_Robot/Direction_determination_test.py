from gps import GPS
from advancedgopigo3 import *
from vector import Vector
destination1 = Vector(1.6,1.32)
destination2 = Vector(1.85,3.2)
destination3 = Vector(.7,2.9)
destination4 = Vector(1.19,1.8)
gpg = AdvancedGoPiGo3(25)
coords = GPS(False,gpg,debug_mode=True)
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
gpg.stop()
coords.stop()
