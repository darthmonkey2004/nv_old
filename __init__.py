# This is the nv package's __init__ file, called on import.
# sets up the nv. resources used in capture.py and process.py, and the /usr/local/bin cli/bash scripts.
#		TODO: Migrate functions to another python file (functions.py),
#			and import in init to speed up import, only grabbing the ones necessary for capture if not processing img.

#This is a work in progress, and I'm no python pro. So of course input, and any suggestions, is amazingly appreciated.
#-Matt
#darthmonkey2004@gmail.com
#NOTE: boxes should be in dlib rectangle format: (l,t,r,b)
from PIL import Image, ImageDraw
import numpy as np
import os.path
import pickle
import cv2
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np

#dlib rectangle objects are (l,t,r,b)
sep = os.path.sep
userdir = os.path.expanduser('~')
EXEC_DIR = (userdir + os.path.sep + ".local" + os.path.sep + "lib" + os.path.sep + "python3.6" + os.path.sep + "site-packages" + os.path.sep + "nv" + os.path.sep + "main")
DATA_DIR=(userdir + os.path.sep + "Nicole" + os.path.sep + "NicVision")
os.chdir(EXEC_DIR)
from nv.main import servodriver as servo
from nv.main import ipptz as ipptz
from nv.main import serve as serve
from nv.main import correlation_tracker as correlation_tracker
from nv.main import trackable_object as trackable_object
from nv.main.capture import VideoCapture
from nv.main import trainer as trainer

def getDaylight():
	import time
	from suntime import Sun
	import datetime
	latitude = 38.21
	longitutde = -98.21
	sun = Sun(latitude, longitutde)
	sunrise = sun.get_sunrise_time()
	sunrise = sunrise.timestamp()
	sunset = sun.get_sunset_time()
	sunset = sunset.timestamp()
	now = time.time()
	if now > sunrise < sunset:
		return "Day"
	else:
		return "Night"

def drawBox(img, data):
	drawn = img#initialize drawn return image with passed image
	#so if this draw function fails, it will still return a current image
	rgb_img = cv2.cvtColor(drawn, cv2.COLOR_BGR2RGB)#convert to RGB for PIL library
	pil_image = Image.fromarray(rgb_img)#create numpy array from RGB
	# Create a Pillow ImageDraw Draw instance to draw with
	draw = ImageDraw.Draw(pil_image)
	if len(data) == 2 and type(data) == tuple:#if data is properly packed, example below
		# ([str(text1), str(text2)], [(box1_left, box1_top, box1_right, box1_bottom), (box2)])
		text_lines, boxes = data#if properly packed, this will pull two list objects out. If not list, the rest will probably fail.
	else:
		out = ("Data not packed correctly: '" + str(data) + "', (is not tuple containing two lists)")
		print (out)
		return out# return error string if not properly packed
	#perform series of checks to determine how much data has been given
	if type(text_lines) != list or type(boxes) != list:# if either item isn't a list...
		out = ("Data not packed correctly: '" + str(data) + "', (is not tuple containing two lists)")
		print (out)
		return out# return error string if not properly packed
	#by now we've filtered the data to ensure it's packed right. So let's unpack.
	pos = -1#initialize counter so first element starts at 0
	towrite = {}#initialize variable to store text_lines and coords. See below.
	for box in boxes:
		pos = pos + 1 #incrementally count upwards through boxes, use for referencing the index of text to include.
		if type(box) == tuple and len(box) == 4:#if data is just one box (dlib rectangle format)... (left, top, right, bottom)
			coords = box[0], box[3]#grab elements 0 and 3 (first and 4th in tuple) as bottom left coords for text
			draw.rectangle(box, outline=GREEN)#draw box on image, I use green for face boxes.
			line = text_lines[pos]#grab corresponding element in text_lines array to use as text for box
			#because we'd have to convert back to np array and would delete the drawing element, and that would take too much time in the loop,
			#we can't draw the text on the image since I'm using cv2 instead of PIL for that. So instead, pack into an array that we'll iterate through shortly.
			towrite[pos] = (line, coords)
		else:#if the below situation occurs, break noisily...and call the ghost busters.
			out = ("Weird, this situation shouldn't have occured. Data got cluster#*$!ed somehow.", str(data))
			print (out)
			return (out)
			exit()
	rgb_img = np.array(pil_image)#convert back to np array
	img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)#convert back to bgr
	drawn = img#update class attribute with so far updated image.
	for pos in towrite:#iterate through our text lines and coords, putting them on the image.
		text, coords = towrite[pos]#unpack from dictionary
		drawn = cv2.putText(img, text, coords, FONT, FONT_SCALE, BLUE, 2, cv2.LINE_AA)#update class attribute with text
	del draw#delete drawing layer, as per PIL documentation.
	return drawn

def writeConfFromShell(conftxt, conf='None'):
	if conf == 'None':
		conf = CONF
	cameras = {}
	with open(conftxt) as f:
		for line in f:
			(key, val) = line.split()
			cameras[int(key)] = val
	f.close()
	writeConf(cameras, conf)
	out=("configuration file updated successfully!")
	print (out)

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
			KNOWN_ENCODINGS = np.array(list(ALL_FACE_ENCODINGS.values()))
		f.close()
		pos = 0
		for testname in all_names:
			testname = testname.split('_')[0]
			if testname not in KNOWN_NAMES:
				pos = pos + 1
				KNOWN_NAMES.append(testname)
				KNOWN_USER_IDS.append(pos)
	except:
		print ("Boobies frighten me.")

	if ret == 'all':
		out = (KNOWN_NAMES, KNOWN_USER_IDS)
	elif ret == 'ids':
		out = KNOWN_USER_IDS
	elif ret == 'names':
		out = KNOWN_USER_NAMES
	elif ret == 'init':
		out = (ALL_FACE_ENCODINGS, KNOWN_NAMES, KNOWN_ENCODINGS, KNOWN_USER_IDS)
	return out

def updateDbFile(name, face_encoding, datfile=None):
	try:
		ALL_FACE_ENCODINGS = {}
		if datfile == None:
			datfile = KNOWN_FACES_DB
		ALL_FACE_ENCODINGS = readDbFile()
		ALL_FACE_ENCODINGS[name] = face_encoding
		with open(datfile, 'wb') as f:
			pickle.dump(ALL_FACE_ENCODINGS, f)
		f.close()
		all_names = list(ALL_FACE_ENCODINGS.keys())
		KNOWN_ENCODINGS = np.array(list(ALL_FACE_ENCODINGS.values()))
		KNOWN_NAMES = []
		KNOWN_USER_IDS = []
		pos = 0
		for testname in all_names:
			testname = testname.split('_')[0]
			if testname not in KNOWN_NAMES:
				pos = pos + 1
				KNOWN_NAMES.append(testname)
				KNOWN_USER_IDS.append(pos)
		return True
	except:
		return False

def readConfToShell(conf='None'):
	if conf == 'None':
		conf = CONF
	try:
		cameras = readConf(conf)
		for cam in cameras:
			print (cameras[cam])
	except:
			print ("")

def writeConf(cameras, conf='None'):
	if conf == 'None':
		conf = CONF
	with open(conf, 'wb') as f:
		pickle.dump(cameras, f)

def url_addAuth(user,pw,url):
	chunks = url.split("//")
	chunks[1] = (user + ":" + pw + "@" + chunks[1])
	delimeter = "//"
	string = delimeter.join(chunks)
	print (string)
	return string

def readIoFile(camera_id):
	id = int(camera_id)
	name = str(IOFILES[id])
	lines = []
	pos = 0
	with open(name, 'rb') as f:
		try:
			data = pickle.load(f)
		except:
			data = []
	f.close()
	return (data)

def testCam(src):#A helper function for scan.networkCameras.sh
	try:
		tempcap = cv2.VideoCapture(src)
		ret, img = tempcap.read()
		state = ret
		tempcap.release()
	except:
		state = False
	return state

def mkIoFiles():
	for camera_id in CAMERAS.keys():
		name = (str(camera_id) + ".io")
		is_tracking = False
		boxes = []
		out = (is_tracking, boxes)
		with open(name, 'wb') as f:
			pickle.dump(out, f)
		f.close()

def writeIoFile(camera_id, outData):
	name = IOFILES[camera_id]
	if outData != []:
		with open(name, 'wb') as f:
			pickle.dump(outData, f)
			f.close()

def readConf():
	CAMERAS = {}
	FEEDS = {}
	PTZS = {}
	with open(CONF, 'rb') as f:
		data = pickle.load(f)
		CAMERAS = data['srcs']
		FEEDS = data['feeds']
		PTZS = data['ptzs']	
		return CAMERAS, FEEDS, PTZS

def addToConf(src, feed, ptz):
	data={}
	cam_id = len(nv.CAMERAS)
	cam_id = cam_id + 1
	CAMERAS[cam_id] = src
	FEEDS[cam_id] = feed
	PTZS[cam_id] = ptz
	data['srcs'] = CAMERAS
	data['feeds'] = FEEDS
	data['ptzs'] = PTZS
	writeConf(data)


def resizeImg(img, scale):
	#print ((img.shape[1]), (img.shape[0]))
	width = int(img.shape[1] * scale / 100)
	height = int(img.shape[0] * scale / 100)
	dsize = (width, height)
	retimg = cv2.resize(img, dsize)
	#print ((retimg.shape[1]), (retimg.shape[0]))
	return retimg

def recognize(imgpath):
	import face_recognition
	img = face_recognition.load_image_file(imgpath)
	img = resizeImg(img, 50)
	name = None
	matches = []
	face_location = None
	if img is not None:
		test_face = face_recognition.face_encodings(img)
		test_location = face_recognition.face_locations(img)
		if len(test_face) == 0:
			out = None
			return out
		else:
			name = "Unidentified Face"
			result = face_recognition.compare_faces(KNOWN_ENCODINGS, test_face[0])
			if True in result:
				i = result.index(True)
				name = KNOWN_NAMES[i]
				splitter = '_'
				name = name.split(splitter)[0]
		if test_location is not None:
			out = (imgpath, name, test_location[0])
			return (out)
		else:
			return None

def recognize_raw(img):
	import face_recognition
	name = None
	matches = []
	face_location = None
	if img is not None:
		test_face = face_recognition.face_encodings(img)
		if len(test_face) == 0:
			out = (None, None)
			return out
		else:
			name = "Unidentified Face"
			face_location = face_recognition.face_locations(img)
			result = face_recognition.compare_faces(KNOWN_ENCODINGS, test_face[0])
			if True in result:
				i = result.index(True)
				names = list(ALL_FACE_ENCODINGS.keys())
				name = names[i]
				splitter = '_'
				name = name.split(splitter)[0]
			return (name, face_location[0])

def recognize_dir(path = None):
	logfile = 'testimages.log'
	import glob
	output = {}
	if path == None:
		path = (nv.DATA_DIR + nv.sep + "training_data")
	os.chdir(path)
	files = os.listdir(path)
	filtered_list = glob.glob('*.jpg')
	pos = 0
	ct = len(filtered_list)
	for file in filtered_list:
		pos = pos + 1
		try:
			matches = recognize(file)
		except:
			matches = None
		if matches is not None:
			filename, result, location = matches
			output[pos] = (filename, result)
			cur = (pos, ct)
			print (cur, result)
			with open(logfile, 'wb') as f:
				pickle.dump(output, f)
			f.close()
	print ("Done!")
	exit()

def face_detect(imgpath):
	img = cv2.imread(imgpath)
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)# convert to grayscale
	faces = nv.FD_CASCADE.detectMultiScale(gray, 1.1, 4)#detect faces
	for face in faces:
		x, y, w, h = face
		cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)#draw rectangle over face on image.
	return faces

def readDbFile(datfile=None):
	ALL_FACE_ENCODINGS = {}
	if datfile == None:
		datfile = KNOWN_FACES_DB
	with open(datfile, 'rb') as f:
		ALL_FACE_ENCODINGS = pickle.load(f)
	f.close()
	return (ALL_FACE_ENCODINGS)

def updateNames():
	pos = 0
	names = []
	ids = []
	all_names = list(ALL_FACE_ENCODINGS.keys())
	for testname in all_names:
		testname = testname.split('_')[0]
		if testname not in names:
			pos = pos + 1
			names.append(testname)
			ids.append(pos)
def rmuser(name):
	ALL_FACE_ENCODINGS = readDbFile(KNOWN_FACES_DB)
	all_names = list(ALL_FACE_ENCODINGS.keys())
	users = {}
	ids = {}
	for testname in all_names:
		test = testname.split('_')[0]
		if name == test:
			del ALL_FACE_ENCODINGS[testname]
	with open(KNOWN_FACES_DB, 'wb') as f:
		pickle.dump(ALL_FACE_ENCODINGS, f)
	f.close()

		
		
def face_detect_raw(img):
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)# convert to grayscale
	faces = FD_CASCADE.detectMultiScale(gray, 1.1, 4)#detect faces
	if len(faces) == 0:
		faces = None
	else:
		for face in faces:
			x, y, w, h = face
			cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)#draw rectangle over face on image.
	return faces


		


sep = os.path.sep
userdir = os.path.expanduser('~')
EXEC_DIR = (userdir + os.path.sep + ".local" + os.path.sep + "lib" + os.path.sep + "python3.6" + os.path.sep + "site-packages" + os.path.sep + "nv" + os.path.sep + "main")
DATA_DIR=(userdir + os.path.sep + "Nicole" + os.path.sep + "NicVision")
KNOWN_FACES_DB=(DATA_DIR + "/nv_known_faces.dat")
CONF=(DATA_DIR + "/nv.conf")
MOTION_CONF=(DATA_DIR + "/nv.motion_feeds.conf")
CAP_EXEC = (EXEC_DIR + os.path.sep + "capture.py")
CAMERAS, FEEDS, PTZ = readConf()
PROTOTXT = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.prototxt')
MODEL = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.caffemodel')
OBJECTDETECTOR_CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
OBJECTDETECTOR_TARGETS = set(["cat", "motorbike", "dog", "person", "car", "bus", "aeroplane", "horse", "truck"])
tod = getDaylight()
if tod == "Day":
	OBJECTDETECTOR_CONFIDENCE = 0.69# found 0.49 to be a good number during night, 0.79 during day
if tod == "Night":
	OBJECTDETECTOR_CONFIDENCE = 0.49# found 0.49 to be a good number during night, 0.79 during day
TRACKER_MAX_AGE = 60
TRAINPATH = (DATA_DIR + os.path.sep + "training_data")
UNKNOWN_FACES_PATH = (DATA_DIR + os.path.sep + "unknown_faces")
LOCALIP = "127.0.0.1"
WEB_PORT = 5000
IMGSRV_PORT = 5555
SKIP_FRAMES = 100
IOFILES = {}
ACTIVE_PROCESS_LIST = CAMERAS
try:
	ALL_FACE_ENCODINGS, KNOWN_NAMES, KNOWN_ENCODINGS, KNOWN_USER_IDS = initDatabase('init')
except:
	ALL_FACE_ENCODINGS = {}
	KNOWN_NAMES = []
	KNOWN_USER_IDS = []
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0 ,0)
RESIZE = 400
METHODS = ['face_recognition', 'object_detection']
HAARFILE = (DATA_DIR + os.path.sep + "haarcascade_frontalface_default.xml")
SMILEFILE = (DATA_DIR + os.path.sep + "haarcascade_smile.xml")
LBOFILE = (DATA_DIR + os.path.sep + "lbpcascade_frontalface.xml")
FD_CASCADE = cv2.CascadeClassifier(HAARFILE)
VIEWER_BORDER_WIDTH = 2
VIEWER_WIDTH = "100%"
VIEWER_HEIGHT = "100%"
for camera_id in FEEDS:
	IOFILES[camera_id] = (DATA_DIR + os.path.sep + str(camera_id) + ".io")
#from nv.main import process as process
