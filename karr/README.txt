Karr is an autonomous rover with a GPS Module.

Functionality:
- Karr can be controlled remotely with an XBOX 360 controller which includes:
	- Movement
	- Return home (to starting coordinate)
	- LED light toggle
- Karr follows a set of GPS coordinates using Dijkstra's shortest path Algorithm when Karr disconnects from the network.


Installation:
Place all files in the Server folder on Karr. 
Note: The files should be stored on Karr under the directory: "/Desktop/Controller".

Before running the program, the gps module needs to be started. To start it, run this command on a terminal window:
>>> sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock
Note: There is a script file that is executed on startup that starts the GPS module.

Next, check that the GPS is running is getting a signal by running:
>>> cgps
If the latitude and longitude display as N/A, then the GPS module is not turned on.
To restart the GPS module, navigate to the home directory by:
>>> cd
and running the script that runs the above command:
>>> ./startgps

Once Karr starts acquiring GPS coordinates run server.py by:
>>> python server.py


Place all files in the Controller folder on a computer with Ubuntu or a Virtual Machine running Ubuntu.
Karr uses pygame to take controller input. Install by running the command:
>>> sudo apt-get install python-pygame
Pygame uses the Python2 interpreter. To run any file that uses Pygame use:
>>> python2 file.py
To set Python2 as your default Python interpreter, run the commands:
>>> nano ~/.bash_aliases
>>> alias python='python2'
Now, Pygame can run by using the default python run code by:
>>> python file.py

Next, start the control.py file.

Make sure to start server.py before running control.py.


Known Issues:
- The GPS module is not very accurate. Coordinates are taken in a wide area around Karr.
- When running the return home feature, the server connection times out to the controller. This bug is mainly caused by performing other commands while the return home feature is running.