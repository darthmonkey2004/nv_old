import numpy as np
import PySimpleGUI as sg
import face_recognition
import imutils #imutils includes opencv functions
import pickle
import time
import cv2
import os
from nv.main.detector import detector
from np.core.log import np_logger

detector = detector()
detector.tolerance = 0.1
cfp = os.path.dirname(cv2.__file__) + "/data/haarcascade_frontalface_alt2.xml"
fc = cv2.CascadeClassifier(cfp)
nvdir = '/home/monkey/.np/nv'
data = pickle.loads(open(f"{nvdir}/face_enc", "rb").read())
logger = np_logger().log_msg


def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)


def get_user_input(window_title='User Input', default_text=None):
	if default_text == None:
		default_text = 'Unknown'
	input_box = sg.Input(default_text=default_text, enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)
	input_btn = sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')
	layout = [[input_box], [input_btn]]
	input_window = sg.Window(window_title, layout, size=(300, 300), keep_on_top=True, element_justification='center', finalize=True)
	user_input = None
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
	if user_input == None:
		user_input = default_text
	return user_input

def learn_face(image, name):
	global data
	print(f"Learning face...{name}")
	w, h, c = image.shape
	if w > 250 or h > 250:
		image = cv2.resize(image, (250, 250))
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	kEncodings = data["encodings"]
	kNames = data['names']
	boxes = face_recognition.face_locations(rgb,model='hog')
	encodings = face_recognition.face_encodings(rgb, boxes)
	for encoding in encodings:
		kEncodings.append(encoding)
		kNames.append(name)
		data = {"encodings": kEncodings, "names": kNames}
		f = open(f"{nvdir}/face_enc", "wb")
		f.write(pickle.dumps(data))#to open file in write mode


def recognize(img):
	name = None
	if type != np.ndarray:
		image = cv2.imread(img)
	else:
		image = img
	if image is None:
		return None, None
	h, w, c = image.shape
	if w > h:
		r = w / 640
		nw = 640
		nh = int(h / r)
	elif h > w:
		r = h / 640
		nh = 640
		nw = int(w / r)
	else:
		nw = 640
		nh = 640
	#image = cv2.resize(image, (nw, nh))
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	faces = None
	
	try:
		n, faces, confidence = detector.face_detect(image)[0]
	except:
		n, face, confidence = None, None, None
	if faces is not None:
		if type(faces) == tuple:
			faces = [faces]
		encodings = face_recognition.face_encodings(rgb)
		names = []
		for encoding in encodings:
			matches = face_recognition.compare_faces(data["encodings"], encoding)
			name = "Unknown"
			if True in matches:
				matchedIdxs = [i for (i, b) in enumerate(matches) if b]
				count = {}
				for i in matchedIdxs:
					name = data["names"][i]
					count[name] = count.get(name, 0) + 1
					name = max(count, key=count.get)
					names.append(name)
					for box, name in zip(faces, names):
						x, y, w, h = box
						cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
						cv2.putText(image, name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
			if name == 'Unknown':
				name = get_user_input("Who is this?")
				learn_face(image, name)
			print (f"I see {name}!")
	return (name, image)


if __name__ == "__main__":
	import sys
	cv2.namedWindow("Viewer", cv2.WINDOW_NORMAL)
	cv2.resizeWindow("Viewer", 640, 480)
	try:
		target = sys.argv[1]
	except:
		target = None
		exit()
	if os.path.exists(target):
		if os.path.isdir(target):
			os.chdir(target)
			files = next(os.walk(target))[2]
		elif os.path.isfile(target):
			path = os.path.dirname(target)
			os.chdir(path)
			files = [target]
	
	for f in files:
		time.sleep(0.5)
		filepath = os.path.realpath(f)
		name, img = recognize(filepath)
		if img is not None:
			h, w, c = img.shape
			if w > h:
				r = 640 / h
				nh = 640
				nw = int(w * r)
			elif h > w:
				r = 640 / w
				nw = 640
				nh = int(h * r)
			else:
				nw = 640
				nh = 640
			#img = cv2.resize(img, (nw,nh))
			cv2.imshow("Viewer", img)
			if cv2.waitKey(1) == ord('q'):
				break


		
