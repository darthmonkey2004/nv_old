from nv.main.browser import start_thread
import psutil
from queue import Queue
import os
import time
import socket
import fcntl
import struct
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from threading import Thread
#from urllib.parse import parse_qs
from nv.main.conf import readConf, read_opts
from nv.main.mkhtml import mkhtml
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0 ,0)
from nv.main.process import process
from nv.main.log import nv_logger
import sys, traceback
import cv2
import datetime
logger = nv_logger().log_msg
from nv.main.nv_ui import start as start_ui


def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)


def get_ip_address(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(s.fileno(), -1071617759, struct.pack('256s', ifname[:15].encode()))[20:24])


class threadserver(ThreadingMixIn, HTTPServer):
	pass

class mjpg_server(BaseHTTPRequestHandler):
			
	def __init__(self, src=None, q=None, addr='127.0.0.1', port=8888, camera_id=0):
		if src is None and q is None:
			log(f"Error: Must set either a source or provide image queue!", 'error')
			return False
		if src is not None:
			self._src = src
			self.q = None
		elif q is not None:
			self._src = None
			self.q = q
		conf = readConf()
		self.debug = conf['debug']
		self.camera_id = camera_id
		self._name = f"Camera_{camera_id}"
		self._addr = addr
		self._port = port
		self._http_server = threadserver((self._addr, self._port), super().__init__)
		self._types = ('.mjpg', '.html', '.jpeg', '.json')
		self._methods = ['cv2', 'pil', 'raw', 'zmq', 'q']
		self._cur_method = 'q'
		self._size = 0
		self._quality = 0
		self._cur_method = 'cv2'
		self._pull_method = None
		self._cap = None
		self._img = None
		log(f"Server init complete! Details: {self._src}, {self._port}, {self._addr}", 'info')

	def set_quality(self, quality=0):
		self._quality = quality


	def set_cap(self, method):
		log(f"Initializing capture device:", 'info')
		if method in self._methods:
			log(f"Trying method: {method}...", 'info')
			self._cur_method = method
			if self._cur_method == 'cv2':
				self._cap = cv2.VideoCapture(self._src)
				self._pull_method = self.__get_cv2
			elif self._cur_method == 'pil':
				self._cap = cv2.VideoCapture(self._src)
				self._pull_method = self.__get_pil
			elif self._cur_method == 'raw':
				self._cap = cv2.VideoCapture(self._src)
				self._pull_method = self.__get_raw
			elif self._cur_method == 'zmq':
				self._pull_method = self.__get_zmq
				log(f"TODO: Finish this method! Old zmq image server is buried somewhere, find it!", 'warning')
				self._cap = None
			elif self._cur_method == 'q':
				self._pull_method = self.__get_q
				log(f"Queue initialized!", 'info')
			if self._cap is not None:
				log(f"Capture initialized! Using source: '{self._src}'", 'info')
		else:
			log(f"Error: No valid capture object! Aborting...", 'error')
			return False
		log(f"Capture and pull methods set: {self._cur_method}", 'info')
		return self._pull_method, self._cap
			
	def start(self, threaded=False):
		if self._pull_method is None:
			errmsg = f"Error: Unknown request type!"
			log(errmsg, 'error')
			raise RuntimeError(errmsg)

		if not threaded:
			log(f"Server starting (unthreaded)... 'http://{self._addr}:{self._port}/{self._name}.html'", 'info')
			self._http_server.serve_forever()
		else:
			log(f"Server starting (threaded)... 'http://{self._addr}:{self._port}/{self._name}.html'", 'info')
			mjpg_thread = Thread(target=self._http_server.serve_forever())
			mjpg_thread.setDaemon(True)
			mjpg_thread.start()

	def __write(self, message):
		if isinstance(message, str):
			self.wfile.write(message.encode('utf8'))
			self.wfile.write(message)

	def __get_q(self, data=None):
		_img = None
		if not self.q.empty():
			try:
				_grab = self.q.get_nowait()
				if _grab is not None:
					_img = _grab
				else:
					_img = None
			except Exception as e:
				_img = None
				#log(f"Error: Unable to get image from capture queue! ({e})", 'error')
		if _img is not None:
			#rgb = cv2.cvtColor(_img, cv2.COLOR_BGR2RGB)
			rgb = _img
			if self._quality > 0:
				encoded = cv2.imencode('.jpeg', rgb, [cv2.IMWRITE_JPEG_QUALITY, self._quality])[1]
			else:
				encoded = cv2.imencode('.jpeg', rgb)[1]
			encoded = bytearray(encoded)
			return encoded
		else:
			return None

	def __get_cv2(self, data=None):
		ret, _img = self._cap.read()
		if not ret:
			log(f"Error: Unable to get image from capture device!", 'error')
			#return None
		#if data is not None:
		#	_img = self.draw_on_image(_img, data)
		rgb = cv2.cvtColor(_img, cv2.COLOR_BGR2RGB)
		if self._quality > 0:
			encoded = cv2.imencode('.jpeg', rgb, [cv2.IMWRITE_JPEG_QUALITY, self._quality])[1]
		else:
			encoded = cv2.imencode('.jpeg', rgb)[1]
		encoded = bytearray(encoded)
		return encoded

	def __get_pil(self, data=None):
		ret, _img = self._cap.read()
		if not ret:
			log(f"Error: Unable to get image from capture device!", 'error')
			return None
		#if data is not None:
		#	_img = self.draw_on_image(_img, data)
		out = BytesIO()
		if self._quality > 0:
			_img.save(out, 'JPEG', quality=self._quality)
		else:
			_img.ave(out, 'JPEG')
		return out.getvalue()

	def __get_raw(self, data=None):
		ret, _img = self._cap.read()
		if not ret:
			log(f"Error: Unable to get image from capture device!", 'error')
			return None
		#if data is not None:
		#	_img = self.draw_on_image(_img, data)
		out = BytesIO()
		if isinstance(_img, str):
			out.write(_img.encode('utf8'))
		elif isinstance(_img, (bytearray, bytes)):
			out.write(_img)
		return out.getvalue()

	def __get_zmq(self):
		log(f"Finish me!", 'warning')
		pass

	def __sel_enc(self, data=None):
		if self._cap is None:
			self._cap = self.set_cap(self._cur_method)
			if self._cap is None:
				log(f"Error: Capture returned none! Method: {self._cur_method}", 'error')
				return None
		if data is None:
			if self._cur_method == 'cv2':
				enc = self.__get_cv2()
			elif self._cur_method == 'pil':
				enc = self.__get_pil()
			elif self._cur_method == 'raw':
				enc = self.__get_raw()
			elif self._cur_method == 'zmq':
				enc = self.__get_zmq()
			elif self._cur_method == 'q':
				enc = self.__get_q()
			return enc
		else:
			if self._cur_method == 'cv2':
				enc = self.__get_cv2(data)
			elif self._cur_method == 'pil':
				enc = self.__get_pil(data)
			elif self._cur_method == 'raw':
				enc = self.__get_raw(data)
			elif self._cur_method == 'zmq':
				enc = self.__get_zmq(data)
			return enc	

	def __handle_mjpeg(self):
		enc = None
		try:
			self.send_response(200)
			self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
			self.end_headers()
		except Exception as e:
			log(f"Exception in __handle_mjpeg (send content type response): {e}", 'error')
			return
		try:
			while True:
				#data = self.read_iofile()
				data = None
				if data is not None:
					enc = self.__sel_enc(data)
				else:
					enc = self.__sel_enc()
				if enc is not None:
					self.wfile.write("--jpgboundary".encode())
					self.wfile.write(bytes([13, 10]))
					self.send_header('Content-type', 'image/jpeg')
					self.send_header('Content-length', str(len(enc)))
					self.end_headers()
					self.wfile.write(enc)
					self.end_headers()
				try:
					self.q.task_done()
				except Exception as e:
					#log(f"MPJGSERVER::Q Empty ({e})", 'warning')
					pass
		except Exception as e:
			log(f"Exception in __handle_mjpeg (send data and end headers): {e}", 'error')
			log(f"Data:{traceback.format_exc()}", 'debug')
			return None


	def __handle_html(self):
		cams = readConf()
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		
		html = mkhtml(cams)
		self.wfile.write((html).encode('utf8'))

	def __handle_jpeg(self):
		enc = self.__sel_enc()
		if enc is None:
			self.send_error(505, 'Error parsing image')
		self.send_response(200)
		self.send_header('Content-type', 'image/jpeg')
		self.send_header('Content-length', len(enc))
		self.end_headers()
		self.wfile.write(enc)


	def do_POST(self):
		log(f"TODO: Finish this method for remote recognition, detection, and settings alteration.", 'warning')
		self.send_error(501, "Remote api in progress (TODO)")
		pass


	def do_GET(self):
		if self.path == '/':
			self.__handle_html()
		elif self.path.endswith(self._name + '.mjpg'):
			self.__handle_mjpeg()
		elif self.path.endswith(self._name + '.jpeg'):
			self.__handle_jpeg()
		elif self.path.endswith(self._name + '.json'):
			self.send_error(405, 'Must use POST to utilize this method')

class capture:
	def __init__(self, src=0):
		self.cap = cv2.VideoCapture(src)
		(self.grabbed, self.frame) = self.cap.read()
		self.stopped = False

	def start(self):
		self.t = Thread(target=self.read, args=())
		self.t.set_daemon = True
		self.t.start()
		return self

	def read(self):
		while not self.stopped:
			if not self.grabbed:
				self.stop()
			else:
				(self.grabbed, self.frame) = self.cap.read()
		return self.frame

	def release(self):
		self.stopped = True
		self.cap.release()
threads = {}

def set_tod(coords=()):
	if coords == ():
		lon = -98.2070059
		lat = 38.2100112
		coords = (lat, lon)
	sun = Sun(lat, lon)
	ct = datetime.datetime.now().timestamp()
	sr = sun.get_local_sunrise_time().timestamp()
	ss = sun.get_local_sunset_time().timestamp()
	if ct >= sr and ct <= ss:
		return 'day'
	elif ct >= sr and ct >= ss:
		return 'night'
	elif ct <= sr:
		return 'night'



def setup(camera_id=None):
	if camera_id is None:
		camera_id = 0
	else:
		camera_id = int(camera_id)
	cams = readConf()
	d = cams
	global mjpg_server
	opts = read_opts(camera_id)
	debug = opts['debug']
	del cams['debug']# remove this from conf, in opts
	maxsize = 30
	mjpg_in_q = Queue(maxsize=30)
	proc_in_q = Queue(maxsize=maxsize)
	proc_out_q = Queue()
	src = cams[camera_id]['src']
	d[camera_id]['html'] = mkhtml(cams, camera_id)
	d[camera_id]['proc_thread'] = start_process(opts, proc_in_q, proc_out_q)
	addr = cams[camera_id]['addr']
	port = int(cams[camera_id]['port'])
	mjpg_server = mjpg_server(src=None, q=mjpg_in_q, addr=addr, port=port, camera_id=camera_id)
	mjpg_server.set_cap(cams[camera_id]['method'])
	mjpg_server.set_quality(50)
	t = Thread(target=mjpg_server.start, args=(True,))
	t.setDaemon(True)
	t.start()
	log(f"Setup Finished, server running", 'info')
	return mjpg_in_q, proc_in_q, proc_out_q




def start_process(opts, in_q, out_q):
	proc_stream = Thread(target=process, args=(opts, in_q, out_q))
	proc_stream.setDaemon(True)
	proc_stream.start()

def draw_on_image(img, data, opts):
	w = img.shape[0]
	h = img.shape[1]
	drawn = img.copy()
	for line in data:
		object_name, box = line
		if box is not None:
			if type(box) == tuple and len(box) == 2:
				object_id, box = box
			l, t, r, b = box
			drawn = cv2.rectangle(img, (int(l), int(t), int(r), int(b)), RED, 2)
			y = t + 30
			coords = (int(l), int(y))
			drawn = cv2.putText(drawn, object_name, coords, opts['FONT'], opts['FONT_SCALE'], BLUE, 2, cv2.LINE_AA)
	return drawn


def run_server(camera_id):
	print("Starting")
	opts = read_opts(camera_id)
	mjpg_in_q, proc_in_q, proc_out_q = setup()
	cap = cv2.VideoCapture(opts['src'])
	width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
	height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
	dets = []
	t = Thread(target=start_ui, args=(opts,))
	t.setDaemon(True)
	t.start()
	frame_ct = 0
	fps = 30
	start_thread()
	while True:
		ret, img = cap.read()
		if ret:
			frame_ct += 1
			if frame_ct == 1:
				#initialize fps counter
				start_time = time.time()
			elif frame_ct == 30:
				#calculate fps
				duration = time.time() - start_time
				#set skip rate to twice the frame rate for processing feed (to stay current, low ram usage)
				fps = round(30 / duration) + 1
				#reset frame count to 0
				frame_ct = 0
				#print currrent main thread memory usage
				#log(f"MAINTHREAD-MEMORY-USAGE: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2}", 'info')
			img2 = img.copy()
			if not proc_in_q.full():
				# put fps * 2 (skip_frames rate) and img to process queue
				out = (fps, img2)
				proc_in_q.put_nowait(out)
			if not mjpg_in_q.full():
				img = draw_on_image(img, dets, opts)
				mjpg_in_q.put_nowait(img)
		if not proc_out_q.empty():
			data = proc_out_q.get_nowait()
			for camera_id in data.keys():
				dets = data[camera_id]
				try:
					proc_out_q.task_done()
				except Exception as e:
					log(f"MAINLOOP::proc_out_q Empty: ({e})", 'warning')


if __name__ == '__main__':
	run_server()
