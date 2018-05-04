from gps import GPS
from gopigo import *
set_speed(75)
coords = GPS(True,True)
#print coords.rotation
coords.turn_to_angle(180)
time.sleep(10)
coords.turn_to_angle(90)
time.sleep(10)
coords.turn_to_angle(270)
time.sleep(10)
coords.turn_to_angle(0)
time.sleep(10)
coords.stop()
