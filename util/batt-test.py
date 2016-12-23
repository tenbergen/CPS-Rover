# !/usr/bin/env python

from gopigo import *
import sys
import atexit

atexit.register(stop)
enable_encoders()
speed = 200
set_speed(speed)
fwd()
secs = 0

while True:
    print secs, volt(), enc_read(0), enc_read(1)
    secs += 10
    time.sleep(10)