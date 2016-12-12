from gopigo import *

def turn_around():
          enc_tgt(1,1,5)
          fwd()
          time.sleep(1)
          set_speed(100)
          enc_tgt(1,1,17)
          right_rot()
          
print "battery voltage"
print volt()
turn_around()
