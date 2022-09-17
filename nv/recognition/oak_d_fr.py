# coding=utf-8
import PySimpleGUI as sg
import time
import subprocess
import os
import argparse
import blobconverter
import cv2
import depthai as dai
import numpy as np
from np.core.log import np_logger
from MultiMsgSync import TwoStageHostSeqSync


dbdir="/home/monkey/.local/lib/python3.8/site-packages/nv/recognition/databases"
unknown_dir = f"{dbdir}/unknown"
known_dir = f"{dbdir}/known"
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


def frame_norm(frame, bbox):
	normVals = np.full(len(bbox), frame.shape[0])
	normVals[::2] = frame.shape[1]
	return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

VIDEO_SIZE = (1024, 768)
databases = "databases"
if not os.path.exists(databases):
	os.mkdir(databases)
	os.mkdir(dbdir)


def get_name_ct(name):
	com = f"find \"{known_dir}\" -name \"{name}*.npz\""
	_list = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	return len(_list)


def get_unknown_ct():
	dbdir
	com = f"find \"{dbdir}\" -name \"*.jpg\""
	images = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	nums = []
	for img in images:
		try:
			num = int(os.path.basename(img).split(".jpg")[0])
			nums.append(num)
		except:
			pass

	nums = sorted(nums)
	if nums != []:
		l = len(nums) - 1
		print(nums, l)
		ct = nums[l]
		return ct
	else:
		return 0


class TextHelper:
	def __init__(self) -> None:
		self.bg_color = (0, 0, 0)
		self.color = (255, 255, 255)
		self.text_type = cv2.FONT_HERSHEY_SIMPLEX
		self.line_type = cv2.LINE_AA
	def putText(self, frame, text, coords):
		cv2.putText(frame, text, coords, self.text_type, 1.0, self.bg_color, 4, self.line_type)
		cv2.putText(frame, text, coords, self.text_type, 1.0, self.color, 2, self.line_type)

class FaceRecognition:
	def __init__(self, db_path, name=None) -> None:
		if name == None:
			self.name = 'Unknown'
		else:
			self.name = name
		self.db_path = db_path
		self.read_db(self.db_path)
		self.bg_color = (0, 0, 0)
		self.color = (255, 255, 255)
		self.text_type = cv2.FONT_HERSHEY_SIMPLEX
		self.line_type = cv2.LINE_AA
		self.printed = True
		self.current_dir = os.getcwd()
		self.unknown_ct = get_unknown_ct()
		self.learn_flag = False
		self.confidence = None
		self.override_name = False

	def cosine_distance(self, a, b):
		if a.shape != b.shape:
			raise RuntimeError("array {} shape not match {}".format(a.shape, b.shape))
		a_norm = np.linalg.norm(a)
		b_norm = np.linalg.norm(b)
		return np.dot(a, b.T) / (a_norm * b_norm)

	def new_recognition(self, results, frame=None):

		conf = []
		max_ = 0
		label_ = None
		for label in list(self.labels):
				for j in self.db_dic.get(label):
					conf_ = self.cosine_distance(j, results)
					if conf_ > max_:
						max_ = conf_
						label_ = label

		conf.append((max_, label_))
		name = conf[0] if conf[0][0] >= 0.5 else (1 - conf[0][0], "UNKNOWN")
		# self.putText(frame, f"name:{name[1]}", (coords[0], coords[1] - 35))
		# self.putText(frame, f"conf:{name[0] * 100:.2f}%", (coords[0], coords[1] - 10))
		_d, _n = name
		user_text = self.win['SET_NAME'].Get()
		if user_text != '':
			self.override_name = True
			self.name = user_text
			print("Override:", self.name)
		else:
			self.override_name = False
			self.name = _n
			print("Normal:", self.name)
		self.win['CURRENT_NAME'].update(self.name)
		#print(_d, _n, conf[0])
		if '.' in str(_n):
			_n = str(os.path.basename(_n).split('.')[0])
		if _n == "UNKNOWN":
			self.create_db(results, frame)
		return _d, _n

	
	def read_db(self, databases_path):
		com = f"find \"{dbdir}\" -name \"*.npz\""
		files = subprocess.check_output(com, shell=True).decode().strip().split("\n")
		self.db_dic = {}
		self.labels = []
		print (len(files), files)
		if files[0] != '':
			for fullpath in files:
				filename = os.path.splitext(fullpath)[0]
				label = os.path.basename(filename)
				self.labels.append(label)
				with np.load(fullpath) as db:
					self.db_dic[label] = [db[j] for j in db.files]


	def putText(self, frame, text, coords):
		cv2.putText(frame, text, coords, self.text_type, 1, self.bg_color, 4, self.line_type)
		cv2.putText(frame, text, coords, self.text_type, 1, self.color, 1, self.line_type)

	def ensure_dir(self, directory=None):
		if directory == None:
			directory = f"{databases}/{self.name}"
		if not os.path.exists(directory):
				os.makedirs(directory)


	def toggle_learning(self, opt=None):
		if opt is not None:
			self.learning_flag = opt
		else:
			if self.learning_flag == True:
				self.learning_flag = False
			elif self.learning_flag == False:
				self.learning_flag = True
		log(f"Learning flag toggled: {self.learning_flag}", 'info')


	def show_ui(self):
		layout = []
		combo = [sg.Combo([True, False], False, enable_events=True, key='SET_LEARN_MODE')]
		text = [sg.Text(self.name, key='CURRENT_NAME'), sg.Input('', enable_events=True, do_not_clear=True, expand_x=True, key='SET_NAME')]
		layout.append(combo)
		layout.append(text)
		self.win = sg.Window('Oak-D Lite Control', layout, no_titlebar=False, location=(0, 1100), size=(300,300), keep_on_top=True, grab_anywhere=True, element_justification='center', finalize=True, resizable=True)
		#self.win = sg.Window(layout, size=(300, 300), location=(0,1100), key='MAIN_WIN', finalize=True)
		return self.win


	def create_db(self, results, frame=None):
		if self.learn_flag == True:
			print(self.confidence)
			imgpath = None
			try:
				is_numeric = int(self.name)
				filepath = f"{unknown_dir}/{self.name}.npz"
			except:
				filepath = f"{known_dir}/{self.name}.npz"
			if self.name is None or self.name == 'Unknown' or self.name == 'UNKNOWN' or 'Unknown' in str(self.name):
				self.unknown_ct += 1
				self.name = self.unknown_ct
				filepath = f"{unknown_dir}/{self.unknown_ct}.npz"
				imgpath = f"{unknown_dir}/{self.unknown_ct}.jpg"
			else:
				filepath = f"{known_dir}/{self.name}.npz"
				imgpath = f"{known_dir}/{self.name}.jpg"

			#self.ensure_dir(directory)
			if frame is not None:
				print (f"Image path:{imgpath}")
				cv2.imwrite(imgpath, frame)
			try:
				with np.load(filepath) as db:
					db_ = [db[j] for j in db.files][:]
			except Exception as e:
				db_ = []
			db_.append(np.array(results))
			fname = os.path.splitext(filepath)[0]
			np.savez_compressed(fname, *db_)
			self.adding_new = False

if __name__ == "__main__":
	print("Creating pipeline...")
	pipeline = dai.Pipeline()
	print("Creating Color Camera...")
	cam = pipeline.create(dai.node.ColorCamera)
	# For ImageManip rotate you need input frame of multiple of 16
	cam.setPreviewSize(1024, 768)
	cam.setVideoSize(VIDEO_SIZE)
	cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
	cam.setInterleaved(False)
	cam.setBoardSocket(dai.CameraBoardSocket.RGB)
	host_face_out = pipeline.create(dai.node.XLinkOut)
	host_face_out.setStreamName('color')
	cam.video.link(host_face_out.input)
	# ImageManip as a workaround to have more frames in the pool.
	# cam.preview can only have 4 frames in the pool before it will
	# wait (freeze). Copying frames and setting ImageManip pool size to
	# higher number will fix this issue.
	copy_manip = pipeline.create(dai.node.ImageManip)
	cam.preview.link(copy_manip.inputImage)
	copy_manip.setNumFramesPool(20)
	copy_manip.setMaxOutputFrameSize(1024*768*3)
	# ImageManip that will crop the frame before sending it to the Face detection NN node
	face_det_manip = pipeline.create(dai.node.ImageManip)
	face_det_manip.initialConfig.setResize(300, 300)
	copy_manip.out.link(face_det_manip.inputImage)

	# NeuralNetwork
	print("Creating Face Detection Neural Network...")
	face_det_nn = pipeline.create(dai.node.MobileNetDetectionNetwork)
	face_det_nn.setConfidenceThreshold(0.5)
	face_det_nn.setBlobPath(blobconverter.from_zoo(name="face-detection-retail-0004", shaves=6))
	# Link Face ImageManip -> Face detection NN node
	face_det_manip.out.link(face_det_nn.input)

	face_det_xout = pipeline.create(dai.node.XLinkOut)
	face_det_xout.setStreamName("detection")
	face_det_nn.out.link(face_det_xout.input)

	# Script node will take the output from the face detection NN as an input and set ImageManipConfig
	# to the 'age_gender_manip' to crop the initial frame
	script = pipeline.create(dai.node.Script)
	script.setProcessor(dai.ProcessorType.LEON_CSS)

	face_det_nn.out.link(script.inputs['face_det_in'])
	# We also interested in sequence number for syncing
	face_det_nn.passthrough.link(script.inputs['face_pass'])

	copy_manip.out.link(script.inputs['preview'])

	with open("script.py", "r") as f:
		script.setScript(f.read())

	print("Creating Head pose estimation NN")

	headpose_manip = pipeline.create(dai.node.ImageManip)
	headpose_manip.initialConfig.setResize(60, 60)
	headpose_manip.setWaitForConfigInput(True)
	script.outputs['manip_cfg'].link(headpose_manip.inputConfig)
	script.outputs['manip_img'].link(headpose_manip.inputImage)

	headpose_nn = pipeline.create(dai.node.NeuralNetwork)
	headpose_nn.setBlobPath(blobconverter.from_zoo(name="head-pose-estimation-adas-0001", shaves=6))
	headpose_manip.out.link(headpose_nn.input)

	headpose_nn.out.link(script.inputs['headpose_in'])
	headpose_nn.passthrough.link(script.inputs['headpose_pass'])

	print("Creating face recognition ImageManip/NN")

	face_rec_manip = pipeline.create(dai.node.ImageManip)
	face_rec_manip.initialConfig.setResize(112, 112)
	face_rec_manip.setWaitForConfigInput(True)

	script.outputs['manip2_cfg'].link(face_rec_manip.inputConfig)
	script.outputs['manip2_img'].link(face_rec_manip.inputImage)

	face_rec_nn = pipeline.create(dai.node.NeuralNetwork)
	face_rec_nn.setBlobPath(blobconverter.from_zoo(name="face-recognition-arcface-112x112", zoo_type="depthai", shaves=6))
	face_rec_manip.out.link(face_rec_nn.input)

	arc_xout = pipeline.create(dai.node.XLinkOut)
	arc_xout.setStreamName('recognition')
	face_rec_nn.out.link(arc_xout.input)


	with dai.Device(pipeline) as device:
		facerec = FaceRecognition(databases)
		facerec.show_ui()
		sync = TwoStageHostSeqSync()
		text = TextHelper()

		queues = {}
		# Create output queues
		for name in ["color", "detection", "recognition"]:
			queues[name] = device.getOutputQueue(name)

		while True:
			for name, q in queues.items():
					# Add all msgs (color frames, object detections and face recognitions) to the Sync class.
					if q.has():
						sync.add_msg(q.get(), name)
			event, values = facerec.win.read(timeout=1)
			if event != '__TIMEOUT__':
				print (event)
				try:
					print(values[event])
				except:
					print("No values for event!")
				if event == 'SET_NAME':
					try:
						if len(values[event]) > 0 and  values[event] != '':
							facerec.override_name = True
							facerec.name = values[event]
						else:
							facerec.override_name = False
					except Exception as e:
						facerec.override_name = False
					
			if event == 'SET_LEARN_MODE':
				facerec.learn_flag = values[event]
				log(f"Set learning mode to {facerec.learn_flag}!", 'info')
			msgs = sync.get_msgs()
			if msgs is not None:
				frame = msgs["color"].getCvFrame()
				dets = msgs["detection"].detections

				for i, detection in enumerate(dets):
					bbox = frame_norm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
					cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (10, 245, 10), 2)

					features = np.array(msgs["recognition"][i].getFirstLayerFp16())
					conf, name = facerec.new_recognition(features, frame)
					if facerec.override_name == True:
						name = facerec.name
					facerec.confidence = conf
					text.putText(frame, f"{name} {(100*conf):.0f}%", (bbox[0] + 10,bbox[1] + 35))

				cv2.imshow("color", cv2.resize(frame, (1024,768)))

				if cv2.waitKey(1) == ord('q'):
						break
