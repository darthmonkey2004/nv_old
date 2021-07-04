import os
import nv
import dlib
from correlation_tracker import CorrelationTracker as CT
from trackable_object import TrackableObject
from imutils.video import VideoStream
from imutils.video import FPS
from detector import detector
import numpy as np
import face_recognition
import imutils
import time
import dlib
import cv2
import sys
from PIL import Image

def ensure_dir(directory):
	if not os.path.exists(directory):
        	os.makedirs(directory)

def writeOutImg(name, frame):
	try:
		name, confidence = (name.split('_')[0]), (name.split('_')[1])
	except:
		name, confidence = (name, "N/A")
	path = (nv.DATA_DIR + nv.sep + "objects" + nv.sep + name)
	ensure_dir(path)
	count = (len(os.listdir(path)) + 1)
	fname = (path + nv.sep + str(count) + ".jpg")
	#frame.save(fname)
	cv2.imwrite(fname, frame)

try:
	camera_id = int(sys.argv[1])
except:
	camera_id = int(1)
src = nv.FEEDS[camera_id] 
CLASSES = nv.OBJECTDETECTOR_CLASSES
net = cv2.dnn.readNetFromCaffe(nv.PROTOTXT, nv.MODEL)
vs = cv2.VideoCapture(src)
W = None
H = None
trackers = {}
trackableObjects = {}
totalFrames = 0
totalDown = 0
totalUp = 0
vs = cv2.VideoCapture(src)
output = []
status = "Waiting"
writeout = None
face_cascade = cv2.CascadeClassifier(nv.HAARFILE)
tracker = None
det = detector()
name = None
while True:
	tracker = None
	output = []
	ret, frame = vs.read()
	if ret == False:
		continue
	if totalFrames % nv.SKIP_FRAMES == 0:
		if "face_detection" in nv.METHODS:
			name, box = det.face_detect(frame)
			if box is not None:
				tracker = CT(box, frame)
				output.append(out)
		elif "object_detection" in nv.METHODS:
			name, box = det.object_detect(frame)
			if box is not None:
				tracker = CT(box, frame)
				if name == "person":
					name = "Unrecognized Face"
					recname, recbox = det.recognize(frame)
					if recname is not None:
						name = recname
						box = recface
						tracker = CT(box, frame)
				writeOutImg(name, frame)
				out = (name, box)
				output.append(out)
		elif "face_recognition" in nv.METHODS:
			name, box = det.recognize(frame)
			if box is not None:
				tracker = CT(box, frame)
				output.append(out)


		if tracker is not (None):
			object_id = len(list(trackers.keys()))
			object_id = object_id + 1
			trackers[object_id] = (name, tracker)
			#writeOutImg(text, frame)
			
	else:
		output = []
		to_del = {}
		if len(trackers.keys()) == 0:
			out = (None, None)
			output.append(out)	#if not output found from either tracker or detection methods,
						#then upload null to output to remove stale draw boxes on image feed.
		else:
			for object_id in trackers.keys():
				name, tracker = trackers[object_id]
				name = name.split('_')[0]#parse confidence (from detector) out of string
				age, confidence, rect = tracker.predict(frame)#calulcate age of object
				box = tuple(rect)
				if age > nv.TRACKER_MAX_AGE:# if max age has occured...
					to_del[object_id] = object_id#...flag object for removal
				confidence = (confidence / 10)
				name = (name + "_" + str(confidence))
				#if confidence < nv.OBJECTDETECTOR_CONFIDENCE:
				#	to_del[object_id] = object_id
				out = (name, box)
				output.append(out)
		for object_id in to_del.keys():
			del trackers[object_id]

	totalFrames = totalFrames + 1
	if output != []:
		nv.writeIoFile(camera_id, output)


