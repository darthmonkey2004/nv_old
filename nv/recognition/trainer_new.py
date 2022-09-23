from random import randint as random
from PIL import Image
import subprocess
import cv2
import numpy as np
import os
from nv.main.conf import read_opts
import PySimpleGUI as sg
opts = read_opts(0)
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(opts['detector']['fd_cv2']['face_cascade']);


def scale(size):
	w, h = size
	if w > h:
		r = 640 / w
		nw = 640
		nh = h * r
	elif w < h:
		r = 640 / h
		nh = 640
		nw = w * r
	else:
		nw = 640
		nh = 640
	newsize = (int(nw), int(nh))
	return newsize



def get_user_input(img_file, window_title='User Input', default_text=None, names=None):
	if names is None:
		names = []
	png = Image.open(img_file)
	fname = f"{os.path.splitext(img_file)[0]}.png"
	print(fname)
	newsize = scale(png.size)
	png.resize(newsize)
	png.save(fname)
	w, h = newsize
	if default_text == None:
		default_text = 'Unknown'
	input_box = [[sg.Listbox(values=names, size=(30, 5), change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key='-SET_NAME-'), sg.Input(default_text=default_text, enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)]]
	input_btn = [[sg.Button(button_text='Skip', auto_size_button=True, pad=(1, 1), key='-SKIP-'), sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')]]
	image = [sg.Image(fname, subsample=4, size=(w, h), enable_events=True, key='id_image')]
	layout = [input_box, input_btn, image]
	win_w = w + 100
	win_h = h + 100
	input_window = sg.Window(window_title, layout, size=(win_w, win_h), location=(0, 1400), keep_on_top=True, element_justification='center', finalize=True)
	user_input = None
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
		elif event == '-SET_NAME-':
			user_input = values[event].pop()
			input_window['-USER_INPUT-'].update(user_input)
		elif event == '-SKIP-':
			user_input = ''
			input_window.close()		
	if user_input == None:
		user_input = default_text
	return user_input


def get_color():
	#gets randomized color for bounding box
	red = (255, 0, 0)
	orange = (255, 127.5, 0)
	yellow = (255, 255, 0)
	green = (0, 255, 0)
	blue = (0, 255, 255)
	indigo = (0, 0, 255)
	violet = (255, 0, 255)
	colors = [red, orange, yellow, green, blue, indigo, violet]
	color_idx = random(1,7) - 1
	return colors[color_idx]


def train():
	colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
	path = opts['detector']['fr_cv2']['dataset']
	faces = []
	ids = []
	names = []
	pos = 0
	com = f"find \"{path}\" -name \"*.jpg\""
	image_files = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	ct = len(image_files)
	for filepath in image_files:
		print (f"Progress: {pos}/{ct}...")
		pos += 1
		name = os.path.basename(os.path.dirname(filepath)).replace('_', ' ')
		img = cv2.imread(filepath)
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		detections = detector.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=8, minSize=(66, 66))
		if len(detections) > 1:
			print("found more than one face. Getting user input...")
			for det in detections:
				x, y, w, h = det
				color = get_color()
				img = cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
				print(w, h)
				cv2.imwrite('temp.jpg', img)
				tname = get_user_input('temp.jpg', 'Name this face:', name, names)
				if tname == '' or tname == 'None':
					print("No user input provided! Skipping...")
					pass
				else:
					name = tname
					if name not in names:
						_id = len(names) + 1
						names.append(name)
						recognizer.setLabelInfo(_id, name)
					else:
						_id = names.index(name)
					ids.append(_id)
					faces.append(gray[y:y+h,x:x+w])
		else:
			print("Single face, got name from path")
			try:
				notempty = any(detections)
			except Exception as e:
				notempty = True
			if notempty:
				x, y, w, h = detections[0]
				print(w, h)
				if name not in names:
					_id = len(names) + 1
					recognizer.setLabelInfo(_id, name)
					names.append(name)
					ids.append(_id)
					faces.append(gray[y:y+h,x:x+w])
				else:
					_id = names.index(name)
					ids.append(_id)
					faces.append(gray[y:y+h,x:x+w])
			else:
				print("No face found in image!")
	recognizer.train(faces, np.array(ids))
	recognizer.save('new_testfr_trained.yml')

if __name__ == "__main__":
	train()
