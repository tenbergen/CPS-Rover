from gps import GPS
from gopigo import *
set_speed(50)
coords = GPS(True)
#print coords.rotation
coords.turn_to_angle(90)
coords.stop()
