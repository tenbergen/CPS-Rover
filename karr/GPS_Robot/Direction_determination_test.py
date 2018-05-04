from gps import GPS
from gopigo import *
from vector import Vector

destination = Vector(1.6,.87)
coords = GPS(True,75,True)
coords.goto_point(destination)
time.sleep(1)
print "Final Distance: ",coords.distance(destination)
stop()
coords.stop()
