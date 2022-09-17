import os
import subprocess
import cv2
import PySimpleGUI as sg
from PIL import Image
from nv.main.detector import detector
d = detector()
import face_recognition
import pickle

userdir = os.path.expanduser('~')
DATA_DIR=(f"{userdir}{os.path.sep}.np{os.path.sep}nv")
KNOWN_FACES_DB=(DATA_DIR + "/nv_known_faces.dat")

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
		pass

	if ret == 'all':
		out = (KNOWN_NAMES, KNOWN_USER_IDS)
	elif ret == 'ids':
		out = KNOWN_USER_IDS
	elif ret == 'names':
		out = KNOWN_USER_NAMES
	elif ret == 'init':
		out = (ALL_FACE_ENCODINGS, KNOWN_NAMES, KNOWN_ENCODINGS, KNOWN_USER_IDS)
	return out

ALL_FACE_ENCODINGS, KNOWN_NAMES, KNOWN_ENCODINGS, KNOWN_USER_IDS = initDatabase('init')



def get_faces(imgpath):
	img = cv2.imread(imgpath)
	img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	fr_faces = face_recognition.face_locations(img2)
	if fr_faces != []:
		return fr_faces
	drec = d.recognize(img2)
	if drec != (None, None, None):
		return drec
	dfaces = d.face_detect(img2)
	if dfaces != (None, None, None):
		return dfaces
	else:
		return None

def train_face(name, encoding):
	try:
		#all_face_encodings = ALL_FACE_ENCODINGS
		with open(KNOWN_FACES_DB, 'rb') as f:
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
		with open(KNOWN_FACES_DB, 'wb') as f:
			pickle.dump(all_face_encodings, f)
			print ("Encodings dat file created!")
		f.close()
		print (f"Face ({name}) added to database!")
		return True
	except Exception as e:
		print (f"Exception in train_face: {e}")
		return False

def rmfile(filepath):
	com = f"rm \"{filepath}\""
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		print(f"Error removing file {filepath}: {ret}")
		return False
	else:
		print ("Ok!")
		return True
	

def train():
	name = 'Unknown'
	path = f"{DATA_DIR}{os.path.sep}Unrecognized Face"
	files = next(os.walk(path))[2]
	for filepath in files:	
		fname = f"{os.path.splitext(filepath)[0]}.png"
		fullpath = f"{path}{os.path.sep}{filepath}"
		faces = get_faces(fullpath)
		if faces is not None:
			pngpath = f"{path}{os.path.sep}{fname}"
			print(pngpath)
			png = Image.open(fullpath)
			newsize = (300,300)
			png2 = png.resize(newsize)
			png2.save(pngpath)
			w, h = png.size
			name = get_user_input(pngpath, w, h, 'Name this face:', name)
			#name = "Matt McClellan"
			img = cv2.imread(fullpath)
			img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
			box = face_recognition.face_locations(img)
			encoding = face_recognition.face_encodings(img, box)
			train_face(name, encoding)
			rmfile(fullpath)
			rmfile(pngpath)
			input("Press a key to continue...")
		else:
			print (f"no face found for {fullpath}")

def get_user_input(src_img, w, h, window_title='User Input', default_text=None):
	if default_text == None:
		default_text = 'Unknown'
	input_box = sg.Input(default_text=default_text, enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)
	input_btn = sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')
	image = sg.Image(src_img, subsample=4, size=(w, h), enable_events=True, key='id_image')
	layout = [[input_box], [input_btn], [image]]
	
	win_w = w + 250
	win_h = h + 240
	print(w, h, win_w, win_h)
	input_window = sg.Window(window_title, layout, size=(win_w, win_h), keep_on_top=True, element_justification='center', finalize=True)
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

if __name__ == "__main__":
	train()
