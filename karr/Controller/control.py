import pygame
import sys, os
import socket
from threading import Thread
from time import sleep
import select
import urllib2

pygame.display.init()
pygame.joystick.init()

#KARR uses AdaFruit Ultimate GPS
#written tutorials for setting it up on page 3
#always run before using gps on KARR
# sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock
#test using: cgps
#more on this
#https://learn.adafruit.com/adafruit-ultimate-gps-on-the-raspberry-pi/setting-everything-up

global sock
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '192.168.1.101'
port = 10000
sock.connect((host, port))
#global running
running = True
global curx
curx = 0
global cury
cury = 0

class Speed(Thread):
	def __init__(self):
		Thread.__init__(self)
	
	def run(self):
		global running
		global curx
		global cury
		while running:
			r, _, _ = select.select([sock], [], [], 2)
			if not r:
				print "I have left speeder"
				return
			newspeed = sock.recv(1024).split()
			if len(newspeed) < 2:
				temp = 0
			elif newspeed[0] == "M":
				if newspeed[1] != curx and newspeed[2] != cury:
					send_message("Stop M " + str(curx) + " " + str(cury))
			elif newspeed[0] == "G":
				print "Latitude", newspeed[1]
				print "Longitude", newspeed[2]
			
def isConnected():
	global addr
	try:
		urllib2.urlopen("http://" + host, timeout=1)
		return True
	except urllib2.URLError as err:
		return False
	except socket.timeout as err:
		return False


def send_message(message):
	print message
	sock.send(str.encode(message + " XXX"))

def main():

	joysticks = []
	clock = pygame.time.Clock()
	axisPos = [0, 0, 0, 0]
	global curx
	global cury
	global running
	curx = 0
	cury = 0

	for i in range(0, pygame.joystick.get_count()):
		joysticks.append(pygame.joystick.Joystick(i))
		joysticks[-1].init()

	print "Ready for input"

	while running:		
		message = ""
		clock.tick(60)
		if not isConnected():
			return
		for event in pygame.event.get():
			if event.type == pygame.JOYBUTTONDOWN:
				if event.button == 0:
					send_message("LON")
				elif event.button == 6:
					running = False
				elif event.button == 8:
					print "Sending home message"
					send_message("Home")
				elif event.button == 11:
					send_message("Stop")
			elif event.type == pygame.JOYAXISMOTION:
				if axisPos[0] != joysticks[0].get_axis(0) or axisPos[1] != joysticks[0].get_axis(1):
					x = float(joysticks[0].get_axis(0))
					y = float(joysticks[0].get_axis(1))
					if -0.03 < x < 0.03 and -0.03 < y < 0.03:
						#stopped
						curx = 0
						cury = 0
					elif -0.03 < y < 0.03:
						#turning
						if x < 0:
							curx = 0
							cury = int(x * 250)
						else:
							curx = int(x * 250)
							cury = 0
					elif -0.03 < x < 0.03:
						#straight
						curx = int(y * 250)
						cury = int(y * 250)
					else:
						#diagonal
						if x < 0.03 and y < 0.03:
							cury = - int((abs(x)+abs(y)) * 250)
							if cury < -250:
								cury = -250
							curx = int((x-y)*cury)
							curx = - ((curx + cury) / 2)
						elif x < 0.03 and y > 0.03:
							cury = int((abs(x)+abs(y)) * 250)
							if cury > 250:
								cury = 250
							curx = int((x+y)*cury)
							curx = ((curx + cury) / 2)
						elif x > 0.03 and y < 0.03:
							curx = - int((abs(x)+abs(y)) * 250)
							if curx < -250:
								curx = -250
							cury = int((x+y)*250)
							cury = ((cury - 250) / 2)
						elif x > 0.03 and y > 0.03:
							curx = int((abs(x)+abs(y)) * 250)
							if curx > 250:
								curx = 250
							cury = int((y-x)*curx)
							cury = ((cury + curx) / 2)
					send_message("M " + str(curx) + " " + str(cury))
					print "Original: " + str(int(x * 250)) + " " + str(int(y * 250))
					print "Speed: " + str(curx) + " " + str(cury)
				elif axisPos[2] != joysticks[0].get_axis(2):
					axisPos[2] = joysticks[0].get_axis(2)
					send_message("SER " + str(axisPos[2]))
					
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
				running = False
			elif event.type == pygame.JOYBUTTONUP:
				if event.button == 13 or event.button == 14 or event.button == 15 or event.button == 16:
					send_message("Stop")
				elif event.button == 0:
					send_message("LOFF")
	print "Quitting"

speeder = Speed()
speeder.start()
main()
speeder.join()
sock.close()
pygame.joystick.quit()
pygame.display.quit()
sys.exit()			
