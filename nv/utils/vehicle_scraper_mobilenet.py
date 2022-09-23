import cv2
import numpy as np
import sys
import pickle
import json
import urllib
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import subprocess
import os
import time
import logging
import requests
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
from nv.main.log import nv_logger
from nv.main.conf import read_opts
from nv.main.log import nv_logger
from nv.main.conf import read_opts
from nv.main.detector import detector
d = detector()
d.confidence = 0.2

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

def load_car_data(save_file='vehicles.dat'):
	with open(save_file, "rb") as f:
		data = pickle.load(f)
	f.close()
	return data



def get_image(url_image):
	image_data = requests.get(url_image)
	img = Image.open(BytesIO(image_data.content))
	return img
	#maxsize = (400, 400)
	#mw = maxsize[0]
	#mh = maxsize[1]
	#w = img.size[0]
	#h = img.size[1]
	#if w > h:
	#	r = mw / w
	#elif w < h:
	#	r = mh / h
	#elif w == h:
	#	r = mh / h
	#nw = int(w * r)
	#nh = int(h * r)
	#newsize = (nw, nh)
	#img2 = img.resize(newsize)



def get_car_data(save_file='vehicles.dat'):
	url = 'https://parseapi.back4app.com/classes/Car_Model_List?limit=100000&order=Make,Model,Year,Category'
	headers = {
	    'X-Parse-Application-Id': 'hlhoNKjOvEhqzcVAJ1lxjicJLZNVv36GdbboZj3Z',
	    'X-Parse-Master-Key': 'SNMJJF0CZZhTPhLDIqGhTlUNV9r60M2Z5spyWfXW'
	}
	log(f"Requesting data from 'back4app.com'...", 'info')
	r = requests.get(url, headers=headers)
	if r.status_code != 200:
		log(f"Error: Unable to get url \"{url}\" (Status code: {r.status_code}", 'error')
		return False
	else:
		json_data = json.loads(r.text)
		with open(save_file, "wb") as f:
			pickle.dump(json_data, f)
		f.close()
		return True

def get_data_images(html_to_parse):
	html = bs(html_to_parse, 'html.parser')
	with open ("temp.html", "w") as f:
		f.write(html_to_parse)
	f.close()
	parent='<div class="vehicle-card-main js-gallery-click-card">'
	image = 'class="vehicle-image"'
	return html.findAll('img', {'class': 'vehicle-image'})
	#print(data)
	#return html.findAll('img', {'class': '_aagt'})
	#Might possibly need further parsing to locate src tag attribute, will find out after fixing yolov3 clusterfuck.

		
def get_url(make, model, year):
	#return f"https://www.cars.com/shopping/results/?stock_type=all&makes[]={make}&models[]={make}-{model}&list_price_max=&maximum_distance=all&zip=66062
	#ensure all models are lowercast and spaces are hyphenated
	return f"https://www.cars.com/shopping/results/?maximum_distance=all&zip=66062&stock_type=all&makes[]={make}&models[]={make}-{model}&year_min={year}&year_max={year}&list_price_min=&list_price_max=&mileage_max="

def detect(image):
	cv2img = np.array(image)
	cv2img = cv2.cvtColor(cv2img, cv2.COLOR_RGB2BGR)
	dets = d.object_detect(cv2img)
	return dets
	

if __name__ == "__main__":
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument('--incognito')
	driver = webdriver.Chrome(chrome_options=chrome_options)
	dataset = "/home/monkey/.np/nv/scraped_dataset"
	save_file=f"{dataset}/vehicles.dat"
	# if save file exists, load from it and avoid web call
	if os.path.exists(save_file):
		data = load_car_data(save_file)
	else:
		#if no file found, run get_car_data to create it.
		if not get_car_data(save_file):
			print("Clusterfuck!")
			exit()
		else:
			data = load_car_data(save_file)
	if data is None:
		print("Further clusterfuckery!")
		exit()
	results = data['results']
	dbtotal = len(results)
	dbpos = 0
	log(f"Loaded {len(results)} entries from file!", 'info')
	for item in results:
		dbpos += 1
		print(f"Progress: {dbpos}/{dbtotal}")
		downloaded_images = []
		path = None
		make = item['Make']
		pmake = make.lower().replace(' ', '-')
		model = item['Model']
		pmodel = model.lower().replace(' ','-')
		year = item['Year']
		cat = item['Category']
		path = f"{dataset}/vehicles/{make}/{model}/{year}"
		#ensure directory exists...
		skip = False
		print("Path:", path)
		if os.path.exists(path):
			#comment this to re-do all
			skip = True
		else:
			skip = False
			search_url = get_url(pmake, pmodel, year)
			driver.get(search_url)
			html_to_parse = str(driver.page_source)
			all_images_data = get_data_images(html_to_parse)
			ict = len(all_images_data)
			ipos = 0
			non_downloaded_images = list(set(all_images_data) - set(downloaded_images))
			c = False
			for image_data in non_downloaded_images:
				ipos += 1
				try:
					image = get_image(image_data.attrs['src'])
					c = True
				except:
					try:
						image = get_image(image_data.attrs['data-src'])
						c = True
					except Exception as e:
						print(f"Unable to find source attribute url for jomama and her monkey pole. Details: {e}", 'info')
						c = False
						pass
				if c is True:
					print(f"Progress ({make}:{model}:{year}) {ipos}/{ict}")
					#run vehicle detection on image to ensure it can be seen by detector
					#as we're gonna use the same detector later to train
					dets = detect(image)
					targets = ['truck', 'car', 'motorbike', 'bus', 'train']
					if dets is not None and dets != []:
						name, box, confidence = dets[0]
						if name in targets:
							os.makedirs(path, exist_ok=True)
							files = next(os.walk(path))[2]
							ct = len(files) + 1
							fname = f"{make}.{model}.{year}.{cat}.{ct}.jpg"
							out_image_path = f"{path}/{fname}"
							print(f"Vehicle found in image '{out_image_path}'", 'info')
							try:
								image.save(out_image_path)
							except Exception as e:
								print("Couldn't save image (bad format???)", e)
							downloaded_images.append(image_data)
						else:
							print (f"Saw {name} in image, but no vehicle!", 'info')
	
