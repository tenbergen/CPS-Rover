from di_sensors import inertial_measurement_unit
from easygopigo3 import *
import time
gpg = EasyGoPiGo3()
imu = inertial_measurement_unit.InertialMeasurementUnit()
turn_degree = 90
offset = 25
actual_turn_degree = turn_degree + turn_degree * offset/360
gpg.set_speed(150)
try:
    print(imu.read_euler())
    #gpg.forward()
    time.sleep(1)

    gpg.turn_degrees(actual_turn_degree)
    #gpg.turn_degrees(turn_degree)
    time.sleep(1)
    print(imu.read_euler())
    time.sleep(1)
    gpg.turn_degrees(actual_turn_degree)
    #gpg.turn_degrees(turn_degree)
    time.sleep(1)
    print(imu.read_euler())
    time.sleep(1)
    gpg.turn_degrees(actual_turn_degree)
    #gpg.turn_degrees(turn_degree)
    time.sleep(1)
    print(imu.read_euler())
    gpg.turn_degrees(actual_turn_degree)
    #gpg.turn_degrees(turn_degree)
    time.sleep(1)
    print(imu.read_euler())
except Exception as ex:
    print(ex)
