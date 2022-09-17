import subprocess
import sys
import cv2
import nv
import os
import glob

det = nv.detector.detector()
pos = 0
def fromCam(src, name):
	cap = cv2.VideoCapture(src)
	while True:
		pos = pos + 1
		ret, img = cap.read()
		if ret and pos < 16:
			pos = 0
			_, box = det.face_detect(img)
			if box is not None:
				#cv2.rectangle(img, face, (255, 0, 0), 2)
				files = os.listdir(path)
				filtered_list = glob.glob(name + '*')
				ct = len(filtered_list)
				ct = ct + 1
				fname = (name + "." + str(ct) + ".jpg")
				cv2.imwrite(fname, img)
			cv2.imshow('NicVision Image grabber', img)
			key = cv2.waitKey(1) & 0xff
			if key == 113:
				cv2.destroyAllWindows()
				print ("Exit key pressed! Quitting...")
				exit()

def fromFile(src, name):
	img = cv2.imread(src)
	_, box = det.face_detect(img)
	if box is not None:
		#cv2.rectangle(img, face, (255, 0, 0), 2)
		files = os.listdir(path)
		filtered_list = glob.glob(name + '*')
		ct = len(filtered_list)
		ct = ct + 1
		fname = (name + "." + str(ct) + ".jpg")
		cv2.imwrite(fname, img)
		return "Image saved to training directory!"
	else:
		return "No face found! Try another..."

def getName():
	name = "Unknown Person"
	return subprocess.check_output(['zenity', '--entry', '--text=Enter name']).decode().split('\n')[0]


try:
	src = sys.argv[1]
except:
	print ("No src provided. Using '/dev/video0' as default.")
	#src=0
	src = 'rtsp://192.168.2.3:9876/h264_pcm.sdp'
path = (nv.DATA_DIR + nv.sep + "training_data")
os.chdir(path)
print ("Enter your name: ")
name = getName()
localdev='/dev/video'
rtsp='rtsp://'
if localdev in src:
	ret = fromCam(src, name)
elif rtsp in src:
	ret = fromCam(src, name)
else:
	print ("Assuming src is image on drive...")
	ret = fromFile(src, name)
print (ret)


print ("All done!")
exit()
