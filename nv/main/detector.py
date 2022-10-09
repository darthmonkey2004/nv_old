from nv.main.conf import read_opts, write_opts, init_opts
import pickle
import datetime
from suntime import Sun, SunTimeException
import os
import imutils
from nv.main.fr_dlib import fr_dlib
import numpy as np
import cv2
from nv.main.log import nv_logger
from nv.main.conf import readConf
import sys, traceback
from nv.utils.ptz_control import ptz_control
ptz = ptz_control()
fr_dlib = fr_dlib()

logger = nv_logger().log_msg
TRACKER_TYPES = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'CSRT']

def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)


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

def constrain_box(img, l, t, r, b):
	h, w, c = img.shape
	if t <= 0:
		t = 10
	elif t >= h:
		t = h - 10
	if b <= 0:
		b = 10
	elif b >= h:
		b = h - 10
	if r <= 0:
		r = 10
	elif r >= w:
		r = w - 10
	if l <= 0:
		l = 10
	elif l >= w:
		l = w - 10
	return l, t, r, b


def get_output_layers(net):	
	layer_names = net.getLayerNames()
	output_layers = []
	l = list(layer_names)
	for i in net.getUnconnectedOutLayers():
		pos = i - 1
		output_layers.append(l[pos])
	return output_layers


def get_known_names(opts):
	cv2_known_names_path = opts['detector']['fr_cv2']['dataset']
	names = []
	for name in next(os.walk(cv2_known_names_path))[1]:
		name = name.replace('_', ' ')
		names.append(name)
	return names
		


class detector:
	def __init__(self, opts={}):
		if opts == {}:
			opts = read_opts(0)
		self.opts = opts
		self.det_provider = self.opts['detector']['provider']
		self.name = None
		self.matches = []
		self.face_location = None
		self.test_location = None
		self.box = None
		self.all_encodings = self.get_known_encodings()
		self.fr_dlib_known_encodings = self.all_encodings.values()
		self.fr_dlib_known_names = [name.split('_')[0] for name in list(self.all_encodings.keys())]
		
		self.classes = self.opts['detector']['object_detector']['classes']
		self.net = cv2.dnn.readNetFromCaffe(self.opts['detector']['object_detector']['prototxt'], self.opts['detector']['object_detector']['model'])
		self.targets = self.opts['detector']['object_detector']['targets']
		self.target_confidence = float(self.opts['detector']['object_detector']['confidence'])
		self.l = 0
		self.t = 0
		self.r = 0
		self.b = 0
		camera_id = self.opts['camera_id']
		self.H = opts['H']
		self.W = opts['W']
		print(self.H, self.W)
		self.tolerance = self.opts['detector']['fr']['tolerance']
		self.model = self.opts['detector']['fr']['model']
		self.mean = (127.5, 127.5, 127.5)
		#self.scale = (300 / self.W) / 100
		#self.scale = 0.004688
		self.scale = 0.01
		#self.detector_input_shape = (self.W, self.H)
		self.detector_input_shape = (300, 300)
		self.cv2_recognizer = cv2.face.LBPHFaceRecognizer_create()
		#self.cv2_detector = self.opts['cv2_detector']
		self.faceCascade = cv2.CascadeClassifier(self.opts['detector']['fd_cv2']['face_cascade']);
		self.font = cv2.FONT_HERSHEY_SIMPLEX
		cv2_fr_trained = self.opts['detector']['fr_cv2']['dbpath']
		self.cv2_known_names = get_known_names(opts)
		self.cv2_recognizer.read(cv2_fr_trained)
		self.cv2_detector = cv2.CascadeClassifier('/home/monkey/.np/nv/haarcascade_frontalface_default.xml')
		#yolov3 init
		self.yolo_config = '/var/dev/cv tests/yolov3/object-detection-opencv/yolov3.cfg'
		self.yolo_weights = '/var/dev/cv tests/yolov3/object-detection-opencv/yolov3.weights'
		self.yolo_scale = 0.00392
		self.yolo_classes = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
		self.yolo_colors = np.random.uniform(0, 255, size=(len(self.yolo_classes), 3))
		self.yolo_net = cv2.dnn.readNet(self.yolo_weights, self.yolo_config)
		self.flip_image = False

	def ptz_track_to_center(self, img, box):
		duration = 0
		d = None
		d = {}
		x_dist = 0
		y_dist = 0
		l, t, r, b = box
		box_cx = ((r - l) / 2) + l
		box_cy = ((b - t) / 2) + t
		img_cx = img.shape[1] / 2
		img_cy = img.shape[0] / 2
		if box_cx > img_cx:
			x_d = 'right'
			x_dist = box_cx - img_cx
		elif box_cx < img_cx:
			x_d = 'left'
			x_dist = img_cx - box_cx
		elif box_cx == img_cx:
			x_d = 'center'
		if box_cy > img_cy:
			y_d = 'down'
			y_dist = box_cy - img_cy
		elif box_cy < img_cy:
			y_d = 'up'
			y_dist = img_cy - box_cy
		elif box_cy == img_cy:
			y_d = 'center'
		rx = (y_dist / img.shape[0]) * 1000
		ry = (x_dist / img.shape[1]) * 1000
		min = 1
		max = 486
		rx = round((rx / max) * 100)
		ry = round((ry / max) * 100)
		print(rx, ry)
		if rx <= 10:
			dx, sx = None, None
		elif rx > 10 and rx <= 20:
			dx, sx = ptz.s[1]
		elif rx > 20 and rx <= 30:
			dx, sx = ptz.s[2]
		elif rx > 30 and rx <= 40:
			dx, sx = ptz.s[3]
		elif rx > 40 and rx <= 50:
			dx, sx = ptz.s[4]
		elif rx > 50 and rx <= 60:
			dx, sx = ptz.s[5]
		elif rx > 60 and rx <= 70:
			dx, sx = ptz.s[6]
		elif rx > 70 and rx <= 80:
			dx, sx = ptz.s[7]
		elif rx > 80 and rx <= 90:
			dx, sx = ptz.s[8]
		elif rx > 90:
			dx, sx = ptz.s[9]
		if ry <= 10:
			dy, sy = None, None
		elif ry > 10 and ry <= 20:
			dy, sy = ptz.s[1]
		elif ry > 20 and ry <= 30:
			dy, sy = ptz.s[2]
		elif ry > 30 and ry <= 40:
			dy, sy = ptz.s[3]
		elif ry > 40 and ry <= 50:
			dy, sy = ptz.s[4]
		elif ry > 50 and ry <= 60:
			dy, sy = ptz.s[5]
		elif ry > 60 and ry <= 70:
			dy, sy = ptz.s[6]
		elif ry > 70 and ry <= 80:
			dy, sy = ptz.s[7]
		elif ry > 80 and ry <= 90:
			dy, sy = ptz.s[8]
		elif ry > 90:
			dy, sy = ptz.s[9]
		print (dx, sx, dy, sy)
		if dx is None and sx is None and dy is None and sy is None:
			move = False
		else:
			if dy is not None and dx is not None:
				if dy < dx:
					duration = dx
				elif dy > dx:
					duration = dy
				elif dy == dx:
					duration = dx
			elif dy is not None and dx is None:
				duration = dy
			elif dy is None and dx is not None:
				duration = dx
			else:
					duration = None
			ptz.set_speed(sx, sy)
			move = True
		if move:
			if x_d != 'center' and y_d != 'center':
				d = f"{y_d}{x_d}"
			elif x_d == 'center' and y_d != 'center':
				d = y_d
			elif x_d != 'center' and y_d == 'center':
				d = x_d
			else:
				d = None
			if d is not None and duration is not None:
				ptz.step(d, duration)

	def get_known_encodings(self):
		datfile = os.path.join(os.path.expanduser("~"), '.np', 'nv', 'nv_known_faces.dat')
		with open(datfile, 'rb') as f:
			self.all_encodings = pickle.load(f)
			f.close()
		return self.all_encodings

	def refresh_opts(self):
		self.opts = read_opts()

	def face_detect(self, imgpath):
		if self.det_provider == 'dlib':
			return self.face_detect_dlib(imgpath)
		elif self.det_provider == 'cv2':
			return self.face_detect_cv2(imgpath)

	def face_detect_cv2(self, img):
		if self.flip_image == True:
			img = cv2.flip(img, -1)
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		faces = self.faceCascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(20, 20))
		out = []
		for (x,y,w,h) in faces:
			box = x, y ,x+w, y+h
			name = 'Unrecognized Face'
			confidence = None
			o = (name, box, confidence)
			out.append(o)
		if ptz.track_to_center:
			try:
				self.ptz_track_to_center(img, out[0][1])
			except:
				pass
		return out


	def face_detect_dlib(self, imgpath):
		if type(imgpath) == str:
			img = cv2.imread(imgpath)
		else:
			img = imgpath
		img = imutils.resize(img, width=400)
		if img is None:
			return (None, None, None)
		model = self.opts['detector']['fr_dlib']['model']
		upsamples = self.opts['detector']['fr_dlib']['upsamples']
		self.box = fr_dlib.face_locations(img, upsamples=upsamples, model=model)
		if ptz.track_to_center:
			try:
				self.ptz_track_to_center(img, box)
			except:
				pass
		if self.box is None:
			return (None, None, None)
		self.name = "Detected Face"
		try:
			out = (self.name, self.box[0], None)
		except:
			out = (None, None, None)
		return out


	def get_matches(self, img, tolerance=None):
		if tolerance is not None:
			#a good start is 0.8
			self.tolerance = tolerance
		if type(img) is str:
			img = cv2.imread(img)
		boxes = fr_dlib.face_locations(img)
		dets = fr_dlib.face_encodings(img, boxes)
		matches = {}
		for box in boxes:
			encodings = list(self.all_encodings.values())
			self.encodings = np.array(encodings, dtype=object)
			for test in dets:
				idx = -1
				for landmark in list(all_encodings.values()):
					idx += 1
					dist = round(float(np.linalg.norm(landmark - test)), 2)
					print(dist)
					tolerance = float(self.tolerance)
					if dist <= tolerance:
						name = list(all_encodings.keys())[idx].split('_')[0]
						matches[dist] = {}
						matches[dist]['idx'] = idx
						matches[dist]['name'] = name
						matches[dist]['dist'] = dist
						matches[dist]['box'] = box
		return matches


	def recognize(self, imgpath):
		if self.det_provider == 'dlib':
			data = self.recognize_dlib(imgpath)
		elif self.det_provider == 'cv2':
			data = self.recognize_cv2(imgpath)
		return data


	def recognize_cv2(self, imgpath):
		out = []
		if type(imgpath) == str:
			img = cv2.imread(imgpath)
		else:
			img = imgpath
		(self.H, self.W) = img.shape[:2]
		minW = 0.1*self.W
		minH = 0.1*self.H
		if self.flip_image == True:
			img = cv2.flip(img, -1)
		gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
		faces = self.faceCascade.detectMultiScale(gray, scaleFactor = 1.2, minNeighbors = 5, minSize = (int(minW), int(minH))) 
		for(x,y,w,h) in faces:
			l, t, r, b = x, y, x+w, y+h
			_id, confidence = self.cv2_recognizer.predict(gray[t:b,l:r])
			if confidence < 100:
				name = self.cv2_known_names[_id]
				confidence = int(f"{format(round(100 - confidence))}")
				o = (name, (l, t, r, b), confidence)
				out.append(o)
		if ptz.track_to_center:
			try:
				self.ptz_track_to_center(img, out[0][1])
			except:
				pass
		return out
		

	def recognize_dlib(self, img, tolerance=None):
		if tolerance is not None:
			#a good start is 0.8
			self.tolerance = tolerance
		matches = self.get_matches(img, self.tolerance)
		out = []
		if matches != {}:
			best = sorted(matches.keys())[0]
			dist = matches[best]['dist']
			confidence = 1 - dist * 100
			c = float(str(confidence).split('-')[1])
			box = matches[best]['box']
			name = matches[best]['name']
			o = name, box, c
			out.append(o)
		if ptz.track_to_center:
			try:
				self.ptz_track_to_center(img, out[0][1])
			except:
				pass
		return out

	def object_detect(self, imgpath):
		if type(imgpath) == str:
			img = cv2.imread(imgpath)
		else:
			img = imgpath
		#img = cv2.resize(fullimg, (300, 300))
		(self.H, self.W) = img.shape[:2]
		blob = cv2.dnn.blobFromImage(img, self.scale, self.detector_input_shape, self.mean, swapRB=True)
		self.net.setInput(blob)
		detections = self.net.forward()
		out = []
		for i in range(0, detections.shape[2]):
			self.confidence = float(detections[0, 0, i, 2])
			idx = int(detections[0, 0, i, 1])
			self.name = self.classes[idx]
			if self.name in self.targets and float(self.confidence) >= float(self.target_confidence):
				#dets = detections[0, 0, i, 3:7] * np.array([self.W, self.H, self.W, self.H])
				dets = detections[0, 0, i, 3:7] * np.array([img.shape[1], img.shape[0], img.shape[1], img.shape[0]])
				l, t, r, b = dets.astype("int")
				l, t, r, b = constrain_box(img, l, t, r, b)
				self.box = (l, t, r, b)
				o = (self.name, self.box, self.confidence)
				out.append(o)
		if ptz.track_to_center:
			try:
				self.ptz_track_to_center(img, out[0][1])
			except:
				pass
		return out

	def yolov3(self, image):
		Width = image.shape[1]
		Height = image.shape[0]
		blob = cv2.dnn.blobFromImage(image, self.yolo_scale, (416,416), (0,0,0), True, crop=False)
		self.yolo_net.setInput(blob)
		outs = self.yolo_net.forward(get_output_layers(self.yolo_net))
		class_ids = []
		confidences = []
		boxes = []
		conf_threshold = 0.5
		nms_threshold = 0.4
		for out in outs:
			for detection in out:
				scores = detection[5:]
				class_id = np.argmax(scores)
				confidence = scores[class_id]
				if confidence > 0.5:
					center_x = int(detection[0] * Width)
					center_y = int(detection[1] * Height)
					w = int(detection[2] * Width)
					h = int(detection[3] * Height)
					x = center_x - w / 2
					y = center_y - h / 2
					class_ids.append(class_id)
					confidences.append(float(confidence))
					boxes.append([x, y, w, h])
			indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
		out = []
		for i in indices:
			box = boxes[i]
			x = box[0]
			y = box[1]
			w = box[2]
			h = box[3]
			box = round(x), round(y), round(x+w), round(y+h)
			name = self.yolo_classes[class_ids[i]]
			confidence  = confidences[i]
			o = (name, box, confidence)
			out.append(o)
		return out
