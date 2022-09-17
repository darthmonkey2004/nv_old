# This is the nv package's __init__ file, called on import.
# sets up the nv. resources used in capture.py and process.py, and the /usr/local/bin cli/bash scripts.
#		TODO: Migrate functions to another python file (functions.py),
#			and import in init to speed up import, only grabbing the ones necessary for capture if not processing img.

#This is a work in progress, and I'm no python pro. So of course input, and any suggestions, is amazingly appreciated.
#-Matt
#darthmonkey2004@gmail.com
#NOTE: boxes should be in dlib rectangle format: (l,t,r,b)
#TODO: create add single camera function
#TODO: Modify serve.py to accomodate imagezmq
#dlib rectangle objects are (l,t,r,b)
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
#from nv.main import serve as serve
from nv.main.functions import writeConfFromShell as writeConfFromShell
from nv.main.functions import updateDbFile as updateDbFile
from nv.main.functions import readConfToShell as readConfToShell
from nv.main.functions import writeConf as writeConf
from nv.main.functions import url_addAuth as url_addAuth
from nv.main.functions import testCam as testCam
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
from nv.main.functions import trainFace as trainFace
from nv.main.functions import object_detect as object_detect
from nv.main.functions import save_face as save_face
from nv.main.functions import sendMail as email
from nv.main.functions import detector_trainer as detector_trainer
from nv.main.conf import readConf, writeConf, nv_logger
from nv.main.mkhtml import mkhtml
log = nv_logger().log_msg
sep = os.path.sep
userdir = os.path.expanduser('~')
EXEC_DIR = (userdir + os.path.sep + ".local" + os.path.sep + "lib" + os.path.sep + "python3.6" + os.path.sep + "site-packages" + os.path.sep + "nv" + os.path.sep + "main")
DATA_DIR=(f"{userdir}{os.path.sep}.np{os.path.sep}nv")
#KNOWN_FACES_DB=(DATA_DIR + "/nv_known_faces.dat")
CAP_EXEC = (EXEC_DIR + os.path.sep + "capture.py")
PROTOTXT = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.prototxt')
MODEL = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.caffemodel')
SQLDB = (DATA_DIR + os.path.sep + 'nv.db')
CAMERAS = {}
FEEDS = {}
PTZS = {}
LOCALIP = "127.0.0.1"
WEB_PORT = 5000
IMGSRV_PORT = 5555
SKIP_FRAMES = 30
IOFILES = {}
ACTIVE_PROCESS_LIST = CAMERAS

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0 ,0)
RESIZE = 400
METHODS = ['object_detection']
TRACKER_TYPES = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'CSRT']
HAARFILE = (DATA_DIR + os.path.sep + "haarcascade_frontalface_default.xml")
SMILEFILE = (DATA_DIR + os.path.sep + "haarcascade_smile.xml")
LBOFILE = (DATA_DIR + os.path.sep + "lbpcascade_frontalface.xml")
FD_CASCADE = cv2.CascadeClassifier(HAARFILE)
VIEWER_BORDER_WIDTH = 2
VIEWER_WIDTH = "100%"
VIEWER_HEIGHT = "100%"
#(CV2_MAJOR_VERSION, CV2_MINOR_VERSION, CV2_SUBMINOR_VERSION) = (cv2.__version__).split('.')
#for camera_id in FEEDS:
#	IOFILES[camera_id] = (DATA_DIR + os.path.sep + str(camera_id) + ".io")
from nv.main import process as process
