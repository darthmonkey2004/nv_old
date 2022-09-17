#!/usr/bin/python3
#This runs a Flask based web streaming process that does several things:
#	1. Serves html pages saved in nv.EXEC_DIR/"templates" (index.html contains multi view)
#	2. Serves individualized video streams at /cam/int(camera_id)/ or /video_feed/int(camera_id)
#		TODO: populate main page with secondary capture stream, single view with primary
#	3. Reads object detection/screen update data in realtime from file paths in nv.IOFILES. 
#	(check __init__.py)
#		Data should be in the format of a list of 2 element tuples of 'object_name, coords'.
#		coords should be in (left, top, right, bottom) or (x1, y1, x2, y2),
#			while object_name should be a string.
#
#			Example: [(object_name1, object_rect1), (object_name2, object_rect2), ...]
#		This is non-bocking, and failures are wrapped in a try except block,
#		so just have your process function drop it's data into file using
#!/usr/bin/python3
#		nv.writeIoFile(camera_id), and it will update streaming image in realtime.
#		TODO: Migrate functions to another python file (functions.py),
#			and import in init to speed up import, only grabbing the ones necessary for capture if not processing img.
#The benefit here is that the display object has nothing to do with the visual processing at all
#	so you can devote how much or little processing power you want without affecting the display object, as it runs in an isolated thread.
#	Just just import and then point the output of your detection/tracking/whatever function or module to nv.writeIoFile().
#This is a work in progress, and I'm no python pro. So of course input, and any suggestions, is amazingly appreciated.
#-Matt
#darthmonkey2004@gmail.com



import nv
from flask import Flask, render_template, request, Response
import cv2
import pickle
from os.path import expanduser, sep
import sys
import threading
import argparse
import imutils
import os
import imagezmq
import numpy as np
import face_recognition
from PIL import Image, ImageDraw
import docopt
#import nv.Main.ipptz as ipptz


#servo = nv.ipptz.ServoDriver()
#servo2 = nv.servo.ServoDriver('/dev/ttyACM0', 57600)
outputFrame = None
app = Flask(__name__)
def gen_frames(camera_id, iofiles, outfile=False):
	global WIDTH
	global HEIGHT
	boxes = []
	camera_state = False
	is_tracking = False
	camera_id = int(camera_id)
	#iofile=iofiles[camera_id]
	iofile='/home/monkey/.np/0.io'
	src = nv.FEEDS[camera_id]
	cap = cv2.VideoCapture(src)
	WIDTH = int(cap.get(3))
	HEIGHT = int(cap.get(4))
	objects = []
	drawn = None
	writer = None
	object_id = 0
	if outfile != False:
		fname = (nv.DATA_DIR + os.path.sep + outfile + "." + str(camera_id) + ".avi")
		print (fname)

		writer = cv2.VideoWriter(fname, cv2.VideoWriter_fourcc('M','J','P','G'), 10, (frame_width,frame_height))
	out = []
	#nv.writeIoFile(camera_id, [out])
	while True:
		data = nv.readIoFile(camera_id)
		if data is None:
			data = []
		camera_state, frame = cap.read()  # read the camera frame
		if camera_state == False:
			break
		if frame is None:
			print ("Empty image. Exiting...")
			break
		if camera_state == True:
			#frame2 = imutils.resize(frame, width=400)
			if outfile != False:
				print ("Writing frame..")
				writer.write(frame)
			pos = -1
			if len(data) > 0 and type(data) == list:
				for line in data:
					object_name, box = line
					if box is not None:
						if type(box) == tuple and len(box) == 2:
							object_id, box = box
						#print (object_name, object_id, box)
						l, t, r, b = box
						#l, t, r, b = ((l+(l/2)), (t+(t/2)), (r+(r/2)), (b+(b/2)))
						#l, t, r, b = ((l*2), (t*2), (r*2), (b*2))
						if camera_id == 3:
							cx = ((r - l) / 2)
							x = l + cx
							cy = ((b - t) / 2)
							y = b - cy
							#servo.move(x, y, WIDTH, HEIGHT)
						elif camera_id == 1:
							cx = ((r - l) / 2)
							x = l + cx
							cy = ((b - t) / 2)
							y = b - cy
							#servo2.move(x, y, WIDTH, HEIGHT)
						frame = cv2.rectangle(frame, (int(l), int(t), int(r), int(b)), nv.RED, 2)
						y = t + 30
						coords = (int(l), int(y))
						drawn = cv2.putText(frame, object_name, coords, nv.FONT, nv.FONT_SCALE, nv.BLUE, 2, cv2.LINE_AA)
			ret, buffer = cv2.imencode('.jpg', frame)
			frame = buffer.tobytes()
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
	if writer is not None:
		writer.release()
	cap.release()		


@app.route('/video_feed/<string:id>/', methods=["GET"])
def video_feed(id):
   
	"""Video streaming route. Put this in the src attribute of an img tag."""
	return Response(gen_frames(id, nv.IOFILES),
					mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/', methods=["GET"])
def index():
	return render_template('index.html')

@app.route('/cam/<string:id>/')
def cam(id):
	camfile = (str(id) + '.html')
	return render_template(camfile)

@app.route('/api/facerec', methods=['POST'])
def rec():
	r = request
	nparr = np.fromstring(r.data, np.uint8)
	# decode image
	img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
	results = str(nv.recognize(img))
	#response = {'message': 'image received'}
	response = results.encode()
	return Response(response=response, status=200, mimetype="application/json")

@app.route('/api/facedetect', methods=['POST'])
def fd():
	r = request
	nparr = np.fromstring(r.data, np.uint8)
	# decode image
	img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
	results = str(nv.recognize(img))
	#response = {'message': 'image received'}
	response = results.encode()
	return Response(response=response, status=200, mimetype="application/json")

if __name__ == '__main__':
	import nv
	ap = argparse.ArgumentParser()
	ap.add_argument("-w", "--webport", dest="web_port", type=int, default="9876", help="HTTP port")
	ap.add_argument("-r", "--recvport", dest="imgsrv_port", type=int, default="5555", help="ImageZMQ receiver port. Starts at 5555, increases incrementally by one for each feed.")
	ap.add_argument("-a", "--listen-address", dest="localip", type=str, default="127.0.0.1", help="Network ip address to run server at.")
	args = vars(ap.parse_args())

	localip = nv.LOCALIP
	web_port = nv.WEB_PORT
	imgsrv_port = nv.IMGSRV_PORT
	CONFIDENCE = 0.45
	imageHub = imagezmq.ImageHub()
	trainpath = nv.TRAINPATH
	all_face_encodings = nv.readDbFile(nv.KNOWN_FACES_DB)
	known_names = list(all_face_encodings.keys())
	known_encodings = np.array(list(all_face_encodings.values()))
	nv.mkIoFiles()
	pos = 0
	t = threading.Thread(target=gen_frames, args=(1, nv.IOFILES))
	t.daemon = True
	t.start()
	app.run(host= '0.0.0.0')

