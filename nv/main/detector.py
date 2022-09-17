from nv.main.conf import read_opts, write_opts, init_opts
import pickle
import datetime
from suntime import Sun, SunTimeException
import os
import imutils
import face_recognition
import numpy as np
import cv2
from nv.main.log import nv_logger
from nv.main.conf import readConf
import sys, traceback

userdir = os.path.expanduser('~')
DATA_DIR=(f"{userdir}{os.path.sep}.np{os.path.sep}nv")
KNOWN_FACES_DB=(DATA_DIR + "/nv_known_faces.dat")


def initDatabase(ret='all', datfile=None):
	ALL_FACE_ENCODINGS = {}
	KNOWN_ENCODINGS = []
	all_names = []
	KNOWN_NAMES = []
	KNOWN_USER_IDS = []
	if datfile == None:
		datfile = KNOWN_FACES_DB
	try:
		with open(datfile, 'rb') as f:
			ALL_FACE_ENCODINGS = pickle.load(f)
			all_names = list(ALL_FACE_ENCODINGS.keys())
			KNOWN_ENCODINGS = np.array(list(ALL_FACE_ENCODINGS.values()), dtype=object)
		f.close()
		pos = 0
		for testname in all_names:
			testname = testname.split('_')[0]
			if testname not in KNOWN_NAMES:
				pos = pos + 1
				KNOWN_NAMES.append(testname)
				KNOWN_USER_IDS.append(pos)
	except:
		pass

	if ret == 'all':
		out = (KNOWN_NAMES, KNOWN_USER_IDS)
	elif ret == 'ids':
		out = KNOWN_USER_IDS
	elif ret == 'names':
		out = KNOWN_USER_NAMES
	elif ret == 'init':
		out = (ALL_FACE_ENCODINGS, KNOWN_NAMES, KNOWN_ENCODINGS, KNOWN_USER_IDS)
	return out

ALL_FACE_ENCODINGS, KNOWN_NAMES, KNOWN_ENCODINGS, KNOWN_USER_IDS = initDatabase('init')


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
		self.det_provider = opts['detector']['provider']
		self.name = None
		self.matches = []
		self.face_location = None
		self.test_location = None
		self.namelist = list(ALL_FACE_ENCODINGS.keys())
		self.box = None
		self.known_encodings = KNOWN_ENCODINGS
		self.classes = opts['detector']['object_detector']['classes']
		self.net = cv2.dnn.readNetFromCaffe(opts['detector']['object_detector']['prototxt'], opts['detector']['object_detector']['model'])
		self.targets = opts['detector']['object_detector']['targets']
		self.target_confidence = opts['detector']['object_detector']['confidence']
		self.l = 0
		self.t = 0
		self.r = 0
		self.b = 0
		self.H = opts['H']
		self.W = opts['W']
		self.tolerance = opts['detector']['fr']['tolerance']
		self.model = opts['detector']['fr']['model']
		self.mean = (127.5, 127.5, 127.5)
		self.scale = 0.007843
		self.detector_input_shape = (300, 300)
		self.cv2_recognizer = cv2.face.LBPHFaceRecognizer_create()
		#self.cv2_detector = opts['cv2_detector']
		self.faceCascade = cv2.CascadeClassifier(opts['detector']['fd_cv2']['face_cascade']);
		self.font = cv2.FONT_HERSHEY_SIMPLEX
		cv2_fr_trained = opts['detector']['fr_cv2']['dbpath']
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
		return out


	def face_detect_dlib(self, imgpath):
		if type(imgpath) == str:
			img = face_recognition.load_image_file(imgpath)
		else:
			img = imgpath
		img = imutils.resize(img, width=400)
		if img is None:
			return (None, None, None)
		self.box = face_recognition.face_locations(img)
		if self.box is None:
			return (None, None, None)
		self.name = "Detected Face"
		try:
			out = (self.name, self.box[0], None)
		except:
			out = (None, None, None)
		return out

	def recognize(self, imgpath):
		if self.det_provider == 'dlib':
			data = self.recognize_dlib(imgpath)
		elif self.det_provider == 'cv2':
			data = self.recognize_cv2(imgpath)
		return data


	def recognize_cv2(self, imgpath):
		out = []
		if type(imgpath) == str:
			#img = face_recognition.load_image_file(imgpath)
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
		return out
		
	def recognize_dlib(self, imgpath):
		if type(imgpath) == str:
			#img = face_recognition.load_image_file(imgpath)
			img = cv2.imread(imgpath)
		else:
			img = imgpath
		img = imutils.resize(img, width=400)
		if img is None:
			return (None, None, None)
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		self.box = face_recognition.face_locations(img,model=self.model)
		if self.box == []:
			return (None, None, None)
		self.encoding = face_recognition.face_encodings(img, self.box)
		log(f"Tolerance:{self.tolerance}", 'info')
		self.result = face_recognition.compare_faces(self.known_encodings, self.encoding, self.tolerance)
		if True in self.result:
			i = self.result.index(True)
			name = self.namelist[i]
			splitter = '_'
			self.name = name.split(splitter)[0]
			t, r, b, l = self.box[0]
			box = (l, t, r, b)
			#return tolerance in lieu of confidence rating
			return [(self.name, box, self.tolerance)]

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
		for i in np.arange(0, detections.shape[2]):
			self.confidence = detections[0, 0, i, 2]
			idx = int(detections[0, 0, i, 1])
			self.name = self.classes[idx]
			if self.name in self.targets and self.confidence >= self.target_confidence:
				#dets = detections[0, 0, i, 3:7] * np.array([self.W, self.H, self.W, self.H])
				dets = detections[0, 0, i, 3:7] * np.array([img.shape[1], img.shape[0], img.shape[1], img.shape[0]])
				(self.l, self.t, self.r, self.b) = dets.astype("int")
				self.box = (self.l, self.t, self.r, self.b)
				o = (self.name, self.box, self.confidence)
				out.append(o)
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
