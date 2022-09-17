# servo control 15.12.2016
# 1) user set servo position in python
# 2) position is sent to arduino
# 3) arduino moves servo to position
# 4) arduino send confirmation message back to python
# 5) message is printed in python console
import serial# import serial library
import requests

class ServoDriver :

	def __init__(self):
		self.panSpeed = 2
		self.left = False
		self.right = False
		self.up = False
		self.down = False
		self.count = 0

	def move(self, x, y, w, h):
		cx = w/2
		cy = h/2
		cx_low = (cx - (w / 6))
		cx_high = (cx + (w / 6))
		cy_low = (cy - (h / 6))
		cy_high = (cy + (h / 6))
		if (x < cx_low):#if object is left of center...
			self.left = True#remove left move flag
			self.right = False#set right move flag

		if (x > cx_high):#if object is right of center...
			self.right = True#remove right move flag
			self.left = False#set left move flag
		
		if (x > cx_low) and (x < cx_high):# if object is in centered on x axis...
			self.right = False#set left false
			self.left = False#set right false

		#if (y < cy_low):#if object is above center...
		#	self.down = False#set down true
		#	self.up = True#set up false

		#if (y > cy_high):# if object is below center...
		#	self.down = True#set down false
		#	self.up = False #set up true

		#if (y > cy_low) and (y < cy_high):# if object is centered on y axis...
		#	self.down = False
		#	self.up = False
		#if (self.up == True) and (self.left == True):#upleft
		#	url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=upleft&-speed=5"
		#	print ("up_left")
		#if (self.up == True) and (self.right == True):#upright
		#	url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=upright&-speed=5"
		#	print ("up_right")
		#if (self.up == True) and (self.right == False) and (self.left == False):#up
		#	url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=up&-speed=5"
		#	print ("up")
		#if (self.down == True) and (self.left == True):#downleft
		#	url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=downleft&-speed=5"
		#	print ("down_left")
		#if (self.down == True) and (self.right == True):#downright
		#	url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=downright&-speed=5"
		#	print ("down_right")
		#if (self.down == True) and (self.right == False) and (self.left == False):#down
		#	url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=down&-speed=5"
		#	print ("down")
		if (self.left == True):#left
			url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=left&-speed=5"
		if (self.right == True):#right
			url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=right&-speed=5"
		if (self.right == False) and (self.left == False):
			url = "http://admin:N0712731l@192.168.2.5/web/cgi-bin/hi3510/ptzctrl.cgi?-step=0&-act=stop&-speed=5"
		r =requests.get(url)	

	def fire(self):
		self.servo.write('3:0')
		reachedPos = str(self.servo.readline())# read serial port for arduino echo
		print (reachedPos)# print arduino echo to console
