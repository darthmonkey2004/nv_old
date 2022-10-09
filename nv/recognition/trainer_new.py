from random import randint as random
from PIL import Image
import subprocess
import cv2
import numpy as np
import os
from nv.main.conf import read_opts
from nv.utils.utils import calculate_scale, get_user_input, get_color
opts = read_opts(0)
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(opts['detector']['fd_cv2']['face_cascade']);


def train():
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
