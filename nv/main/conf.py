from suntime import Sun, SunTimeException
import datetime
import os
import pickle
#import pathlib
from nv.main.log import nv_logger
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

user = os.path.expanduser("~")
DATA_DIR = (f"{user}{os.path.sep}.np{os.path.sep}nv")
CONFFILE = f"{DATA_DIR}{os.path.sep}nv.conf"
LOGFILE = f"{DATA_DIR}{os.path.sep}nv.log"


def readConf(path=None):
	if path == None:
		path = CONFFILE
	try:

		with open(path, 'rb') as f:
			cams = pickle.load(f)
		f.close()
		return cams
	except Exception as e:
		#log(f"Warning: conf file not found! Using defaults...", 'warning')
		camera_id = 0
		cams = {}
		cams[camera_id] = {}
		cams[camera_id]['addr'] = '192.168.2.4'
		cams[camera_id]['port'] = 8080
		cams[camera_id]['url'] = (f"http://{cams[0]['addr']}:{cams[0]['port']}/Camera_{camera_id}.jpeg")
		cams[camera_id]['w'] = 640
		cams[camera_id]['h'] = 352
		cams[camera_id]['src'] = 'rtsp://192.168.2.12/12'
		cams[camera_id]['method'] = 'cv2'
		cams['debug'] = True
		with open(path, 'wb') as f:
			pickle.dump(cams, f)
		f.close()
		return cams
conf = readConf()

def writeConf(data):
	try:
		with open(CONFFILE, 'wb') as f:
			pickle.dump(data, f)
		f.close()
		
		log('conf.py, writeConf: Conf updated!', 'info')
		return True
	except Exception as e:
		print(f"Exception in conf.py, writeConf, line 83:{e}")
		return False



def init_opts(camera_id):
	conf = readConf()
	opts = {}
	opts['debug'] = True
	opts['camera_id'] = 0
	opts['confidence_filter'] = 0.5
	opts['tracker_max_age'] = 300
	opts['writeOutImg'] = {}
	opts['writeOutImg']['path'] = {}
	opts['writeOutImg']['path']['known'] =  '/home/monkey/.np/nv/Recognized Faces'
	opts['writeOutImg']['path']['unknown'] =  '/home/monkey/.np/nv/Unrecognized Face'
	opts['writeOutImg']['enabled'] = True
	opts['skip_frames'] = 15
	opts['status'] = None
	opts['src'] = 'rtsp://192.168.2.12/11'
	opts['detector'] = {}
	opts['detector']['METHODS'] = ['object_detection', 'face_recognition']
	opts['detector']['object_detector'] = {}
	opts['detector']['object_detector']['prototxt'] =  '/home/monkey/.np/nv/MobileNetSSD_deploy.prototxt'
	opts['detector']['object_detector']['model'] =  '/home/monkey/.np/nv/MobileNetSSD_deploy.caffemodel'
	opts['detector']['object_detector']['targets'] =  ['person', 'cat', 'horse', 'truck', 'dog', 'car', 'motorbike']
	opts['detector']['object_detector']['classes'] =  ['background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
	opts['detector']['object_detector']['confidence'] =  0.49
	opts['detector']['fd'] = {}
	opts['detector']['fr'] = {}
	opts['detector']['fr']['tolerance'] =  0.55
	opts['detector']['fr']['model'] =  'hog'
	opts['detector']['provider'] = 'dlib'
	opts['detector']['all_providers'] = ['cv2', 'dlib']
	opts['detector']['fr_cv2'] = {}
	opts['detector']['fr_cv2']['dbpath'] =  '/home/monkey/.np/nv/cv2_fr_trained.yml'
	opts['detector']['fr_cv2']['face_cascade'] =  '/home/monkey/.np/nv/haarcascade_frontalface_default.xml'
	opts['detector']['fr_dlib'] = {}
	opts['detector']['fr_dlib']['tolerance'] =  0.55
	opts['detector']['fr_dlib']['model'] =  'hog'
	opts['detector']['fd_cv2'] = {}
	opts['detector']['fd_cv2']['scale_factor'] =  1.1
	opts['detector']['fd_cv2']['minimum_neighbors'] =  5
	opts['detector']['fd_cv2']['face_cascade'] =  '/home/monkey/.np/nv/haarcascade_frontalface_default.xml'
	opts['detector']['fd_dlib'] = {}
	opts['detector']['fd_dlib']['face_cascade'] =  '/home/monkey/.np/nv/haarcascade_frontalface_default.xml'
	opts['detector']['ALL_METHODS'] = ['object_detection', 'face_detection', 'yolov3', 'face_recognition']
	opts['detector']['scraper'] = {}
	opts['detector']['scraper']['path_out'] = '/home/monkey/.np/nv/scraped_dataset'
	opts['H'] = 352
	opts['W'] = 640
	opts['addr'] = '192.168.2.2'
	opts['port'] = 8080
	opts['url'] = 'http://192.168.2.2:8080/Camera_0.mjpg'
	opts['pull_method'] = 'q'
	opts['FONT'] = 0
	opts['FONT_SCALE'] = 1
	opts['ptz'] = {}
	opts['ptz']['events'] = True
	opts['ptz']['tour_wait_low'] = 15
	opts['ptz']['tour_wait_med'] = 10
	opts['ptz']['tour_wait_high'] = 7
	opts['ptz']['ptz_low'] = 2
	opts['ptz']['ptz_med'] = 1
	opts['ptz']['ptz_high'] = 0
	opts['ptz']['ptz_speed'] = 1
	opts['ptz']['tour_wait'] = 10
	opts['ptz']['keyboard_control'] = False
	opts['ptz']['tour'] = False
	opts['ptz']['base_path'] = 'web/cgi-bin/hi3510'
	opts['ptz']['control_endpoint'] = 'ptzctrl.cgi'
	opts['ptz']['param_endpoint'] = 'param.cgi'
	opts['ptz']['window'] = {}
	opts['ptz']['window']['location'] =  (20, 1220)
	opts['ptz']['window']['size'] =  (400, 400)
	return opts



def write_opts(opts):
	camera_id = opts['camera_id']
	try:
		optsfile = f"{DATA_DIR}{os.path.sep}ptz_opts_{camera_id}.conf"
		with open(optsfile, "wb") as f:
			pickle.dump(opts, f)
		f.close()
		log(f"Options file for camera_id {camera_id} written!", 'info')
		return True
	except Exception as e:
		log(f"Unable to write option config file: {e}", 'error')
		return False


def read_opts(camera_id):
	try:
		optsfile = f"{DATA_DIR}{os.path.sep}ptz_opts_{camera_id}.conf"
		with open(optsfile, "rb") as f:
			opts = pickle.load(f)
		f.close()
		log(f"Options file for camera_id {camera_id} read", 'info')
		return opts
	except Exception as e:
		log(f"Error: Unable to read opts file! Re-initializing...", 'error')
		opts = init_opts(camera_id)
		write_opts(opts)
		return opts

