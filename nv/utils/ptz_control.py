import sys
import os
import subprocess
import requests
import base64
import time
import pickle
from nv.main.conf import read_opts, write_opts, init_opts
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


class ptz_control():
	def __init__(self):
		self.opts = read_opts(0)
		self.headers = {}
		self.base_path = self.opts['ptz']['base_path']
		self.param_endpoint = self.opts['ptz']['param_endpoint']
		self.control_endpoint = self.opts['ptz']['control_endpoint']
		self.addr = self.opts['ptz']['addr']
		self.speeds = [0, 1, 2]
		self.speeds_names = ['high', 'medium', 'low']
		self.uses_auth = self.opts['ptz']['auth']['uses_auth']
		self.user = self.opts['ptz']['auth']['user']
		self.event_loop = self.opts['ptz']['events']
		self.key = None
		self.action = None
		self.base_url = f"http://{self.addr}/{self.base_path}"
		self.stop_command = f"-step=0&-act=stop"
		self.stop_url = f"{self.create_url(type='control')}?{self.stop_command}"
		self.directions = ['left', 'downleft', 'down', 'downright', 'right', 'upright', 'up', 'upleft', 'stop']
		# if authentication used, modify empty headers dictionary to use basic auth
		if self.uses_auth is True:
			try:
				pw = self.get_pass()
				if pw is None:
					self.set_pass(user)
					pw = self.get_pass()
			except:
				self.set_pass(user)
				pw = self.get_pass()
			#pw = opts['auth']['pw']
			#string=f"{user}:{pw}".encode('ascii')
			#self.headers = {"Authorization: Basic'] = base64.b64encode(string).decode()
		

	def send(self, url):
		if self.uses_auth is True:
			pw = self.get_pass()
			ret = requests.get(url, auth=(self.user, pw))
		else:
			ret = requests.get(url)
		if ret.status_code == 200:
			return True
		else:
			log(f"Error: Bad status code: {ret.status_code}", 'error')
			return False


	def create_url(self, type=None):
		if type == 'control':
			url = f"{self.base_url}/{self.control_endpoint}"
		elif type == 'param':
			url = f"{self.base_url}/{self.param_endpoint}"
		return url


	def set_speed(self, pan_spd=1, tilt_spd=1):
		if pan_spd > 2 or pan_spd < 0:
			log(f"Error: pan speed out of range! (Valid options: 0=high, 1=medium, 2=low)", 'error')
			return False
		if tilt_spd > 2 or tilt_spd < 0:
			log(f"Error: tilt speed out of range! (Valid options: 0=high, 1=medium, 2=low)", 'error')
			return False
		set_command = f"cmd=setmotorattr&-tiltspeed={tilt_spd}&-panspeed={pan_spd}"
		url = f"{self.create_url(type='param')}?{set_command}"
		self.send(url)

	def get_pass(self):
		try:
			com = f"secret-tool lookup ptz_auth pw"
			return subprocess.check_output(com, shell=True).decode().strip()
		except Exception as e:
			log(f"Error getting password: {e}", 'info')
			return None


	def set_pass(self, user):
		label = f"ptz:{self.addr}"
		com = f"secret-tool store --label=\"{label}\" ptz_auth pw"
		return subprocess.check_output(com, shell=True).decode().strip()

	def goto(self, num):
		set_command = f"cmd=preset&-act=goto&-number={num}"
		url = f"{self.create_url(type='param')}?{set_command}"
		self.send(url)


	def set_goto(self, num):
		set_command = f"cmd=preset&-act=set&-status=1&-number={num}"
		url = f"{self.create_url(types='param')}?{set_command}"
		self.send(url)


	def step(self, d=None, wait=1):
		directions = ['left', 'downleft', 'down', 'downright', 'right', 'upright', 'up', 'upleft']
		if d is None:
			d = input("Enter direction:")
		if d not in self.directions:
			log(f"Unknown direction: {d}", 'info')
		else:
			self.action = f"{self.create_url(type='control')}?-step=0&-act={d}"
			self.send(self.action)
			time.sleep(wait)
			self.action = f"{self.create_url(type='control')}?-step=0&-act=stop"
			self.send(self.action)


	def move(self, d=None):
		if d not in self.directions:
			log(f"Unknown direction: {d}", 'info')
			return False
		else:
			self.action = f"{self.create_url(type='control')}?-step=0&-act={d}"
			self.send(self.action)


	def start_loop(self):
		try:
			from threading import Thread
			t = Thread(target=self.move_loop)
			t.setDaemon(True)
			t.start()
			log("Event loop started!", 'info')
			return True
		except Exception as e:
			log(f"Couldn't start loop: {e}", 'error')
			return False

	def move_loop(self):
		self.event_loop = True
		self.key = None
		while self.event_loop is True:
			if self.key is None:
				pass
			elif self.key == 'stop' or self.key == 'Stop':
				log(f"PTZ EVENT: {self.key.lower()}", 'info')
				self.move(self.key.lower())
				self.key = None
			else:
				log(f"PTZ EVENT: {self.key.lower()}", 'info')
				self.move(self.key.lower())
				self.key = None
		
	
if __name__ == "__main__":
	import sys
	try:
		act = sys.argv[1]
	except:
		log("Error: No arguments given!", 'info')
		exit()
	try:
		arg1 = sys.argv[2]
	except:
		arg1 = None

	ptz = ptz()
	
