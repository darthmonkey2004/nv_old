import os
import subprocess
from nv.main.conf import init_opts, read_opts, write_opts
import PySimpleGUI as sg
import keyring
from nv.main.log import nv_logger
import sys


exit_loop = False


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


def set_auth(label, key, val):
	return keyring.set_password(label, key, val)


def get_auth(label, key):
	return keyring.get_password(label, key)


def get_new_id():
	home = os.path.expanduser("~")
	path = f"{home}{os.path.sep}.np{os.path.sep}nv"
	ids = []
	com = f"cd \"{path}\"; ls *.conf | grep -v \"nv.conf\""
	confs = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	for conf in confs:
		ids.append(int(conf.split('_')[2].split('.conf')[0]))
	ids = sorted(ids)
	newid = ids[len(ids) - 1] + 1
	return newid

def new_camera(opts):
	camera_id = opts['camera_id']
	user = opts[camera_id]['user']
	location = opts['ptz']['window']['location']
	size = opts['ptz']['window']['size']
	ww, wh = size
	wh = wh - 100
	ww = ww - 150
	size = (ww, wh)
	layout = []
	#settings_menus = ['PTZ Settings', 'Face Detection Settings', 'Object Detection Settings', 'Image Output Settings', 'Capture Settings', 'Server Settings', 'General Settings']
	#menu_def = [['Settings', [settings_menus]]]
	#menu = sg.MenubarCustom(menu_def, tearoff=True, key='-menubar_key-')
	
	line1 = [sg.Text('Camera_id'), sg.Input(default_text=opts['camera_id'], size=(10, 10), enable_events=True, change_submits=True, key='-CAMERA_ID-')]
	auth_ckbox = [sg.Checkbox('Rqeuires Authentication', default=True, enable_events=True, key='-HAS_AUTH-')]
	ptz_ckbox = [sg.Checkbox('PTZ Enabled', default=False, enable_events=True, key='-HAS_PTZ-')]
	cam_width = [sg.Text('Camera Width:'), sg.Input(default_text='640', size=(10, 10), enable_events=True, change_submits=True, key='-CAMERA_WIDTH-')]
	cam_height = [sg.Text('Camera Height'), sg.Input(default_text='352', size=(10, 10), enable_events = True, change_submits=True, key='-CAMERA_HEIGHT-')]
	userline = [sg.Text('Username:'), sg.Input(default_text=user, size=(10, 30), enable_events=True, change_submits=True, key='-SET_USER-')] 
	pwline = [sg.Text('Password:'), sg.Input(default_text="", size=(10, 30), password_char = "*", key='-SET_PASS-')]
	line3 = [sg.Button('Add'), sg.Button('Cancel')]
	keyboard_checkbox = [sg.Button('Save Window Location'), sg.Checkbox('Keyboard Control:', default=False, enable_events=True, key='-KEYBOARD_CONTROL-')]
	layout.append(line1)
	layout.append(cam_width)
	layout.append(cam_height)
	layout.append(auth_ckbox)
	layout.append(userline)
	layout.append(pwline)
	layout.append(ptz_ckbox)
	layout.append(line3)
	win = sg.Window('Add Camera', layout, return_keyboard_events=False, location=location, size=size, element_justification='center', finalize=True, resizable=True)
	return win

def new_camera_loop(win=None):
	global exit_loop
	user = os.path.expanduser("~").split('/home/')[1]
	camera_id = get_new_id()
	opts = init_opts(camera_id)
	opts['camera_id'] = camera_id
	opts[camera_id] = {}
	opts[camera_id]['has_auth'] = True
	opts[camera_id]['has_ptz'] = False
	opts[camera_id]['H'] = None
	opts[camera_id]['W'] = None
	opts[camera_id]['url'] = None
	opts[camera_id]['user'] = user
	if win is None:
		win = new_camera(opts)
	while True:
		if exit_loop == True:
			break
		try:
			window, event, values = sg.read_all_windows(timeout=1)
		except Exception as e:
			log(f"Exit exception:{e}", 'error')
			exit_loop = True
		if event == '__TIMEOUT__':
			pass
		else:
			print(event)
			try:
				print(values[event])
			except:
				pass
			if event == 'Add':
				pw = window['-SET_PASS-'].get()
				label=f"cam_{camera_id}"
				set_auth(label, 'pw', pw)
				opts[camera_id]['src']['pw'] = f"cam_{camera_id}:pw"
				write_opts(opts)
				log(f"Options file written for camera id {camera_id}!", 'info')
				win.close()
				break
			elif event == 'Cancel':
				win.close()
				break
			elif event == '-CAMERA_ID-':
				opts['camera_id'] = values[event]
				log(f"Updated camera id! {camera_id}", 'info')
			elif event == '-CAMERA_WIDTH-':
				opts[camera_id]['H'] = values[event]
				log(f"Updated camera height: {values[event]}", 'info')
			elif event == '-CAMERA_HEIGHT-':
				opts[camera_id]['W'] = values[event]
				log(f"Updated camera width: {values[event]}", 'info')
			elif event == '-HAS_AUTH-':
				opts[camera_id]['src']['has_auth'] = values[event]
				log(f"Updated camera authentication flag: {values[event]}", 'info')
			elif event == '-SET_USER-':
				try:
					var = opts[camera_id]['src']
				except:
					opts[camera_id]['src'] = {}
				opts[camera_id]['src']['user'] = values[event]
				log(f"Updated camera height: {values[event]}", 'info')
			elif event == '-HAS_PTZ-':
				opts[camera_id]['has_ptz'] = values[event]
				log(f"Changed ptz enabled value: {values[event]}", 'info')
