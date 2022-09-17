import subprocess
import os
import time
import requests
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
from nv.main.yolov3 import yolov3
from nv.main.log import nv_logger
from nv.main.conf import read_opts

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

class InstaBot():
	def __init__(self):
		opts = read_opts(0)
		self.path_out = opts['detector']['scraper']['path_out']
		authstring = self.auth()
		self.user = authstring.split(':')[0]
		self.password  = authstring.split(':')[1]
		chrome_options = webdriver.ChromeOptions()
		chrome_options.add_argument('--incognito')
		self.driver = webdriver.Chrome(chrome_options=chrome_options)
		self.yolov3 = yolov3()

	@staticmethod
	def get_image(url_image):
		image_data = requests.get(url_image)
		image_data_content = image_data.content
		return Image.open(BytesIO(image_data_content))

	def save_image(self, image, label):
		out_folder_path = os.path.join(self.path_out, label)
		os.makedirs(out_folder_path, exist_ok=True)
		out_image_path = os.path.join(out_folder_path, '{}.jpg'.format(str(time.time())))
		image.save(out_image_path)
		log(f"Image saved to \"{out_image_path}\"", 'info')

	def labels_in_image(self, image):
		return list(set(self.yolov3(image=image)))

	def get_data_images(self):
		html_to_parse = str(self.driver.page_source)
		html = bs(html_to_parse, 'html.parser')
		#Might possibly need further parsing to locate src tag attribute, will find out after fixing yolov3 clusterfuck.
		return html.findAll('img', {'class': '_aagt'})
		#log(f"Data: {data}", 'info')
		#return data

	def download_images(self):
		"""Main process to find, filter and download the images.
		   Obtaining the images by scrolling and using the yolov3 to check if it includes what we are looking for.
		"""
		downloaded_images = []
		r_scroll_h = 'return document.body.scrollHeight'
		scroll_h = 'window.scrollTo(0, document.body.scrollHeight);'

		lh = self.driver.execute_script(r_scroll_h)
		while True:
			self.driver.execute_script(scroll_h)
			self.driver.implicitly_wait(1)
			nh = self.driver.execute_script(r_scroll_h)

			if nh == lh:
				self.driver.execute_script(scroll_h)
				continue
			else:
				lh = nh
				self.driver.implicitly_wait(1)

			all_images_data = self.get_data_images()
			non_downloaded_images = list(set(all_images_data) - set(downloaded_images))
			for image_data in non_downloaded_images:
				try:
					image = self.get_image(image_data.attrs['src'])
					labels = self.labels_in_image(image)
					for label in labels:
						if label in ['dog', 'cat']:
							self.save_image(image, label)
							downloaded_images.append(image_data)
				except Exception as e:
					log(f"Error downloading an image: {e}", 'error')

	def __call__(self, *args, **kwargs):
		self.driver.get('https://instagram.com')
		self.driver.implicitly_wait(2)
		self.driver.find_element(by='xpath', value='//input[@name=\"username\"]').send_keys(self.user)
		self.driver.find_element(by='xpath', value='//input[@name=\"password\"]').send_keys(self.password)

		self.driver.find_element(by='xpath', value='//button[@type=\"submit\"]').click()
		self.driver.implicitly_wait(4)
		self.driver.find_element(by='xpath', value='//button[contains(text(), "Not Now")]').click()  # "Ahora no" in spanish
		self.driver.implicitly_wait(4)

		self.driver.find_element(by='xpath', value='//input[@type=\"text\"]').send_keys('#PETS')
		time.sleep(3)
		for _ in range(2):
			self.driver.find_element(by='xpath', value='//input[@type=\"text\"]').send_keys(Keys.ENTER)

		self.download_images()

	def auth(self):
		try:
			return self._get_auth()
		except Exception as e:
			log(f"Couldn't get credentials from keystore! Please re-enter Instagram credentials (fomat: 'username:password')", 'warning')
			if self._set_auth():
				log(f"Success!", 'info')
				return self._get_auth()
				

	def _get_auth(self):
		return subprocess.check_output(f"secret-tool lookup instagram authstr", shell=True).decode().strip()


	def _set_auth(self):
		ret = subprocess.check_output(f"secret-tool store --label=\"instagram_scraper\" instagram authstr", shell=True).decode.strip()
		if ret != '':
			log(f"Error saving password: {ret}", 'error')
			return False
		else:
			return True

if __name__ == '__main__':
	bot = InstaBot()
	bot()
