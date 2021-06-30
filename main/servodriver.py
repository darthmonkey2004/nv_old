# servo control 15.12.2016
# 1) user set servo position in python
# 2) position is sent to arduino
# 3) arduino moves servo to position
# 4) arduino send confirmation message back to python
# 5) message is printed in python console
import serial# import serial library

class ServoDriver :

	def __init__(self, port='/dev/ttyACM0', baud=57600):
		self.servo = serial.Serial(port, baud)# create serial object named arduino
		self.panServo = 1
		self.tiltServo = 2
		self.tiltAngle = 90
		self.panAngle = 90
		self.left = False
		self.right = False
		self.up = False
		self.down = False

	def move(self, x, y, w, h):
		cx = w/2
		cy = h/2
		cx_low = (cx - (w / 6))
		cx_high = (cx + (w / 6))
		cy_low = (cy - (h / 6))
		cy_high = (cy + (h / 6))
		print (cx_low, cx, cx_high)
		print (cy_low, cy, cy_high)
		if (x < cx_low):#if object is left of center...
			self.left = True#remove left move flag
			self.right = False#set right move flag

		if (x > cx_high):#if object is right of center...
			self.right = True#remove right move flag
			self.left = False#set left move flag
		
		if (x >= cx_low) and (x <= cx_high):# if object is in centered on x axis...
			self.right = False#set left false
			self.left = False#set right false

		if (y < cy_low):#if object is above center...
			self.down = False#set down true
			self.up = True#set up false

		if (y > cy_high):# if object is below center...
			self.down = True#set down false
			self.up = False #set up true

		if (y > cy_low) and (y < cy_high):# if object is centered on y axis...
			self.down = False
			self.up = False

		if (self.up == True) and (self.left == True):#upleft
			print ("up_left")
			self.tiltAngle = self.tiltAngle - 10
			self.panAngle = self.panAngle + 10
		if (self.up == True) and (self.right == True):#upright
			print ("up_right")
			self.tiltAngle = self.tiltAngle - 10
			self.panAngle = self.panAngle - 10
		if (self.up == True) and (self.right == False) and (self.left == False):#up
			print ("up")
			self.tiltAngle = self.tiltAngle - 10
		if (self.down == True) and (self.left == True):#downleft
			print ("down_left")
			self.tiltAngle = self.tiltAngle + 10
			self.panAngle = self.panAngle + 10
		if (self.down == True) and (self.right == True):#downright
			print ("down_right")
			self.tiltAngle = self.tiltAngle + 10
			self.panAngle = self.panAngle - 10
		if (self.down == True) and (self.right == False) and (self.left == False):#down
			print ("down")
			self.tiltAngle = self.tiltAngle + 10
		if (self.left == True) and (self.up == False) and (self.down == False):#left
			print ("left")
			self.panAngle = self.panAngle + 10
		if (self.right == True) and (self.up == False) and (self.down == False):#right
			self.panAngle = self.panAngle - 10
			print ("right")
		if self.panAngle > 180:
			self.panAngle = 180
		elif self.panAngle < 0:
			self.panAngle = 0
		if self.tiltAngle > 180:
			self.tiltAngle = 180
		elif self.tiltAngle < 0:
			self.tiltAngle = 0

		com = (str(self.tiltServo) + ":" + str(self.tiltAngle))
		b = str.encode(com)
		self.servo.write(b)
		tilt_results = str(self.servo.readline())
		com = (str(self.panServo) + ":" + str(self.panAngle))
		b = str.encode(com)
		self.servo.write(b)
		pan_results = str(self.servo.readline())
		print ("Wrote to servo: " + com)


	def fire(self):
		self.servo.write('3:0')
		reachedPos = str(self.servo.readline())# read serial port for arduino echo
		print (reachedPos)# print arduino echo to console
