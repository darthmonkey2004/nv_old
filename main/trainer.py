import cv2
import os
import face_recognition
import pickle
import glob
import nv

def resizeImg(img, scale):
	#print ((img.shape[1]), (img.shape[0]))
	width = int(img.shape[1] * scale / 100)
	height = int(img.shape[0] * scale / 100)
	dsize = (width, height)
	retimg = cv2.resize(img, dsize)
	#print ((retimg.shape[1]), (retimg.shape[0]))
	return retimg


def train(path = None):
	try:
		with open(nv.KNOWN_FACES_DB, 'rb') as f:
			all_face_encodings = pickle.load(f)
			print ("Encodings dat file loaded!")
		f.close()
	except:
		all_face_encodings = {}
	if path == None:
		path = (nv.DATA_DIR + nv.sep + "training_data")
	os.chdir(path)
	print ("Training...")
	ct = len(os.listdir(path))
	pos = 0
	files = os.listdir(path)
	filtered_list = glob.glob('*.jpg')
	names_ct = {}
	namect = 0
	names = {}
	for file in filtered_list:
		pos = pos + 1
		img = face_recognition.load_image_file(file)
		img = resizeImg(img, 50)
		name = file.split('.')[0]
		if name not in names:
			namect=1
		else:
			namect = names_ct[name]
			namect = namect + 1
		names_ct[name] = namect
		names[name] = name
		name = (name + "_" + str(namect))
		ct = len(filtered_list)
		print ("Name: " + name + "(" + str(pos) + "/" + str(ct) + ")")
		try:
			all_face_encodings[name] = face_recognition.face_encodings(img)[0]
		except:
			continue

	
	with open(nv.KNOWN_FACES_DB, 'wb') as f:
		pickle.dump(all_face_encodings, f)
		print ("Encodings dat file created!")
	f.close()


def recognize(img):
	img = face_recognition.load_image_file(img)
	test_face = face_recognition.face_encodings(img)
	result = face_recognition.compare_faces(nv.KNOWN_ENCODINGS, test_face)
	results = list(zip(nv.KNOWN_NAMES, result))
	print (results)
	return results

if __name__ == "__main__":
	train()
