import keyring
import pickle
import os
data_dir = os.path.join(os.path.expanduser("~"), '.ipwebcam')
optsfile = os.path.join(data_dir, 'options.conf')
import requests
import json


def get_local_ip():
	com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}' | grep \"192.168\""
	return sg.subprocess.check_output(com, shell=True).decode().strip()

def init_opts(ip_address='192.168.2.22', port=6969):
	opts = {}
	base_url = f"http://{ip_address}:{port}"
	opts['motion_sensitivity'] = 250
	opts['has_auth'] =  False
	opts['user'] =  'monkey'
	opts['zoom'] =  0
	opts['ip_address'] = '192.168.2.22'
	opts['port'] = 6969
	opts['cropx'] =  0
	opts['cropy'] =  0
	opts['quality'] = 30
	opts['overlay'] = 'off'
	opts['night_vision'] = 'off'
	opts['ffc'] = 'off'
	opts['motion'] = 'off'
	opts['event'] = 1
	opts['has_auth'] =  False
	opts['video_modes'] =  ['off', 'flash', 'browser', 'java', 'js']
	opts['audio_modes'] =  ['off', 'flash', 'html5_wav', 'html5_opus']
	opts['overlay_options'] = ['on', 'off']
	opts['night_vision_options'] = ['on', 'off']
	opts['ffc_options'] = ['on', 'off']
	opts['motion_detect_options'] = ['on', 'off']
	opts['motion_range'] = {'min': 1, 'max': 1000, 'val': 293}
	opts['range_crop_x'] = {'min': 0, 'max': 100, 'value': 50}
	opts['range_crop_y'] = {'min': 0, 'max': 100, 'value': 50}
	opts['range_quality'] = {'min': 1, 'max': 100}
	opts['range_exposure'] = {'min': 1, 'max': 100}
	opts['range_motion_limit'] = {'min': 1, 'max': 1000}
	opts['range_nightvision_gain'] = {'min': 1, 'max': 240, 'value': 1}
	opts['range_nightvision_average'] = {'min': 1, 'max': 20, 'value': 1}
	opts['video_size'] = ['1920x1080', '1280x720', '960x720', '720x480', '640x480', '352x288', '320x240', '256x144', '176x144']
	opts['orientation'] = ['Landscape', 'Portrait', 'Upside down', 'Upside down portrait']
	opts['mirror_flip'] = ['None', 'Mirror', 'Flip', 'Mirror', 'Flip']
	opts['photo_sizes'] = ['4128x2322', '3264x2448', '3264x1836', '3088x3088', '2048x1536', '2048x1152', '1920x1080', '1280x720', '960x720', '720x480', '640x480', '352x288', '320x240', '256x144', '176x144']
	opts['focusmode'] = ['Manually set', 'Auto', 'manually triggered', 'Macro', 'manual', 'Smooth', 'for recording video', 'Aggressive', 'for taking photos']
	opts['range_focus_distance'] = {'min': 0, 'max':1000}
	opts['coloreffect'] = ['No effects', 'Sepia', 'Posterization', 'Aqua']
	opts['range_zoom'] = {'min': 0, 'max':100, 'value':0}
	opts['range_focal_length'] = {'min': 0, 'max':0}
	opts['flash_modes'] = ['Flash disabled', 'Auto flash', 'Always use flash', 'Red-eye reduction mode']
	opts['antibanding'] = ['Off', 'Auto']
	opts['whitebalance'] = ['whitebalance_off', 'Auto', 'Incandescent', 'Fluorescent', 'Daylight', 'Cloudy daylight']
	opts['iso_sensitivity'] = {'min': 50, 'max': 1600}
	opts['manual_exposure'] = {'min': 14000, 'max': 125000000}
	opts['urls'] = {}
	opts['urls']['audio_stream'] = f"ws://{ip_address}:{port}/audioin.wav"
	opts['urls']['circular_record'] = f"{base_url}/startvideo?force=1&mode=circular&tag=fd"
	opts['urls']['manual_record'] = f"{base_url}/startvideo?force=1&tag=fd"
	opts['urls']['zoom'] = f"{base_url}/ptz?zoom={opts['zoom']}"
	opts['urls']['cropx'] = f"{base_url}/settings/crop_x?set={opts['cropx']}"
	opts['urls']['cropy'] = f"{base_url}/settings/crop_y?set={opts['cropy']}"
	opts['urls']['stream_quality'] = f"{base_url}/settings/quality?set={opts['quality']}"
	opts['urls']['focus'] = f"{base_url}/focus"
	opts['urls']['nofocus'] = f"{base_url}/nofocus"
	opts['urls']['enable_torch'] = f"{base_url}/enabletorch"
	opts['urls']['disable_torch'] = f"{base_url}/disabletorch"
	opts['urls']['overlay'] = f"{base_url}/settings/overlay?set={opts['overlay']}"
	opts['urls']['night_vision'] = f"{base_url}/settings/night_vision?set={opts['night_vision']}"
	opts['urls']['switch_camera'] = f"{base_url}/settings/ffc?set={opts['ffc']}"
	opts['urls']['motion_detect'] = f"{base_url}/settings/motion_detect?set={opts['motion']}"
	opts['urls']['motion_sensetivity'] = f"{base_url}/settings/motion_limit?set={opts['motion_sensitivity']}"
	opts['urls']['photo'] = f"{base_url}/photo.jpg"
	opts['urls']['still'] = f"{base_url}/shot.jpg"
	opts['urls']['focused_photo'] = f"{base_url}/photoaf.jpg"
	opts['urls']['save_photo'] = f"{base_url}/photo_save_only.jpg"
	opts['urls']['save_focused_photo'] = f"{base_url}/photoaf_save_only.jpg"
	opts['urls']['tasker_event'] = f"{base_url}/gen?event=0"
	opts['urls']['browser_fullscreen'] = f"{base_url}/browserfs.html"
	opts['urls']['audio_wav'] = f"{base_url}/audio.wav"
	opts['urls']['audio_opus'] = f"{base_url}/audio.opus"
	opts['urls']['list_saved_videos'] = f"{base_url}/list_videos"
	return opts


def write_opts(opts):
	with open(optsfile, "wb") as f:
		pickle.dump(opts, f)
		f.close()


def ckdatadir():
	if not os.path.exists(data_dir):
		os.mkdir(data_dir)
	if not os.path.exists(optsfile):
		opts = init_opts()
		write_opts(opts)


def read_opts():
	try:
		with open(optsfile, "rb") as f:
			opts = pickle.load(f)
			f.close()
		return opts
	except:
		opts = init_opts()
		write_opts(opts)
		return opts
		



class ipwebcam():
	def __init__(self):
		self.opts = read_opts()
		self.ip_address = self.opts['ip_address']
		self.port = self.opts['port']
		self.opts = read_opts()
		if self.opts['has_auth']:
			pw = get_auth()
			user = self.opts['user']
			self.base_url = f"http://{user}:{pw}@{self.ip_address}:{self.port}"
		else:
			self.base_url = f"http://{self.ip_address}:{self.port}"

		self.urls = self.opts['urls']


	def get_url(self, command, *args):
		if command == audio_stream:
			url = f"ws://{args[0]}:{args[1]}/audioin.wav"
		elif command == circular_record:
			url = f"{self.base_url}/startvideo?force=1&mode=circular&tag=fd"
		elif command == manual_record:
			url = f"{self.base_url}/startvideo?force=1&tag=fd"
		elif command == zoom:
			url = f"{self.base_url}/ptz?zoom={args[0]}"
		elif command == cropx:
			url = f"{self.base_url}/settings/crop_x?set={args[0]}"
		elif command == cropy:
			url = f"{self.base_url}/settings/crop_y?set={args[0]}"
		elif command == stream_quality:
			url = f"{self.base_url}/settings/quality?set={args[0]}"
		elif command == focus:
			url = f"{self.base_url}/focus"
		elif command == nofocus:
			url = f"{self.base_url}/nofocus"
		elif command == enable_torch:
			url = f"{self.base_url}/enabletorch"
		elif command == disable_torch:
			url = f"{self.base_url}/disabletorch"
		elif command == overlay:
			url = f"{self.base_url}/settings/overlay?set={args[0]}"
		elif command == night_vision:
			url = f"{self.base_url}/settings/night_vision?set={args[0]}"
		elif command == switch_camera:
			url = f"{self.base_url}/settings/ffc?set={args[0]}"
		elif command == motion_detect:
			url = f"{self.base_url}/settings/motion_detect?set={args[0]}"
		elif command == motion_sensetivity:
			url = f"{self.base_url}/settings/motion_limit?set={args[0]}"
		elif command == photo:
			url = f"{self.base_url}/photo.jpg"
		elif command == still:
			url = f"{self.base_url}/shot.jpg"
		elif command == focused_photo:
			url = f"{self.base_url}/photoaf.jpg"
		elif command == save_photo:
			url = f"{self.base_url}/photo_save_only.jpg"
		elif command == save_focused_photo:
			url = f"{self.base_url}/photoaf_save_only.jpg"
		elif command == tasker_event:
			url = f"{self.base_url}/gen?event=0"
		elif command == browser_fullscreen:
			url = f"{self.base_url}/browserfs.html"
		elif command == audio_wav:
			url = f"{self.base_url}/audio.wav"
		elif command == audio_opus:
			url = f"{self.base_url}/audio.opus"
		elif command == list_saved_videos:
			url = f"{self.base_url}/list_videos"
		return url


	def set_auth(self):
		import getpass
		auth_key = 'ipwebcam:22:6969'
		auth_attr = 'authstring'
		pw = getpass.getpass()
		keyring.set_password(auth_key, auth_attr, pw)
		return pw


	def get_auth(self):
		auth_key = 'ipwebcam:22:6969'
		auth_attr = 'authstring'
		try:
			pw = keyring.get_password(auth_key, auth_attr)
			if pw is None:
				return self.set_auth()
			else:
				return pw
		except:
			return self.set_auth()
			


	def get_videos(self):
		pw = self.get_auth()
		url = f"http://monkey:{pw}@192.168.2.22:6969/list_videos"
		r = requests.get(url)
		data = r.text
		json_data = json.loads(r.text)
		for item in json_data:
			name = item['name']
			path = item['path']
			url = f"http://monkey:{pw}@192.168.2.22:6969/v{path}/{name}"
			outpath = f"/home/monkey/Videos/catcam/{name}"
			r = requests.get(url)
			with open(outpath, "wb") as f:
				f.write(r.content)
				f.close()
			if os.path.exists(outpath):
				url = f"http://monkey:{pw}@192.168.2.22:6969/remove{path}/{name}"
				r = requests.get(url)
				if r.status_code != 200:
					print("Error: Bad status code removing video!")
				else:
					print("OK!")
	


