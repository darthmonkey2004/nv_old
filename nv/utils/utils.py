import subprocess
import sys
import cv2
import PySimpleGUI as sg
from nv.main.log import nv_logger
import keyring
import getpass


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

def get_local_ip():
	com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}' | grep \"192.168\""
	return subprocess.check_output(com, shell=True).decode().strip()


def set_auth(camera_id, pw):
	auth_key = f"Camera_{camera_id}:auth"
	try:
		keyring.set_password(auth_key, 'pw', pw)
		return auth_key
	except Exception as e:
		log(f"Failed to set password in keyring: {e}", 'error')
		return None


def get_auth(camera_id):
	auth_key = f"Camera_{camera_id}:auth"
	try:
		pw = keyring.get_password(auth_key, 'pw')
		return pw
	except Exception as e:
		log(f"Couldn't get password from store ({e})! Enter it now:", 'info')
		pw = getpass.getpass("Password: ")
		set_auth(camera_id, pw)
		log(f"Password stored in keyring!")
		return pw


def calculate_ratio_bysize(img_size, target_size):
	#Accepts either the original image  or image shape as a tuple (img_size)
	if type(img_size) is tuple:
		iw, ih = img_size
	else:
		iw, ih = (img_size.shape[1], img_size.shape[0])
	tw, th = target_size
	if iw > ih or iw == ih:
		r = tw / iw
	elif iw < ih:
		r = th / ih
	return r


def scale_box(img, ratio, box):
	# if ratio is a tuple, then size was provided, we get ratio from size
	if type(ratio) is tuple:
		ratio = calculate_ratio_bysize(img, ratio)
	# if ratio over 5, function was probably given a percentage, so reduce to decimal
	if ratio > 5:
		ratio = ratio / 100
	startx, starty, endx, endy = box[0], box[1], box[2], box[3]
	bw = endx - startx
	bh = endy - starty
	cx = startx + (bw / 2)
	cy = starty + (bh / 2)
	ncx = cx * ratio
	ncy = cy * ratio
	nbw = bw * ratio
	nbh = bh * ratio
	nstartx = int(ncx - (nbw / 2))
	nstarty = int(ncy - (nbh / 2))
	nendx = int(nstartx + nbw)
	nendy = int(nstarty + nbh)
	box = nstartx, nstarty, nendx, nendy
	return box
	#return constrain_box(box, img)



def get_color(color='random'):
	colors = {}
	colors['red'] = (255, 0, 0)
	colors['orange'] = (255, 127.5, 0)
	colors['yellow'] = (255, 255, 0)
	colors['green'] = (0, 255, 0)
	colors['blue'] = (0, 255, 255)
	colors['indigo'] = (0, 0, 255)
	colors['violet'] = (255, 0, 255)
	colors_vals = list(colors.values())
	colors_names = list(colors.values())
	if color == 'random':
		#if color argument omitted or 'random', randomize color tuple.
		colortup = colors_vals[random(1,7) - 1]
	else:
		#if color argument given, try and return color from dict. except None.
		try:
			colortup = colors[color]
		except:
			log(f"Color not found: {color}", 'error')
			return None
			
	return colortup


def get_user_input(img_file, window_title='User Input', default_text=None, names=None):
	if names is None:
		names = []
	png = Image.open(img_file)
	fname = f"{os.path.splitext(img_file)[0]}.png"
	print(fname)
	newsize = calculate_scale(png.size, (640, 640))
	png.resize(newsize)
	png.save(fname)
	w, h = newsize
	if default_text == None:
		default_text = 'Unknown'
	input_box = [[sg.Listbox(values=names, size=(30, 5), change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key='-SET_NAME-'), sg.Input(default_text=default_text, enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)]]
	input_btn = [[sg.Button(button_text='Skip', auto_size_button=True, pad=(1, 1), key='-SKIP-'), sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')]]
	image = [sg.Image(fname, subsample=4, size=(w, h), enable_events=True, key='id_image')]
	layout = [input_box, input_btn, image]
	win_w = w + 100
	win_h = h + 100
	input_window = sg.Window(window_title, layout, size=(win_w, win_h), location=(0, 1400), keep_on_top=True, element_justification='center', finalize=True)
	user_input = None
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
		elif event == '-SET_NAME-':
			user_input = values[event].pop()
			input_window['-USER_INPUT-'].update(user_input)
		elif event == '-SKIP-':
			user_input = ''
			input_window.close()		
	if user_input == None:
		user_input = default_text
	return user_input


def calculate_scale(img_size, max_size=None):
	#calculates size ratio for a (w, h) tuple, preserving aspect ratio
	#if max_size provided, uses it for scale dimensions, otherwise 300,300 (mobilnet nn requirement)
	if max_size is None:
		mw = 300
		mh = 300
	else:
		mw, mh = max_size
	w, h = img_size
	if w > h or w == h:
		r = mw / w
	elif w < h:
		r = mh / h
	nw = int(w * r)
	nh = int(h * r)
	return (nw, nh)


def calculate_scale_byratio(img_size, r=0.5):
	#calculates size ratio for a (w, h) tuple, preserving aspect ratio
	#if max_size provided, uses it for scale dimensions, otherwise 300,300 (mobilnet nn requirement)
	w, h = img_size
	nw = int(w * r)
	nh = int(h * r)
	return (nw, nh)


def constrain_box(box, img):
	#constrain box to image dimensions (check r and bo within w and h)
	try:
		l, t, r, b = box[0](), box[1](), box[2](), box[3]()
	except Exception as e:
		data = dir(box)
		#log(f"Tuple probably not rectangle ({box}, data:{data}", 'error')
		l, t, r, b = box
	h, w, c = img.shape
	if b > h:
		b = h - 10
	if r > w:
		r = w - 10
	return l, t, r, b


def scale_img(img, target_size=None, percent=None): 
	w = img.shape[1]
	h = img.shape[0]
	size = (w, h)
	# resizes image (keeping ratio) with either a (w, h) tuple or percentage ratio.
	if target_size is None and percent is None:
		#if no arguments provided, scale using 300,300
		log(f"utils:scale_img(): No size provided. Using 300,300!", 'warning')
		target_size = (300, 300)
		newsize = calculate_scale(size, newsize)
	elif target_size is None and percent is not None:
		# if percentage (ratio) given, scale both sides to ratio
		if percent > 1:
			percent = percent / 100
			nw = int(w * percent)
			nh = int(h * percent)
		newsize = (nw, nh)
	elif target_size is not None and percent is None:
		# if target size given, calculate new scale from image shape
		newsize = calculate_scale(size, target_size)
	#return scaled image
	return cv2.resize(img, newsize)
		


	
	
