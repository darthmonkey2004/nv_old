# This is the nv package's __init__ file, called on import.
# sets up the nv. resources used in capture.py and process.py, and the /usr/local/bin cli/bash scripts.
#		TODO: Migrate functions to another python file (functions.py),
#			and import in init to speed up import, only grabbing the ones necessary for capture if not processing img.

#This is a work in progress, and I'm no python pro. So of course input, and any suggestions, is amazingly appreciated.
#-Matt
#darthmonkey2004@gmail.com
#NOTE: boxes should be in dlib rectangle format: (l,t,r,b)
#TODO: create add single camera function
#TODO: create mkdataset_fromCamera and mkdataset_fromImage functions that will aquire name and properly save image to 'train_data' directory
#TODO: create capture class that utilizes cv2, imagezmq, and possibly imutils captures as a standardized class
from PIL import Image, ImageDraw
import numpy as np
import os.path
import pickle
import cv2
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np
import sqlite3
import face_recognition

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
from nv.main import capture as cap
from nv.main import trainer as trainer
from nv.main import detector as detector
from nv.main.functions import getDaylight as getDaylight
from nv.main.functions import drawBox as drawBox
from nv.main.functions import writeConfFromShell as writeConfFromShell
from nv.main.functions import initDatabase as initDatabase
from nv.main.functions import updateDbFile as updateDbFile
from nv.main.functions import readConfToShell as readConfToShell
from nv.main.functions import writeConf as writeConf
from nv.main.functions import url_addAuth as url_addAuth
from nv.main.functions import readIoFile as readIoFile
from nv.main.functions import testCam as testCam
from nv.main.functions import mkIoFiles as mkIoFiles
from nv.main.functions import writeIoFile as writeIoFile
from nv.main.functions import readConf as readConf
from nv.main.functions import addToConf as addToConf
from nv.main.functions import resizeImg as resizeImg
from nv.main.functions import recognize as recognize
from nv.main.functions import recognize_raw as recognize_raw
from nv.main.functions import recognize_dir as recognize_dir
from nv.main.functions import face_detect_cv2 as face_detect_cv2
from nv.main.functions import face_detect as face_detect
from nv.main.functions import readDbFile as readDbFile
from nv.main.functions import updateNames as updateNames
from nv.main.functions import rmuser as rmuser
from nv.main.functions import face_detect_raw as face_detect_raw


		


sep = os.path.sep
userdir = os.path.expanduser('~')
EXEC_DIR = (userdir + os.path.sep + ".local" + os.path.sep + "lib" + os.path.sep + "python3.6" + os.path.sep + "site-packages" + os.path.sep + "nv" + os.path.sep + "main")
DATA_DIR=(userdir + os.path.sep + "Nicole" + os.path.sep + "NicVision")
KNOWN_FACES_DB=(DATA_DIR + "/nv_known_faces.dat")
#CONF=(DATA_DIR + "/nv.conf")
#MOTION_CONF=(DATA_DIR + "/nv.motion_feeds.conf")
CAP_EXEC = (EXEC_DIR + os.path.sep + "capture.py")
PROTOTXT = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.prototxt')
MODEL = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.caffemodel')
SQLDB = (EXEC_DIR + os.path.sep + 'nv.db')
CAMERAS = {}
FEEDS = {}
PTZS = {}
conn = sqlite3.connect(SQLDB)
cur = conn.cursor()
cur.execute("SELECT camera_id, src, feed, ptz FROM cams")
rows = cur.fetchall()
for row in rows:
	camera_id, src, feed, ptz = row
	CAMERAS[camera_id] = src
	FEEDS[camera_id] = feed
	PTZS[camera_id] = ptz
OBJECTDETECTOR_CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
OBJECTDETECTOR_TARGETS = set(["cat", "motorbike", "dog", "person", "car", "horse", "truck"])
tod = getDaylight()
#if tod == "Day":
#	OBJECTDETECTOR_CONFIDENCE = 0.69# found 0.49 to be a good number during night, 0.79 during day
#if tod == "Night":
#	OBJECTDETECTOR_CONFIDENCE = 0.49# found 0.49 to be a good number during night, 0.79 during day
OBJECTDETECTOR_CONFIDENCE = 0.75
TRACKER_MAX_AGE = 30
TRAINPATH = (DATA_DIR + os.path.sep + "training_data")
UNKNOWN_FACES_PATH = (DATA_DIR + os.path.sep + "unknown_faces")
LOCALIP = "127.0.0.1"
WEB_PORT = 5000
IMGSRV_PORT = 5555
SKIP_FRAMES = 30
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
METHODS = ['face_recgnition']
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
