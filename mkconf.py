KNOWN_FACES_DB=(DATA_DIR + "/nv_known_faces.dat")
PROTOTXT = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.prototxt')
MODEL = (DATA_DIR + os.path.sep + 'MobileNetSSD_deploy.caffemodel')
SQLDB = (EXEC_DIR + os.path.sep + 'nv.db')
try:
	conn = sqlite3.connect(SQLDB)
	cur = conn.cursor()
	cur.execute("SELECT camera_id, src, feed, ptz FROM cams")
	rows = cur.fetchall()
	for row in rows:
		camera_id, src, feed, ptz = row
		CAMERAS[camera_id] = src
		FEEDS[camera_id] = feed
		PTZS[camera_id] = ptz
except:
	CAMERAS = {}
	FEEDS = {}
	PTZS = {}
OBJECTDETECTOR_CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
OBJECTDETECTOR_TARGETS = set(["cat", "motorbike", "dog", "person", "car", "horse", "truck"])
tod = getDaylight()
try:
	if tod == "Day":
		OBJECTDETECTOR_CONFIDENCE = OBJECTDETECTOR_CONFIDENCE_LIGHT # found 0.49 to be a good number during night, 0.79 during day
	if tod == "Night":
		OBJECTDETECTOR_CONFIDENCE = OBJECTDETECTOR_CONFIDENCE_DARK # found 0.49 to be a good number during night, 0.79 during day
except:
	OBJECTDETECTOR_CONFIDENCE_LIGHT = 0.79
	OBJECTDETECTOR_CONFIDENCE_DARK = 0.49
	if tod == "Day":
		OBJECTDETECTOR_CONFIDENCE = OBJECTDETECTOR_CONFIDENCE_LIGHT # found 0.49 to be a good number during night, 0.79 during day
	if tod == "Night":
		OBJECTDETECTOR_CONFIDENCE = OBJECTDETECTOR_CONFIDENCE_DARK # found 0.49 to be a good number during night, 0.79 during day

TRACKER_MAX_AGE = 30
TRAINPATH = (DATA_DIR + os.path.sep + "training_data")
UNKNOWN_FACES_PATH = (DATA_DIR + os.path.sep + "unknown_faces")
LOCALIP = "127.0.0.1"
WEB_PORT = 5000
IMGSRV_PORT = 5555
SKIP_FRAMES = 30
IOFILES = {}
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0 ,0)
METHODS = ['face_recgnition']
HAARFILE = (DATA_DIR + os.path.sep + "haarcascade_frontalface_default.xml")
#TODO: Figure out LBO
LBOFILE = (DATA_DIR + os.path.sep + "lbpcascade_frontalface.xml")
data['KNOWN_FACES_DB'] = KNOWN_FACES_DB
data['PROTOTXT'] = PROTOTXT
data['MODEL'] = MODEL
data['SQLDB'] = SQLDB
data['CAMERAS'] = CAMERAS
data['FEEDS'] = FEEDS
data['PTZS'] = PTZS
data['OBJECTDETECTOR_CLASSES'] = OBJECTDETECTOR_CLASSES
data['OBJECTDETECTOR_TARGETS'] = OBJECTDETECTOR_TARGETS
data['OBJECTDETECTOR_CONFIDENCE_LIGHT'] = OBJECTDETECTOR_CONFIDENCE_LIGHT
data['OBJECTDETECTOR_CONFIDENCE_DARK'] = OBJECTDETECTOR_CONFIDENCE_DARK
data['OBJECTDETECTOR_CONFIDENCE'] = OBJECTDETECTOR_CONFIDENCE
data['TRACKER_MAX_AGE'] = TRACKER_MAX_AGE
data['TRAINPATH'] = TRAINPATH
data['UNKNOWN_FACES_PATH'] = UNKNOWN_FACES_PATH
data['LOCALIP'] = LOCALIP
data['WEB_PORT'] = WEB_PORT
data['IMGSRV_PORT'] = IMGSRV_PORT
data['SKIP_FRAMES'] = SKIP_FRAMES
data['IOFILES'] = IOFILES
data['FONT'] = FONT
data['FONT_SCALE'] = FONT_SCALE
data['RED'] = RED
data['GREEN'] = GREEN
data['BLUE'] = BLUE
data['METHODS'] = METHODS
data['HAARFILE'] = HAARFILE
data['LBOFILE'] = LBOFILE
with open(conf, "wb") as f:
pickle.dump(data, f)
f.close()
print ('init file created!')
