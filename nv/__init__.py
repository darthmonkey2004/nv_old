
#This is a work in progress, and I'm no python pro. So of course input, and any suggestions, is amazingly appreciated.
#-Matt
#darthmonkey2004@gmail.com
#NOTE: boxes should be in dlib rectangle format: (l,t,r,b)
#dlib rectangle objects are (l,t,r,b)
import os
import cv2
from nv.main.conf import readConf, writeConf
from nv.main.mkhtml import mkhtml
from nv.main import process as process
from nv.utils.kill_nv import kill_nv as quit
red = (255, 0, 0)
orange = (255, 127.5, 0)
yellow = (255, 255, 0)
green = (0, 255, 0)
blue = (0, 255, 255)
indigo = (0, 0, 255)
violet = (255, 0, 255)
colors = [red, orange, yellow, green, blue, indigo, violet]
