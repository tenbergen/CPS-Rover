from gps import GPS
from gopigo import *
set_speed(100)
coords = GPS(True)
print coords.rotation
turn_left(30)
coords.goto_point([1,1])
##turn_right_wait_for_completion(90)
##time.sleep(.1)
##turn_left_wait_for_completion(90)
##time.sleep(.1)
##turn_right_wait_for_completion(90)
##time.sleep(.1)
##turn_left_wait_for_completion(90)
##time.sleep(5)
stop()
coords.stop()
