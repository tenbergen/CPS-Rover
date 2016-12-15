##############################################################################
#MIT License
#
#Copyright (c) 2016 Mike Mekker, Justin MacCreery, Ryan Staring
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
##############################################################################

from picamera.array import PiRGBArray
from picamera import PiCamera
import imutils
import json
import argparse
import time
import cv2
from gopigo import *
import MotorControl

#Set which cascade classifiers to use
side = cv2.CascadeClassifier('/home/pi/Kitt/data/GLC8/Side/GLCS8.15.xml')
fb = cv2.CascadeClassifier('/home/pi/Kitt/data/GLC8/FrontBack/GLCFB8.15.xml')

motor = MotorControl.MotorControl()

print("[INFO] 4 second warm up...")

camera = PiCamera()
camera.resolution = (608, 464)
camera.framerate = 16
camera.hflip = True
camera.vflip = True

rawCapture = PiRGBArray(camera, size=(608, 464))

time.sleep(2.5)

Distance = 600
Where = None
ObjectCenter = False

moveStr = ""
previous = ""
move = 1
checkForTurn = 0

for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

    enable_encoders()
    frame = f.array
    frame = imutils.resize(frame, width=608)
    
    centerOfFind= -1 #Center of the best find
    cropped = frame[175:375, 0:608]
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("gray.jpg", gray)
    DetectedFB = fb.detectMultiScale(gray, 1.1, 5) #Search for FrontBack of GoPiGo
    DetectedS = side.detectMultiScale(gray, 1.1, 5) #Search for Sides of GoPiGo
    
    #Loop through all detected FrontBacks
    for (x, y, w, h) in DetectedFB:
        print("found front/back")
        
        #Draw a rectangle around the find
        cv2.rectangle(gray, (x, y), (x + w, y + h), (255, 255, 0), 2)
        
        #SAVE the result image
        cv2.imwrite("results/aresult_frontback.jpg", gray)
        
        #Compute new center and check against old
        newCenter = x + (w/2)

        #Check if any have been found yet
        if centerOfFind == -1:
            centerOfFind = newCenter

        #Checks which is closer to the center
        elif centerOfFind < 304:
            if centerOfFind < newCenter:
                centerOfFind = newCenter
        elif centerOfFind > 304:
            if centerOfFind > newCenter:
                centerOfFind = newCenter
    if centerOfFind == -1:
        #Loop through all detected sides
        for (x, y, w, h) in DetectedS:
            print("found side")
            
            #Draw a rectangle around the find
            cv2.rectangle(gray, (x, y), (x + w, y + h), (255, 255, 0), 2)
            
            #SAVE the result image
            cv2.imwrite("results/aresult_side.jpg", gray)
            
            #Compute new center and check against old
            newCenter = x + (w/2)

            #Check if any have been found yet
            if centerOfFind == -1:
                centerOfFind = newCenter

            #Checks which is closer to the center
            elif centerOfFind < 304:
                if centerOfFind < newCenter:
                    centerOfFind = newCenter
            elif centerOfFind > 304:
                if centerOfFind > newCenter:
                    centerOfFind = newCenter
    
    d = servo.distance() #Measure Distance to Find
    moveStr = "" #Where it was seen

    if centerOfFind < 240 and centerOfFind > -1: #Found in the left section (0-240)
        moveStr = "left"
        print("left: " + str(centerOfFind))
        
    elif centerOfFind < 360 and centerOfFind > -1: #Found in the center section (240-360)
        if d > 150: #If the find is more than 150cm away
            moveStr = "fwdfar"
            if checkForTurn == 1:
                checkForTurn = 0
            move = 1
            print("fwdfar: " + str(centerOfFind))
        elif d < 80: #If we are closer than 80cm
            moveStr = "close"
            print("close: " + str(centerOfFind))
        else: #Between 80 and 150
            moveStr = "fwd"
            if checkForTurn == 1:
                checkForTurn = 0
            move = 1
            print("fwd: " + str(centerOfFind))
            
    elif centerOfFind < 608 and centerOfFind > -1: #Found in the right section (360-608)
        moveStr = "right"
        print("right: " + str(centerOfFind))

    if move == 1: #if we can move
        if moveStr == "close": 
            checkForTurn = 1 #check for if it turned on the next iteration of the loop
            move = 0
        elif moveStr == "fwd":
            motor.moveForward(7)
        elif moveStr == "fwdfar":
            motor.moveForward(10)
        if moveStr == "right":
            motor.turnRight(1)
        elif moveStr == "left":
            motor.turnLeft(1)
    else:
        if moveStr == previous:
            if checkForTurn == 1: #if looking for it to be turning  
                if moveStr == "right":
                    time.sleep(4)
                    print("move forward for turn")
                    motor.moveForward(int(d * .68)+ 15)
                    time.sleep(4)
                    print("            turn right")
                    motor.turnRight(16)
                    move = 1
                    checkForTurn = 0
                    moveStr = ""
                    previous = ""
                    
                elif moveStr == "left":
                    time.sleep(4)
                    print("move forward for turn")
                    motor.moveForward(int(d * .68)+ 15)
                    time.sleep(4)
                    print("            turn left")
                    motor.turnLeft(16)
                    move = 1
                    checkForTurn = 0
                    moveStr = ""
                    previous = ""
                    
    previous = moveStr  
    centerOfFind = -1
    print("moveStr: " + str(moveStr))
    print("move: " + str(move))
    print("checkForTurn: " + str(checkForTurn))
    print("Distance: " + str(d))
    rawCapture.truncate(0)














