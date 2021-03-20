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
from nv.main import capture as capture
from nv.main import correlation_tracker as correlation_tracker
from correlation_tracker import CorrelationTracker as CT
#TODO: fix serve and trainer to run with if __name__ == "__main__" block to allow not-execution import
#from nv.main import serve as serve
from nv.main import trackable_object as trackable_object
#from nv.main import trainer as trainer
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

#helper function for shell usage with nv-record
#TODO: Fix me, frame rate not correct, plays slow. More GD Homework....=( (variable bitrate?)
def record(src="rtsp://192.168.2.10/mpeg4cif", outfile="nv.capture.avi"):
	cap = cv2.VideoCapture(src)
	frame_width = int(cap.get(3))
	frame_height = int(cap.get(4))
	out = cv2.VideoWriter(outfile, cv2.VideoWriter_fourcc('M','J','P','G'), 10, (frame_width,frame_height))
	while True:
		ret, img = cap.read()
		if ret:
			out.write(img)
			title = ("Recording (" + str(src) + ")...")
			cv2.imshow('Recording', img)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
	out.release()
	cap.release()
	exit()

#TODO: this doesn't work yet, but the draw code in capture.py does. Adapt this to that, and re-point the resource to the nv package
#def drawBox(img, draw_data):
#	text, box = draw_data
#	rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#	pil_image = Image.fromarray(rgb_img)
#	# Create a Pillow ImageDraw Draw instance to draw with
#	draw = ImageDraw.Draw(pil_image)
#	if len(box) == 4:
#		#print (left, top, right, bottom)
#		draw.rectangle(box, outline=GREEN)#draw box on image
#	else:
#		for rect in box:#iterate through boxes if more than one provided
#		#print (left, top, right, bottom)
#			draw.rectangle(rect, outline=GREEN)#draw box on image#draw box on image
#	rgb_img = np.array(pil_image)
#	del draw
#	img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
#	return img

def resize(img):
	width = int(img.shape[1])
	height = int(img.shape[0])
	if width > 640 and height > 480:
		dim = (640, 480)
		img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
	return img


def writeConfFromShell(conftxt, conf='None'):
	if conf == 'None':
		conf = getConfPath()
	cameras = {}
	with open(conftxt) as f:
		for line in f:
			(key, val) = line.split()
			cameras[int(key)] = val
	f.close()
	writeConf(cameras, conf)
	out=("configuration file updated successfully!")
	print (out)

def readDbFile(datfile):
	with open(datfile, 'rb') as f:
		all_face_encodings = pickle.load(f)
	return (all_face_encodings)

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
	cameras = readConf()
	for camera_id in cameras.keys():
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

def readConf(conf='None'):
	if conf == 'None':
		conf = CONF
	try:
		with open(conf, 'rb') as f:
			cameras = pickle.load(f)
	except:
		cameras = {}
		with open(conf, 'wb') as f:
			pickle.dump(cameras, f)
	return cameras



sep = os.path.sep
userdir = os.path.expanduser('~')
EXEC_DIR = (userdir + os.path.sep + ".local" + os.path.sep + "lib" + os.path.sep + "python3.6" + os.path.sep + "site-packages" + os.path.sep + "nv" + os.path.sep + "main")
DATA_DIR=(userdir + os.path.sep + "Nicole" + os.path.sep + "NicVision")
KNOWN_FACES_DB=(DATA_DIR + "/nv_known_faces.dat")
CONF=(DATA_DIR + "/nv.conf")
CAP_EXEC = (EXEC_DIR + os.path.sep + "capture.py")
CAMERAS = readConf(CONF)
PROTOTXT = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.prototxt')
MODEL = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.caffemodel')
OBJECTDETECTOR_CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
OBJECTDETECTOR_TARGETS = set(["dog", "person", "car", "truck"])
OBJECTDETECTOR_CONFIDENCE = 0.79# found 0.45 to be a good number during night, 0.8 during day
TRACKER_MAX_AGE = 30
TRAINPATH = (DATA_DIR + os.path.sep + "training_data")
LOCALIP = "127.0.0.1"
WEB_PORT = 5000
IMGSRV_PORT = 5555
SKIP_FRAMES = 30
IOFILES = {}
ACTIVE_PROCESS_LIST = CAMERAS
ALL_FACE_ENCODINGS = readDbFile(KNOWN_FACES_DB)
KNOWN_NAMES = list(ALL_FACE_ENCODINGS.keys())
KNOWN_ENCODINGS = np.array(list(ALL_FACE_ENCODINGS.values()))
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0 ,0)
FACE_CASCADE = (DATA_DIR + os.path.sep + "lbpcascade_frontalface.xml")
RESIZE = 400
METHODS = ['face_recognition', 'object_detection']
haarfile = (DATA_DIR + os.path.sep + "haarcascade_frontalface_default.xml")
FACEDETECT_CASCADE = cv2.CascadeClassifier(haarfile)
VIEWER_BORDER_WIDTH = 2
VIEWER_WIDTH = "100%"
VIEWER_HEIGHT = "100%"
for camera_id in CAMERAS:
	IOFILES[camera_id] = (DATA_DIR + os.path.sep + str(camera_id) + ".io")
#from nv.main import process as process
