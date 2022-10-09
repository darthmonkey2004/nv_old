import subprocess
import sys
import PySimpleGUI as sg
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

DATA_DIR = os.path.join(os.path.expanduser("~"), '.np', 'nv')
CONFFILE = os.path.join(DATA_DIR, 'nv.conf')
LOGFILE = os.path.join(DATA_DIR, 'nv.log')

def get_local_ip():
	com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}' | grep \"192.168\""
	return subprocess.check_output(com, shell=True).decode().strip()

def get_user_input(window_title='User Input'):
	user_input = None
	input_box = sg.Input(default_text='', enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)
	input_btn = sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')
	layout = [[input_box], [input_btn]]
	input_window = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
	return user_input


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
		conf = {}
		conf['cameras'] = {}
		conf['cameras'][camera_id] = {}
		opts = init_opts(camera_id)
		conf['cameras'][camera_id] = opts
		conf['debug'] = True
		with open(path, 'wb') as f:
			pickle.dump(conf, f)
		f.close()
		return conf

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



def init_opts(camera_id=None):
	if camera_id is None:
		camera_id = 0
	data_dir = os.path.join(os.path.expanduser("~"), '.np', 'nv')
	conf = readConf()
	localip = get_local_ip()
	opts = {}
	opts['debug'] = True
	opts['camera_id'] = camera_id
	opts['confidence_filter'] = 0.5
	opts['tracker_max_age'] = 300
	opts['writeOutImg'] = {}
	opts['writeOutImg']['path'] = {}
	opts['writeOutImg']['path']['known'] =  os.path.join(data_dir, 'Recognized Faces')
	opts['writeOutImg']['path']['unknown'] =  os.path.join(data_dir, 'Unrecognized Face')
	opts['writeOutImg']['enabled'] = True
	opts['skip_frames'] = 15
	opts['status'] = None
	opts['src'] = {}
	src = input("Enter camera source url or device number (blank for None): ")
	if src is None or src == '':
		opts['src']['url'] = None
	else:
		opts['src']['url'] = src
	opts['src']['has_auth'] = False
	opts['src']['user'] = os.path.expanduser("~").split(f"{os.path.sep}home{os.path.sep}")[1]
	opts['H'] = 352
	opts['W'] = 640
	opts['has_ptz'] = False
	opts['detector'] = {}
	opts['detector']['METHODS'] = ['object_detection', 'face_recognition']
	opts['detector']['object_detector'] = {}
	opts['detector']['object_detector']['prototxt'] =  os.path.join(data_dir, 'MobileNetSSD_deploy.prototxt')
	opts['detector']['object_detector']['model'] =  os.path.join(data_dir, 'MobileNetSSD_deploy.caffemodel')
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
	opts['detector']['fr_cv2']['dbpath'] =  os.path.join(data_dir, 'cv2_fr_trained.yml')
	opts['detector']['fr_cv2']['face_cascade'] =  os.path.join(data_dir, 'haarcascade_frontalface_default.xml')
	opts['detector']['fr_cv2']['dataset'] = os.path.join(os.path.expanduser("~"), '.np', 'nv', 'dataset')
	opts['detector']['fr_dlib'] = {}
	opts['detector']['fr_dlib']['tolerance'] =  0.55
	opts['detector']['fr_dlib']['model'] =  'hog'
	opts['detector']['fr_dlib']['upsamples'] = 1
	opts['detector']['fr_dlib']['type'] = 'large'
	opts['detector']['fr_dlib']['passes'] = 1
	opts['detector']['fd_cv2'] = {}
	opts['detector']['fd_cv2']['scale_factor'] =  1.1
	opts['detector']['fd_cv2']['minimum_neighbors'] =  5
	opts['detector']['fd_cv2']['face_cascade'] =  os.path.join(data_dir, 'haarcascade_frontalface_default.xml')
	opts['detector']['fd_dlib'] = {}
	opts['detector']['fd_dlib']['face_cascade'] =  os.path.join(data_dir, 'haarcascade_frontalface_default.xml')
	opts['detector']['ALL_METHODS'] = ['object_detection', 'face_detection', 'yolov3', 'face_recognition']
	opts['detector']['scraper'] = {}
	opts['detector']['scraper']['path_out'] = os.path.join(data_dir, 'scraped_dataset')
	opts['port'] = 8080
	opts['addr'] = localip
	opts['url'] = f"http://{localip}:{opts['port']}/Camera_{camera_id}.mjpg"
	opts['addr'] = localip
	opts['pull_method'] = 'q'
	opts['FONT'] = 0
	opts['FONT_SCALE'] = 1
	opts['ptz'] = {}
	opts['ptz']['addr'] = opts['src']['url'].split('://')[1].split('/')[0]
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
	opts['ptz']['auth'] = {}
	opts['ptz']['auth']['uses_auth'] = True
	opts['ptz']['auth']['user'] = os.path.expanduser("~").split(f"{os.path.sep}home{os.path.sep}")[1]
	opts['maxsize'] = 30
	return opts

def init_camera(camera_id):
	conf = readConf()
	if camera_id not in list(cams.keys()):
		conf['cameras'][camera_id] = {}
		opts = init_opts(camera_id)
		conf['cameras'][camera_id] = opts
		log(f"Camera {camera_id} initialized!", 'info')
		writeConf(conf)
		return opts
	else:
		log(f"Camera id already exists: {camera_id}", 'warning')
		return conf['cameras'][camera_id]

def write_opts(opts):
	# update options config for camera id
	conf = readConf()
	try:
		camera_id = opts['camera_id']
		conf['cameras'][camera_id] = opts
		writeConf(conf)
		return True
	except Exception as e:
		log(f"Unable to write options to config file: {e}", 'error')
		return False


def read_opts(camera_id=None):
	conf = readConf()
	if camera_id is None:
		camera_id = 0
	try:
		if camera_id in list(conf['cameras'].keys()):
			return conf['cameras'][camera_id]
		else:
			log(f"Camera id not found! Initializing  from default...", 'warning')
			opts = init_camera(camera_id)
	except Exception as e:
		log(f"Error: Unable to read opts file! Re-initializing...", 'error')
		conf['cameras'][camera_id] = init_opts(camera_id)
		writeConf(conf)
		return conf['cameras'][camera_id]




