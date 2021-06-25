import imagezmq
import cv2



#TODO:
#1. modify zmq function code to handle 'ERROR' response (camera source unavailable on client end)
#2. modify client.py (zmq) to detect non-response from offlline/crashed server and handle accordingly.
#3. Modify cams.py's readConf and findCamera methods to test and filter out offline/non-functional cameras. (main script)
#4. Add filtered camera list to different dict object.
#4. Modify cams.py's call to nv.mkHtml.sh to only include objects in online_cams dict object, re-write html (and refresh?) on changes
#5. 

class VideoCapture:
	def __init__(self, id, src):
		self.zmq_check = "zmq://"
		self.id = id
		self.src = src
		if self.zmq_check in self.src:
			self.port = src.split("/")[2]
			self.type="zmq"
			self.constr = ('tcp://' + str(self.port))
			self.cap = imagezmq.ImageHub(self.constr)
		else:
			self.type="cv2"
			self.port="Null"
			self.cap = cv2.VideoCapture(self.src)

	def read(self):
		if self.type == 'zmq':
			try:
				(self.name, self.img) = self.cap.recv_image()
				if self.img is not None:
					self.state = (True, True)
					reply = ('Resp:OK, State:' + str(self.state))
					rep = reply.encode()
				else:
					#self.cap.send_reply(b'ERROR, Img:False')
					self.state = (True, False)
					reply = ('Resp:ERROR, State:' + str(self.state))
					rep = reply.encode()
			except:
				self.state = (False, False)
				#TODO: Insert code to remove disconnected/offline camera from active cameras dictionary (add to main code in cams.py)
				# assigns 'Camera ID not found' to removed_cam if not in dictionary instead of raising exception.
				#removed_cam = cameras.pop(id, 'Camera Id not found') 
			self.cap.send_reply(rep)
		elif self.type == 'cv2':
			state, self.img = self.cap.read()
			self.state = (True, state)
		return (self.state, self.img)

	def release(self):
		if self.type == 'cv2':
			self.cap.release()
			self.state = (False, False)
		elif self.type == 'zmq':
			self.state = (False, False)
			reply = ('Com:disconnect, State: ' + str(self.state))
