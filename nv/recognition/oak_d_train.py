import numpy as np
import subprocess
import cv2
import PySimpleGUI as sg
from PIL import Image
import os

name = 'Unknown'
path = f"{os.getcwd()}{os.path.sep}databases"
unknown_dir = f"{path}/unknown"
known_dir = f"{path}/known"


def get_unknowns():
	condense_dbs()
	global name, path, unknown_dir, known_dir
	com = f"find \"{unknown_dir}\" -name \"*.jpg\""
	images = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	for img_file in images:
		print("Image file:", img_file)
		if os.path.exists(img_file):
			train(img_file)
	com = f"find \"{known_dir}\" -name \"*.jpg\""
	images = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	print("images:", images)
	for img_file in images:
		n = os.path.splitext(os.path.basename(img_file))[0]
		print(n)
		try:
			n = int(n)
			ret = train(img_file)
			print(ret)
			
		except:
			pass
	print("Done!")
	return True

def train(img_file, name=None):
	_rm = False
	if name == None:
		name = 'Unknown'
	_id = os.path.basename(img_file).split(".jpg")[0]
	print(img_file)
	path = os.path.dirname(img_file)
	print("Id:", _id, "Path:", path)
	old_db_path = get_db_path(_id, path)
	if os.path.exists(old_db_path):
		png = Image.open(img_file)
		fname = f"{os.path.splitext(img_file)[0]}.png"
		print(fname)
		png.save(fname)
		w, h = png.size
		name = get_user_input(fname, w, h, "Who is this?", name)
		print(name)
		#ct = get_name_ct(name) + 1
		#print(ct)
		#new_db_path = f"{known_dir}/{name}.{ct}.npz"
		new_db_path = f"{known_dir}/{name}.npz"
		try:
			append_db(old_db_path, new_db_path)
			_rm = True
		except:
			_rm = False
		if _rm == True:
			rm(old_db_path)
			dirname = os.path.dirname(old_db_path)
			imgnamejpg = f"{os.path.splitext(os.path.basename(old_db_path))[0]}.jpg"
			imgpathjpg = f"{dirname}/{imgnamejpg}"
			imgnamepng = f"{os.path.splitext(os.path.basename(old_db_path))[0]}.png"
			imgpathpng = f"{dirname}/{imgnamepng}"
			print (f"Removing {imgpathjpg, imgpathpng}")
			rm(imgpathjpg)
			rm(imgpathpng)
			return True
	else:
		return False
			

def get_db_path(_id, path=None):
	global unknown_dir
	if path == None:
		path = unknown_dir
	#print("ID:", _id, "Path:", path)
	com = f"find \"{path}\" -name \"{_id}.npz\""
	try:
		return subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print (f"Can't get path: {e}")

def rm(f):
	com = f"rm \"{f}\""
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print(f"Couldn't delete: Doesn't exist! ({e})")
		return False
	if ret != '':
		print(f"Error: {ret}")
		return False
	else:
		return True


def append_db(unknown_db, known_db):
	try:
		with np.load(unknown_db) as db:
			data = [db[j] for j in db.files]
	except Exception as e:
		print("Error: Failed to read db: {e}")
		return None
	try:
		if os.path.exists(known_db):
			with np.load(known_db) as db:
				db_ = [db[j] for j in db.files][:]
		else:
			db_ = []
	except Exception as e:
		db_ = []
	try:
		for item in data:
			db_.append(np.array(item))
		fname = os.path.splitext(known_db)[0]
		np.savez_compressed(fname, *db_)
		return True
	except Exception as e:
		print(f"Error: Couldn't append data to file {known_db}: ({e})")
		return False

def condense_dbs():
	com = f"find \"{unknown_dir}\" -name \"*.npz\""
	unknown_dbs = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	com = f"find \"{known_dir}\" -name \"*.npz\""
	known_dbs = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	for udb in unknown_dbs:
		fromdb = None
		todb = None
		fromimg = None
		toimg = None
		udbn = os.path.basename(udb)
		if udbn in known_dbs:
			kdb = known_dbs[known_dbs.index(udbn)]
			n = os.path.basename(os.path.splitext(kdb)[0])
			try:
				n = int(n)
				fromimg = f"{known_dir}/{n}.jpg"
				toimg = f"{unknown_dir}/{n}.jpg"
				fromdb = f"{known_dir}/{n}.npz"
				todb = f"{unknown_dir}/{n}.npz"
			except:
				fromimg = f"{unknown_dir}/{n}.jpg"
				toimg = f"{known_dir}/{n}.jpg"
				fromdir = f"{unknown_dir}/{n}.npz"
				todir = f"{known_dir}/{n}.npz"     
			append_db(fromdb, todb)
			if os.path.exists(fromimg):
				com = f"mv \"{fromimg}\" \"{toimg}\""
				ret = subprocess.check_output(com, shell=True).decode().strip()
				if ret != '':
					print ("Error migrating image: {ret}")
					break
			else:
				print(f"File not found: {fromimg}")



def get_name_ct(name):
	com = f"find \"{known_dir}\" -name \"{name}*.npz\""
	_list = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	return len(_list)


def get_user_input(src_img, w, h, window_title='User Input', default_text=None):
	if default_text == None:
		default_text = 'Unknown'
	input_box = sg.Input(default_text=default_text, enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)
	input_btn = sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')
	image = sg.Image(src_img, subsample=4, size=(w, h), enable_events=True, key='id_image')
	layout = [[input_box], [input_btn], [image]]
	win_w = w - 500
	win_h = h - 400
	print(w, h, win_w, win_h)
	input_window = sg.Window(window_title, layout, size=(win_w, win_h), keep_on_top=True, element_justification='center', finalize=True)
	user_input = None
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
	if user_input == None:
		user_input = default_text
	return user_input

if __name__ == "__main__":
	get_unknowns()
