import gopigo
from marvelmind import MarvelmindHedge
from time import sleep
import sys

dst = 0.0
def main():
    hedge = MarvelmindHedge(tty = "/dev/ttyACM0", adr=10, debug=False) # create MarvelmindHedge thread
    hedge.start() # start thread
    sleep(.1)
    start_pos = convert2D(hedge.position())
    print hedge.position()
    print start_pos
    new_pos = start_pos
    dst = 0.0
    gopigo.set_speed(100)
    gopigo.fwd()
    try:
        while(abs(dst)<1):
            sleep(.1)
            new_pos = convert2D(hedge.position())
            hedge.print_position()
            dst = distance(start_pos,new_pos)
            print "start: ",start_pos
            print "current: ",new_pos
            print "distance: ",dst
    except KeyboardInterrupt:
        hedge.stop()  # stop and close serial port
        gopigo.stop()
        sys.exit()
    hedge.stop()
    gopigo.stop()
        

def convert2D(coord):
    new_coord = [coord[0],coord[1]]
    return new_coord

def distance(a,b):
    return pow(pow(a[0]-b[0],2) + pow(a[1] - b[1],2),.5)


main()
