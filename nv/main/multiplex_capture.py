#This is a class that will initialize a cv2 VideoCapture device and multiplex it out to a list of pipelines provided
#by the parent object.
import sys
import cv2
import keyring
import getpass
from nv.main.conf import read_opts
from nv.utils.utils import get_auth
import time
from threading import Thread
from nv.main.log import nv_logger
logger = nv_logger().log_msg

def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)

class multiplexer():
	def __init__(self, com_q, img_q_list=[], camera_id=0, run_threaded=True):
		if type(img_q_list) != list:
			self.img_q_list = [img_q_list]
		else:
			self.img_q_list = img_q_list
		self.com_q = com_q
		self.camera_id = camera_id
		self.opts = read_opts(camera_id)
		self.src = self.opts['src']['url']
		self.has_auth = self.opts['src']['has_auth']
		self.user = self.opts['src']['user']
		if self.has_auth:
			pw = get_auth(self.camera_id)
			self.src = f"rtsp://{user}:{pw}@{src.split('://')[1]}"
		self.exit = False
		self.is_capturing = False
		self.is_connected = False
		self.error = None
		#initialize img grab attempts counter before we mark with error
		self.fail_max = 30
		self.fail_ct = 0
		self.run_threaded = run_threaded
		self.cap = self.get_capture()
		if self.cap is not None:
			#if capture is good, start loop
			if self.run_threaded == True:
				#start threaded loop
				self.start_loop()
			else:
				#start regular loop (blocking???)
				self.start_loop()


	def get_capture(self):
		try:
			cap = cv2.VideoCapture(self.src)
			self.error = None
		except Exception as e:
			self.error = e
			log(f"Error: Couldn't get capture device: {self.error}", 'error')
			return None
		ret, img = cap.read()
		if ret:
			self.is_connected = True
		else:
			log(f"Camera initialized, but couldn't get image!", 'warning')
			self.connected = False
		if self.is_connected:
			self.cap = cap
			return self.cap
		else:
			self.error = f"Unknown error: is_connected returned False!"
			return None

	def start_loop(self):
		try:
			t = Thread(target=self.capture_loop)
			t.setDaemon(True)
			t.start()
			log(f"Capture loop running!", 'info')
			return True
		except Exception as e:
			log(f"Unable to start capture loop: {e}", 'error')
			return False

	def capture_loop(self):
		self.run = True
		#if class instance exit property is not True, loop as normal. settings self.exit = True will break loop
		while self.exit is not True and self.run is True:
			#check to see if any incoming commands are in queue
			if not self.com_q.empty():
				com = self.com_q.get_nowait()
				# send to command handler. log response if data returned.
				ret = self.command_handler(com)
				if ret:	
					log(f"MULTIPLEXER_COMMAND:{com}, Response:{ret}", 'info')
				#notify other end of pipe that command processing is finished.
				self.com_q.task_done()
			#read image
			ret, img = self.cap.read()
			if ret:
				#in case there was a temporary problem that's fixed, reset fail count to 0
				self.fail_ct = 0
				#set is_capturing flag to True if image received
				self.is_capturing = True
				for q in self.img_q_list:
					#if q isn't already full...
					if not q.full():
						q.put_nowait(img)
			else:
				#set capturing flag to false (possible reasons: reboot, temporary disconnect)
				self.is_capturing = False
				self.fail_ct += 1
				#if max retries exceeded...
				if self.fail_ct >= self.fail_max:
					#set is_connected flag to false and break loop. Will be up to main loop to re-initialize if possible.
					self.is_connected = False
					self.error = f"MULTIPLEXER:cap_read(): Max retries exceeded! Capture released, breaking loop."
					log(self.error, 'error')
					break
		# if loop broken and exit is True, run graceful exit
		if self.exit is True:
			self.quit()

	def quit(self):
		self.exit = True # if quit ran from parent, set self.exit to True to break above loop.
		# if capture still intialized...
		if self.cap is not None:
			self.cap.release()
			self.cap = None
			log(f"Capture released!", 'info')
		self.is_connected = False
		self.is_capturing = False
		#terminate thread
		exit()

	def command_handler(com):
		if com == 'quit':
			self.quit()
		if com == 'reinit':# if reinit, release and re initialize capture.
			#break current loop, but not exit.
			self.run = False
			self.cap.release()
			log(f"MULTIPLEXER:command_hanlder(reinit):Capture released!", 'info')
			log(f"MULTIPLEXER:command_hanlder(reinit):Waiting 3 secs...", 'info')
			time.sleep(1)
			log(f"MULTIPLEXER:command_hanlder(reinit):Waiting 2 secs...", 'info')
			time.sleep(1)
			log(f"MULTIPLEXER:command_hanlder(reinit):Waiting 1 secs...", 'info')
			time.sleep(1)
			log(f"MULTIPLEXER:command_hanlder(reinit):Reinitializing capture...", 'info')
			self.cap = self.get_capture()
			if self.cap is not None:
				log(f"MULTIPLEXER:command_hanlder(reinit):Capture re-initialized! Resuming loop...", 'info')
				ret = self.start_loop()
				if ret:
					log(f"MULTIPLEXER:command_hanlder(reinit):Sucess!", 'info')
				else:
					log(f"MULTIPLEXER:command_hanlder(reinit):Unable to re-init capture device. Exiting...", 'error')
					self.quit()
			elif self.cap is None:
				self.error = f"Device capture requests returned none! Aborting..."
				log(f"MULTIPLEXER:command_hanlder(reinit):{self.error}", 'error')
				self.quit()

