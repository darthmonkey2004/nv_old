from threading import Thread
#from nv.main.browser import *
import psutil
from nv.main.conf import write_opts
import time
from nv.utils.ptz_control import ptz_control
from nv.utils.keyboard import keyboard
import PySimpleGUI as sg
from nv.main.log import nv_logger
import sys
#import traceback
from nv.utils.settings_menu import *
from nv.utils.keymap import ctk
from nv import quit as quit_nv
from nv.utils.new_camera import *

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


def ptz_ui(opts):
	location = opts['ptz']['window']['location']
	size = opts['ptz']['window']['size']
	layout = []
	settings_menus = ['PTZ Settings', 'Face Detection Settings', 'Object Detection Settings', 'Image Output Settings', 'Capture Settings', 'Server Settings', 'General Settings']
	menu_def = [['Settings', [settings_menus], 'Oak-D Lite']]
	menu = [sg.MenubarCustom(menu_def, tearoff=True, key='-menubar_key-'), sg.Button('Add Camera')]
	line1 = [sg.Button('Up Left'), sg.Button('Up'), sg.Button('Up Right')]
	line2 = [sg.Button('Left'), sg.Button('Stop'), sg.Button('Right')]
	line3 = [sg.Button('Down Left'), sg.Button('Down'), sg.Button('Down Right')]
	keyboard_checkbox = [sg.Button('Save Window Location'), sg.Checkbox('Keyboard Control:', default=False, enable_events=True, key='-KEYBOARD_CONTROL-')]
	ptz_track_checkbox = [sg.Checkbox('PTZ Auto Tracking:', default=opts['detector']['track_to_center'], enable_events=True, key='-PTZ_TRACKING-')]
	current_memory_box = [sg.Text(psutil.virtual_memory().percent, key='CURRENT_MEMORY')]
	layout.append(menu)
	layout.append(line1)
	layout.append(line2)
	layout.append(line3)
	layout.append(keyboard_checkbox)
	layout.append(current_memory_box)
	presets = []
	for i in range(0, 4):
		presets.append(i)
	preset_line = [sg.Text('Presets:'), sg.Combo(presets, 0, enable_events=True, key='-SELECT_PRESET-'), sg.Button('Set'), sg.Button('Goto')]
	layout.append(preset_line)
	last_line = [sg.Button('Tour Start'), sg.Button('Tour Stop'), sg.Button('Quit')]
	layout.append(last_line)
	win = sg.Window('PTZ Control', layout, return_keyboard_events=False, location=location, size=size, element_justification='center', finalize=True, resizable=True)
	return win

def quit(opts):
	log(f"UI: Writing opts file (on exit)...", 'info')
	write_opts(opts)
	quit_nv()

def ui_loop(win=None, ptz=None, opts=None):
	settings_menus = ['PTZ Settings', 'Face Detection Settings', 'Object Detection Settings', 'Image Output Settings', 'Capture Settings', 'Server Settings', 'General Settings']
	events = opts['ptz']['events']
	tour_wait_low = opts['ptz']['tour_wait_low']
	tour_wait_med = opts['ptz']['tour_wait_med']
	tour_wait_high = opts['ptz']['tour_wait_high']
	ptz_low = opts['ptz']['ptz_low']
	ptz_med = opts['ptz']['ptz_med']
	ptz_high = opts['ptz']['ptz_high']
	ptz_speed = opts['ptz']['ptz_speed']
	tour_wait = opts['ptz']['tour_wait']
	keys = list(ctk.values())
	codes = list(ctk.keys())
	k = keyboard()
	exit = False
	keyboard_control = opts['ptz']['keyboard_control']
	tour = opts['ptz']['tour']
	tour_started = None
	if ptz == None:
		ptz = ptz_control()
	if win == None:
		win = ptz_ui()
	if events is True:
		ptz.start_loop()
		ptz.set_speed(ptz_speed)
	preset = None
	while True:
		if tour == True:
			if tour_started is None:
				tour_started = time.time()
				tour_dest = 0
			else:
				duration = round(time.time() - tour_started)
				if duration >= tour_wait:
					if tour_dest == 0:
						tour_dest = 1
					elif tour_dest == 1:
						tour_dest = 0
					ptz.goto(tour_dest)
					tour_started = time.time()
		if keyboard_control == True:
			for event, code in k.get_keys():
				if event is not None:
					if event == 'KEY_UP':
						log(f"KEYBOARD: Event=Key Up, PTZ Stopped.", 'info')
						ptz.key = 'stop'
					elif event == 'KEY_DOWN':
						if code in codes:
							key = keys[codes.index(code)]
							if '_' in key:
								key = key.split('_')[1]
							ptz.key = key
						
		if exit == True:
			quit(opts)
			break
		try:
			window, event, values = sg.read_all_windows(timeout=1)
			win['CURRENT_MEMORY'].update(psutil.virtual_memory().percent)
		except Exception as e:
			log(f"Exit exception:{e}", 'error')
			exit = True
		if event == '__TIMEOUT__':
			pass
		else:
			settings_menus = ['PTZ Settings', 'Face Detection Settings', 'Object Detection Settings', 'Image Output Settings', 'Capture Settings', 'Server Settings', 'General Settings']
			if event in settings_menus:
				win.hide()
				settings(event)
				event_loop()
				win.un_hide()
			elif event == 'Add Camera':
				win.hide()
				new_camera_loop()
				win.un_hide()
			if ptz.opts['debug'] == True:
				log(f"EVENT: {event}", 'info')
			if event == 'Quit':
				exit = True
				window.close()
			elif event == '-KEYBOARD_CONTROL-':
				keyboard_control = values[event]
				log(f"Keyboard events set to {keyboard_control}!", 'info')
			elif event == 'Tour Start':
				tour = True
				log(f"Tour started!", 'info')
				tour_started = None
				tour_dest = 0
			elif event == 'Tour Stop':
				tour = False
				tour_started = None
				tour_dest = 0
				log(f"Tour stopped!", 'info')
			elif event == '-SELECT_PRESET-':
				preset = values[event]
				print(f"Selected preset: {preset}")
			elif event == 'Goto':
				if preset == None:
					preset = 0
				else:
					ptz.goto(preset)
				print(f"Move to preset: {preset}")
			elif event == 'Save Window Location':
				coords = window.CurrentLocation()
				opts['ptz']['window']['location'] = coords
				log(f"Current lcoation: {coords}", 'info')
			elif event == sg.WIN_CLOSED:
				try:
					window.close()
					if exit == True:
						quit(opts)
						break
				except:
					exit = True
			elif event == '-PTZ_TRACKING-':
				ptz.track_to_center = values[event]
				log(f"Toggle PTZ Auto Tracking: {ptz.track_to_center}!", 'info')
			else:
				print(event)

	


def start(opts):
	#bt = Thread(target=load_viewer, args=(0,))
	#bt.setDaemon(True)
	#bt.start()
	#load_viewer(0)
	win = ptz_ui(opts)
	ui_loop(win=win, ptz=None, opts=opts)

if __name__ == "__main__":
	start()
	
