# servo control 15.12.2016
# 1) user set servo position in python
# 2) position is sent to arduino
# 3) arduino moves servo to position
# 4) arduino send confirmation message back to python
# 5) message is printed in python console
import serial# import serial library

class ServoDriver :

	def __init__(self, port='/dev/ttyACM0', baud=9600):
		self.servo = serial.Serial(port, baud)# create serial object named arduino
		self.panServo = 1
		self.tiltServo = 0
		self.tiltAngle = 0
		self.panAngle = 0

	def move(self, x, y, w, h):
		cx = w/2
		cy = h/2
		cx_low = (cx - (w / 10))
		cx_high = (cx + (w / 10))
		cy_low = (cy - (h / 10))
		cy_high = (cy + (h / 10))
		print (cx_low, cx, cx_high)
		print (cy_low, cy, cy_high)
		if (x < cx_low):
			self.panAngle += 5
			if self.panAngle > 180:
				self.panAngle = 180
			com = (str(self.panServo) + ":" + str(self.panAngle))
			b = str.encode(com)
			self.servo.write(b)# write position to serial port
			print ("Wrote to servo: " + com)

		if (x > cx_high):
			self.panAngle -= 5
			if self.panAngle < 0:
				self.panAngle = 0
			com = (str(self.panServo) + ":" + str(self.panAngle))
			b = str.encode(com)
			self.servo.write(b)# write position to serial port
			print ("Wrote to servo: " + com)
		
		if (x > cx_low) and (x < cx_high):
			self.panAngle = 90
			com = (str(self.panServo) + ":" + str(self.panAngle))
			b = str.encode(com)
			self.servo.write(b)# write position to serial port
			print ("Wrote to servo: " + com)

		if (y < cy_low):
			self.tiltAngle += 5
			if self.tiltAngle > 180:
				self.tiltAngle = 180
			com = (str(self.tiltServo) + ":" + str(self.tiltAngle))
			b = str.encode(com)
			self.servo.write(b)# write position to serial port
			print ("Wrote to servo: " + com)

		if (y > cy_high):
			self.tiltAngle -= 5
			if self.tiltAngle < 0:
				self.tiltAngle = 0
			com = (str(self.tiltServo) + ":" + str(self.tiltAngle))
			b = str.encode(com)
			self.servo.write(b)# write position to serial port
			print ("Wrote to servo: " + com)

		if (y > cy_low) and (y < cy_high):
			self.tiltAngle = 90
			com = (str(self.tiltServo) + ":" + str(self.tiltAngle))
			b = str.encode(com)
			self.servo.write(b)# write position to serial port
			print ("Wrote to servo: " + com)


	def fire(self):
		self.servo.write('3:0')
		reachedPos = str(self.servo.readline())# read serial port for arduino echo
		print (reachedPos)# print arduino echo to console
