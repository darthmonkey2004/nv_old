from nv.main.conf import readConf
from PIL import Image, ImageDraw
import numpy as np
import os, os.path
import pickle
import cv2
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np
import sqlite3
import face_recognition
import itertools
from pathlib import Path
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
import keyring

userdir = os.path.expanduser('~')
EXEC_DIR = (userdir + os.path.sep + ".local" + os.path.sep + "lib" + os.path.sep + "python3.6" + os.path.sep + "site-packages" + os.path.sep + "nv" + os.path.sep + "main")
DATA_DIR=(f"{userdir}{os.path.sep}.np{os.path.sep}nv")

def split_4(camera_id, img):# returns a dictionary of an image with camera_id(n) split 4 ways (1,2,3,4). for dvr output, multi-view BNC output.
	out = {}
	full_height, full_width = img.shape[:2]
	width = int(full_width / 2)
	height = int(full_height / 2)
	x1 = 0
	y1 = 0
	h1 = y1 + height
	w1 = x1 + width
	x2 = 0
	y2 = height
	h2 = y2 + height
	w2 = x2 + width
	x3 = width
	y3 = 0
	h3 = y3 + height
	w3 = x3 + width
	x4 = width
	y4 = height
	h4 = y4 + height
	w4 = x4 + width
	tocrop = img.copy()
	img1 = tocrop[y1:h1, x1:w1]
	img2 = tocrop[y2:h2, x2:w2]
	img3 = tocrop[y3:h3, x3:w3]
	img4 = tocrop[y4:h4, x4:w4]
	id1 = (str(camera_id) + ":1")
	id2 = (str(camera_id) + ":2")
	id3 = (str(camera_id) + ":3")
	id4 = (str(camera_id) + ":4")
	out[id1] = img1
	out[id2] = img2
	out[id3] = img3
	out[id4] = img4
	return out


def detector_trainer(xml_path, symmetrical=False, accuracy=5):
	cores = int(subprocess.check_output(['nproc']))
	detector_file_name = (xml_path.split('.')[0] + ".svm")
	options = dlib.simple_object_detector_training_options()
	options.add_left_right_image_flips = symmetrical #(symmetrical = true if face, false for object)
	options.C = int(accuracy) # adjust value on untested images to dial accuracy in
	options.num_threads = cores #(how many cores your processor has, speeds training)
	options.be_verbose = True
	testing_xml_path = (DATA_DIR + os.path.sep + (xml_path.split('.')[0]) + ".xml")
	dlib.train_simple_object_detector(training_xml_path, detector_file_name, options) # set detector_file_name to the name you wish to give to this detector.
	
def sendMail(camera_id, className, fpath):
	subject = "NicVision Alert!"
	body = "A " + className + " was just spotted on camera " + camera_id + "!"
	sender_email = "darthmonkey2004@gmail.com"
	receiver_email = "darthmonkey2004@gmail.com"
	port = 465
	try:
		pw = keyring.get_password("gmail", receiver_email)
	except:
		pw = input("Enter password: ")
	keyring.set_password("gmail", receiver_email, pw)
	message = MIMEMultipart()
	message["From"] = sender_email
	message["To"] = receiver_email
	message["Subject"] = subject
	message["Bcc"] = receiver_email
	message.attach(MIMEText(body, "plain"))
	with open(fpath, "rb") as attachment:
		part = MIMEBase("application", "octet-stream")
		part.set_payload(attachment.read())
	encoders.encode_base64(part)
	part.add_header("Content-Disposition", f"attachment; filename= {fpath}")
	message.attach(part)
	text = message.as_string()
	context = ssl.create_default_context()
	with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
		server.login(receiver_email, pw)
		server.sendmail(receiver_email, receiver_email, text)


def getlocalip():
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	return s.getsockname()[0]


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

def readConfToShell():
	cameras, feeds, ptzs = readConf(SQLDB)
	for cam_id in cameras:
		print (cameras[cam_id])
	#except:
	#		print ("")

def writeConf(cameras, conf='None'):
	if conf == 'None':
		conf = readConf()
	with open(conf, 'wb') as f:
		pickle.dump(cameras, f)

def url_addAuth(user,pw,url):
	chunks = url.split("//")
	chunks[1] = (user + ":" + pw + "@" + chunks[1])
	delimeter = "//"
	string = delimeter.join(chunks)
	print (string)
	return string


def save_face(img, box, name):
	Path(nv.UNKNOWN_FACES_PATH).mkdir(parents=True, exist_ok=True)
	path, dirs, files = next(os.walk(nv.UNKNOWN_FACES_PATH))
	ct = len(files)
	ct = ct + 1
	fname = (nv.UNKNOWN_FACES_PATH + name + "." + str(ct) + ".jpg")
	x, y, w, h = box
	drawn = cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
	cv2.imwrite(fname, drawn)
	

def testCam(src):#A helper function for scan.networkCameras.sh
	try:
		tempcap = cv2.VideoCapture(src)
		ret, img = tempcap.read()
		state = ret
		tempcap.release()
	except:
		state = False
	return state

def readConf(dbfile=None):
	if dbfile == None:
		try:
			dbfile = SQLDB
		except:
			dbfile = input("Enter db file path:")
	CAMERAS = {}
	FEEDS = {}
	PTZS = {}
	data = {}
	conn = sqlite3.connect(dbfile)
	cur = conn.cursor()
	cur.execute("SELECT camera_id, src, feed, ptz FROM cams")
	rows = cur.fetchall()
	for row in rows:
		camera_id, src, feed, ptz = row
		CAMERAS[camera_id] = src
		FEEDS[camera_id] = feed
		PTZS[camera_id] = ptz
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
	import imutils
	import face_recognition
	if type(imgpath) == str:
		img = face_recognition.load_image_file(imgpath)
	else:
		img = imgpath
	img = imutils.resize(img, width=400)
	name = None
	matches = []
	face_location = None
	if img is not None:
		test_face = face_recognition.face_encodings(img)
		test_location = face_recognition.face_locations(img)
		if len(test_face) == 0:
			return (None, None)
		else:
			name = "Unidentified Face"
			result = face_recognition.compare_faces(nv.KNOWN_ENCODINGS, test_face[0])
			if True in result:
				i = result.index(True)
				namelist = list(nv.ALL_FACE_ENCODINGS.keys())
				name = namelist[i]
				splitter = '_'
				name = name.split(splitter)[0]
		if test_location is not None:
			out = (name, test_location[0])
			return (out)
		else:
			return (None, None)

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
			result = face_recognition.compare_faces(nv.KNOWN_ENCODINGS, test_face[0])
			if True in result:
				i = result.index(True)
				names = list(nv.ALL_FACE_ENCODINGS.keys())
				name = names[i]
				splitter = '_'
				name = name.split(splitter)[0]
			return (name, face_location[0])

def recognize_dir(path = None, outfile=False):
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
			result, location = matches
			output[pos] = (result, location)
			cur = (pos, ct)
			print (cur, result)
			if outfile is not False:
				with open(outfile, 'wb') as f:
					pickle.dump(output, f)
				f.close()
	return output
	exit()

def trainFace(name, encoding):
	try:
		all_face_encodings = nv.ALL_FACE_ENCODINGS
		with open(nv.KNOWN_FACES_DB, 'rb') as f:
			all_face_encodings = pickle.load(f)
			print ("Encodings dat file loaded!")
		f.close()
		pos = 0
		for item in list(all_face_encodings.keys()):
			if name in item:
				pos = pos + 1
		ct = pos + 1
		name = (name + "_" + str(ct))
		all_face_encodings[name] = encoding
		with open(nv.KNOWN_FACES_DB, 'wb') as f:
			pickle.dump(all_face_encodings, f)
			print ("Encodings dat file created!")
		f.close()
		return True
	except:
		return False

def face_detect_cv2(imgpath):
	if type(imgpath) == str:
		img = cv2.imread(imgpath)
	else:
		img = imgpath
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)# convert to grayscale
	faces = FD_CASCADE.detectMultiScale(gray, 1.1, 4)#detect faces
	for face in faces:
		x, y, w, h = face
		#cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)#draw rectangle over face on image.
		return (x, y, (x+w), (y+h))

def face_detect(imgpath):
	if type(imgpath) == str:
		img = face_recognition.load_image_file(imgpath)
	else:
		img = imgpath	
	faces = face_recognition.face_locations(img)
	for face in faces:
		return face


def readDbFile(datfile=None):
	ALL_FACE_ENCODINGS = {}
	if datfile == None:
		datfile = nv.KNOWN_FACES_DB
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



def object_detect(img):
	if type(img) == str:
		img = cv2.imread(img)
	det = nv.detector.detector()
	name, box = det.object_detect(img)
	if box is not None:
		return (name, box)

		
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
