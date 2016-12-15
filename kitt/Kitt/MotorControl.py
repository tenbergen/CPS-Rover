import io
from gopigo import *
import time

class MotorControl:
    def __init__(self):
        enable_encoders()

    def __del__(self):
        stop()
        disable_encoders()

    def turnRight(self, r):
        enc_tgt(1,0, r)
        right()
        time.sleep(.5)
        
    def turnLeft(self, r):
        enc_tgt(0,1, r)
        left()
        time.sleep(.5)
        
    def moveForward(self, r):
        enc_tgt(1,1, r)
        speed = 200
        right_speed = speed 
        higher_constant = 15
        lower_constant = 1
        set_right_speed(150)
        set_left_speed(155)
        fwd()
        
        
    def moveBackward(self, r): 
        enc_tgt(1,1, r)
        bwd()
        time.sleep(.5)

    def stop(self):
        stop()

    def rot(self, r):
        left_rot()
        time.sleep()
        stop()
