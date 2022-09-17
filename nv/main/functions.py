from getpass import getpass
import numpy as np
import os
import pickle
import cv2
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
	body = f"A {className} was just spotted on camera {camera_id}!"
	sender_email = "darthmonkey2004@gmail.com"
	receiver_email = "darthmonkey2004@gmail.com"
	port = 465
	pw = keyring.get_password("gmail", receiver_email)
	if pw is None:
		pw = getpass("Enter Password: ")
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

def fr_dlib_updatedb(name, face_encoding, datfile=None):
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


def testCam(src):#A helper function for scan.networkCameras.sh
	try:
		tempcap = cv2.VideoCapture(src)
		ret, img = tempcap.read()
		state = ret
		tempcap.release()
	except:
		state = False
	return state


def scale(img, scale):
	#print ((img.shape[1]), (img.shape[0]))
	width = int(img.shape[1] * scale / 100)
	height = int(img.shape[0] * scale / 100)
	dsize = (width, height)
	retimg = cv2.resize(img, dsize)
	#print ((retimg.shape[1]), (retimg.shape[0]))
	return retimg


