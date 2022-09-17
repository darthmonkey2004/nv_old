from imutils import paths #imutils includes opencv functions
import face_recognition
import pickle
import cv2
import os
import subprocess
import imutils

nvdir = '/home/monkey/.np/nv'
path = f"{nvdir}/dataset"
com = f"find \"{path}\" -name \"*.jpg\""
images = subprocess.check_output(com, shell=True).decode().strip().split("\n")

imagePath = list(paths.list_images(path))
kEncodings = []
kNames = []
l = len(images)
pos = -1
for (i, ip) in enumerate(imagePath):
	pos += 1
	name = ip.split(os.path.sep)[-2]
	image = cv2.imread(ip)
	w, h, c = image.shape
	if w > 250 or h > 250:
		image = imutils.resize(image, width=250)
	print (f"Name: {name} ({pos}/{l})")
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	boxes = face_recognition.face_locations(rgb,model='hog')
	encodings = face_recognition.face_encodings(rgb, boxes)
	for encoding in encodings:
		kEncodings.append(encoding)
		kNames.append(name)
		data = {"encodings": kEncodings, "names": kNames}
		f = open(f"{nvdir}/face_enc", "wb")
		f.write(pickle.dumps(data))#to open file in write mode
		f.close()#to close file
