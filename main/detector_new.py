import imutils
import face_recognition
import nv
import numpy as np
import cv2

class detector:
	def __init__(self):
		self.name = None
		self.matches = []
		self.face_location = None
		self.test_location = None
		self.namelist = list(nv.ALL_FACE_ENCODINGS.keys())
		self.box = None
		self.known_encodings = nv.KNOWN_ENCODINGS
		self.classes = nv.OBJECTDETECTOR_CLASSES
		self.net = cv2.dnn.readNetFromCaffe(nv.PROTOTXT, nv.MODEL)
		self.targets = nv.OBJECTDETECTOR_TARGETS
		self.target_confidence = nv.OBJECTDETECTOR_CONFIDENCE
		self.l = 0
		self.t = 0
		self.r = 0
		self.b = 0
		self.H = 0
		self.W = 0

	def face_detect(self, imgpath):
		if type(imgpath) == str:
			img = face_recognition.load_image_file(imgpath)
		else:
			img = imgpath
		img = imutils.resize(img, width=400)
		if img is None:
			return (None, None)
		self.box = face_recognition.face_locations(img)
		if self.box is None:
			return (None, None)
		self.name = "Detected Face"
		try:
			out = (self.name, self.box[0])
		except:
			out = (None, None)
		return out

	def recognize(self, imgpath):
		if type(imgpath) == str:
			img = face_recognition.load_image_file(imgpath)
		else:
			img = imgpath
		img = imutils.resize(img, width=400)
		if img is None:
			return (None, None)
		self.box = face_recognition.face_locations(img)
		if self.box == []:
			return (None, None)
		self.encoding = face_recognition.face_encodings(img, self.box)
		self.result = face_recognition.compare_faces(self.known_encodings, self.encoding)
		if True in self.result:
			i = self.result.index(True)
			name = self.namelist[i]
			splitter = '_'
			self.name = name.split(splitter)[0]
			return (self.name, self.box[0])

	def object_detect(self, imgpath):
		if type(imgpath) == str:
			img = cv2.imread(imgpath)
		else:
			img = imgpath
		(self.H, self.W) = img.shape[:2]
		blob = cv2.dnn.blobFromImage(img, 0.007843, (self.W, self.H), 127.5)
		self.net.setInput(blob)
		detections = self.net.forward()
		for i in np.arange(0, detections.shape[2]):
			self.confidence = detections[0, 0, i, 2]
			idx = int(detections[0, 0, i, 1])
			self.name = self.classes[idx]
			if self.name in self.targets and self.confidence >= self.target_confidence:
				dets = detections[0, 0, i, 3:7] * np.array([self.W, self.H, self.W, self.H])
				(self.l, self.t, self.r, self.b) = dets.astype("int")
				self.box = (self.l, self.t, self.r, self.b)
				self.name = self.name + "_" + str(self.confidence)
				return (self.name, self.box)
			else:
				return (None, None)
