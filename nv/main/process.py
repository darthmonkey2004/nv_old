from nv.utils.kill_nv import *
import psutil
import sys
from queue import Queue
from threading import Thread
import time
import inspect, traceback
import os
from nv.main import detector as detector
import pickle
from nv.main.correlation_tracker_new import tracker_mgr
from nv.main.log import nv_logger
from nv.main.conf import readConf, read_opts
#from np.nv.trackable_object import TrackableObject
import cv2
logger = nv_logger().log_msg

def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)




def read_input(camera_id=None):
	if camera_id == None:
		camera_id = 0
	iofiles = {}
	iofiles[0] = '/home/monkey/.np/0.io.in'
	id = int(camera_id)
	name = str(iofiles[id])
	lines = []
	pos = 0
	with open(name, 'rb') as f:
		try:
			data = pickle.load(f)
		except:
			data = []
	f.close()
	return data

				
def process(opts=None, input_q=None, out_q=None):
	if opts is None:
		opts = read_opts(0)
	camera_id = int(opts['camera_id'])
	#src = opts['src']
	#CLASSES = opts['detector']['object_detector']['classes']
	#net = cv2.dnn.readNetFromCaffe(opts['detector']['object_detector']['prototxt'] , opts['detector']['object_detector']['model'])
	W = opts['H'] 
	H = opts['W']
	trackers = []
	trackableObjects = {}
	totalFrames = 0
	totalDown = 0
	totalUp = 0
	output = []
	status = "Waiting"
	writeout = None
	try:
		face_cascade = cv2.CascadeClassifier(opts['detector']['fd_cv2']['face_cascade'])
		log(f"PROCESS_THREAD:{camera_id}::Facial classifier read!", 'info')
	except Exception as e:
		log(f"PROCESS_THREAD:{camera_id}::Couldn't read face cascade: {e}", 'error')
	tracker = None
	try:
		log(f"PROCESS_THREAD:{camera_id}::Getting detector...", 'info')
		det = detector.detector(opts)
	except Exception as e:
		log(f"PROCESS_THREAD(Exception!):{camera_id}::Unable to get detector:{e}", 'error')
	name = None
	METHODS = opts['detector']['METHODS']
	log(f"PROCESS_THREAD:{camera_id}::Methods={METHODS}", 'info')
	write_out_img = opts['writeOutImg']['enabled']
	object_id = 0
	#ct = tracker_mgr()
	while True:
		nv_usage = psutil.Process(os.getpid()).memory_info().rss
		percent_used = psutil.virtual_memory()[2]
		if percent_used > 85:
			log("PROCESS:SYSTEM MEMORY LOW!!! EXITING....", 'error')
			break
		#log(f"PROCESS-THREAD-USAGE: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2}", 'info')
		totalFrames += 1
		output = []
		if input_q.empty():
			pass
		else:
			skip_frames, frame = input_q.get_nowait()
			name = None
			box = None
			names = []
			if totalFrames % skip_frames == 0:
				if "face_detection" in METHODS:
					log(f"PROCESS:Detecting face...", 'info')
					ret = det.face_detect(frame)
					if ret is not None:
						box, name, _ = ret
						log(f"PROCESS_THREAD:{camera_id}::Face found!", 'info')
						box = dbox
						name = dname
						log(f"Face dtected: {box}", 'info')
						out=(name, box)
						output.append(out)
						path = opts['writeOutImg']['path']
						ct = len(next(os.walk(path))[2]) + 1
						fname = f"{path}{os.path.sep}{name}.{ct}.jpg"
						if write_out_img == True:
							cv2.imwrite(fname, frame)
						
						
				if "object_detection" in METHODS:
					for oname, obox, confidence in det.object_detect(frame):
						if obox is not None:
							box = obox
						if oname is not None:
							name = oname
							if "person" in oname:
								name = "Unrecognized Face"
								ret = det.recognize(frame)
								if ret is not None:
									name, recbox, tolerance = ret
									log(f"PROCESS_THREAD:{camera_id}::face recognized! Name: {name}", 'info')
									box = recbox
									if write_out_img == True:
										path = opts['writeOutImg']['path']['known']
										dname = name.replace(' ', '_')
										savepath = f"{path}{os.path.sep}{dname}"
										os.makedirs(savepath, exist_ok=True)
										ct = len(next(os.walk(savepath))[2]) + 1
										fname = f"{savepath}{os.path.sep}{dname}_{ct}.jpg"
										cv2.imwrite(fname, frame)									
								else:
									log(f"PROCESS_THREAD:{camera_id}::Unknown Face: {box}", 'info')
									if write_out_img == True:
										path = opts['writeOutImg']['path']['unknown']
										ct = len(next(os.walk(path))[2]) + 1
										fname = f"{path}{os.path.sep}{name}.{ct}.jpg"
										cv2.imwrite(fname, frame)
							out = (name, box)
							log(f"Object Detection output: {out}", 'info')
							output.append(out)
				if "yolov3" in METHODS:
					for name, box, confidence in det.yolov3(img):
						out = (name, box)
						log(f"Yolo output: {out}", 'info')
						output.append(out)

				if "face_recognition" in METHODS:
					data = det.recognize(frame)
					if data is None:
						tname, tbox, tolerance = None, None, None
					else:
						for name, box, tolerance in data:
							log(f"PROCESS_THREAD:{camera_id}::face recognized! Name:{name}", 'info')
							out = (name, box)
							output.append(out)
							if write_out_img == True:
								path = opts['writeOutImg']['path']['known']
								dname = name.replace(' ', '_')
								savepath = f"{path}{os.path.sep}{dname}"
								os.makedirs(savepath, exist_ok=True)
								ct = len(next(os.walk(savepath))[2]) + 1
								fname = f"{savepath}{os.path.sep}{dname}_{ct}.jpg"
								cv2.imwrite(fname, frame)

				out = {}
				out[camera_id] = output
				out_q.put_nowait(out)
				try:
					input_q.task_done()
				except Exception as e:
					log(f"PROCESS::input_q Empty ({e})", 'warning')
					pass
				#log(f"Proc::Qsize:{out_q.qsize()}, MaxSize:{out_q.maxsize}, Unfinished:{out_q.unfinished_tasks}", 'info')
		#totalFrames = totalFrames + 1
	#kill nv process before exiting (should only trigger in low ram environment
	log(f"MAIN PROCESS LOOP EXITED (low memory???)!!! Dumping crash data...", 'error')
	nv_percent_used = psutil.Process(os.getpid()).memory_info().rss / psutil.virtual_memory().used * 100
	available = psutil.virtual_memory().available
	total = psutil.virtual_memory().total
	used = psutil.virtual_memory().used
	string = f"MEMORY_INFO:Total:{total}, Available:{available}, Used:{used}, Used by nv:{nv_percent_used}"
	log(string, 'warning')
	inqsize = input_q.qsize()
	inmaxsize = input_q.maxsize
	inunfinished = input_q.unfinished_tasks
	outqsize = out_q.qsize()
	outmaxsize = out_q.maxsize
	outunfinished = out.unfinished_tasks
	instring = f"INPUTQUEUE DATA:Input size:{inqsize}, Input maxsize:{inmaxsize}, Input skip:{skip_frames}, Input Unfinished:{inunfinished}"
	outstring = f"OUTPUTQUEUE DATA:Output size:{outqsize}, Output maxsize:{outmaxsize}, Output Unfinished:{outunfinished}"
	log(f"instring", 'warning')
	log(f"outstring", 'warning')
	log(f"MAIN PROCESS: Killing nv via SIGKILL...", 'error')
	kill_nv()
	exit()

#TODO: Create process dictionary object, to be passed with image data in input queue, unpacked, and used to set detection options and methods in realtime.
#proc dict should be returned with current values in process output queue, so parent thread can return current values for non class (no properties) objects.
#TODO: Create thread group (pool?) to encapsulate all io queues, processing streams(per camera_id and server instances.
if __name__ == "__main__":
	import sys
	try:
		camera_id = sys.argv[1]
	except:
		camera_id = 0
	process(camera_id)
