# import the necessary packages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
import glob
import pickle
import face_recognition
import nv
import base64
from PIL import Image
from io import StringIO
import numpy as np
import urllib.request
import json
import cv2
import os
import random
import uuid


# define the path to the face detector and smile detector
FACE_DETECTOR_PATH = "{base_path}/cascades/haarcascade_frontalface_default.xml".format(
	base_path=os.path.abspath(os.path.dirname(__file__)))

SMILE_DETECTOR_PATH = "{base_path}/cascades/haarcascade_smile.xml".format(
	base_path=os.path.abspath(os.path.dirname(__file__)))

# path to trained faces and labels
TRAINED_FACES_PATH = "{base_path}/faces".format(
	base_path=os.path.abspath(os.path.dirname(__file__)))

# maximum distance between face and match
THRESHOLD = 75

# create the cascade classifiers
detector = cv2.CascadeClassifier(FACE_DETECTOR_PATH)
smiledetector = cv2.CascadeClassifier(SMILE_DETECTOR_PATH)


@csrf_exempt
def recognize(request):
	data = {}
	image = None
	if request.method == "GET":
		if request.GET.get("imageBase64", None) is not None:
			image = _grab_image(base64_string=request.GET.get("imageBase64", None))
		else:
			url = request.GET.get("url", None)
			if url is None:
				data["error"] = "No URL provided."
				return JsonResponse(data)
			image = _grab_image(url=url)
	elif request.method == "POST":
		print (request.POST.keys())
#TODO:curl -XPOST --data @saml.txt http://www.example.net/
		if request.POST['imageBase64'] is not None:
			print ("post request properly formatted. getting image...")
			image = _grab_image(base64_string=request.POST['imageBase64'])
	if image is not None:

		name, rects = nv.recognize_raw(image)
		if name is not None:
			names, ids = nv.initDatabase('all')
			try:
				fname = name.split(' ')[0]
				lname = name.split(' ')[1]
				user_test1 = User.objects.get(first_name=fname)
				user_test2 = User.objects.get(last_name=lname)
				if user_test1 is not None and user_test2 is not None:
					user = {
					   	"first_name" : user_test1.first_name,
					   	"last_name" : user_test1.last_name,
					   	"username" : user_test1.username,
					   	"email" : user_test1.email,
					   	"id" : user_test1.pk,
					   }
				data.update({"detected": True, "registered": True, "user": user, "box": rects})

			except  User.DoesNotExist:
				os.chdir(nv.UNKNOWN_FACES_PATH)
				unknowns = glob.glob('*.jpg')
				ct = len(unknowns)
				ct = ct + 1
				fname = (nv.UNKNOWN_FACES_PATH + nv.sep + name + "." + str(ct) + ".jpg")
				cv2.imwrite(fname, image)
				data.update({"detected": True, "name": name, "registered": False, "box": rects})
		else:
			data.update({"detected": False, "registered": False, "user": "Unknown Person"})
		return JsonResponse(data)

@csrf_exempt
def train(request):
	data = {}
	try:
		with open(nv.KNOWN_FACES_DB, 'rb') as f:
			all_face_encodings = pickle.load(f)
			known_names = list(all_face_encodings.keys())
		f.close()
	except:
		all_face_encodings = {}
		known_names = []
	if request.method == "GET":
		if request.GET.get("imageBase64", None) is not None and request.GET.get("user", None) is not None :
			image = _grab_image(base64_string=request.GET.get("imageBase64", None))
		elif request.GET.get("url", None) is not None and request.GET.get("user", None) is not None:
			url = request.GET.get("url", None)
			if url is None:
				data["error"] = "No URL provided."
				return JsonResponse(data)
			image = _grab_image(url=url)
		name = str(request.GET.get("user", None))
		print ("Name:", name)
		pos = 0
		for test in known_names:
			if name in test:
				pos = pos + 1
		pos = pos + 1
		addname = (name + "_" + str(pos))
		face_encoding = face_recognition.face_encodings(image)[0]
		result = nv.updateDbFile(addname, face_encoding)
		if result is True:
			data["success"] = ("Added face to " + name + "'s registry in position " + str(pos) + "!")
		elif result is False:
			data["failure"] = ("No face found in image.")
		return JsonResponse(data)
		#except:
		#	data["error"] = "No face detected."
		#	return JsonResponse(data)



@csrf_exempt
def new(request):
	if request.method == "GET":
		if request.GET.get("username", None) is not None and request.GET.get("email", None) is not None:
			user = User.objects.create_user(request.GET.get("username", None), request.GET.get("email", None), '')
			user.save()
	return JsonResponse({"sucess": True})

@csrf_exempt
def users(request):
	users = [{"first_name" : user.first_name, "last_name": user.last_name, "id" : user.pk} for user in User.objects.all()]

	return JsonResponse({"users" : users})

def _grab_image(path=None, base64_string=None, url=None):
	if path is not None:
		image = cv2.imread(path)
	else:
		if url is not None:
			with urllib.request.urlopen(url) as resp:
				data = resp.read()
				image = np.asarray(bytearray(data), dtype="uint8")
				image = cv2.imdecode(image, cv2.IMREAD_COLOR)
		elif base64_string is not None:
			image = base64.b64decode(base64_string)
			image = np.fromstring(image, dtype=np.uint8)
			image = cv2.imdecode(image, 1)
	return image
