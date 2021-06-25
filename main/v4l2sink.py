import cv2
import fcntl
import v4l2
import urllib.request
import argparse

#wav="http://192.168.2.8:9876/audio.wav"# the audio stream in Wav format.
#aac="http://192.168.2.8:9876/audio.aac"# the audio stream in AAC format (if supported by hardware).
#opus="http://192.168.2.8:9876/audio.opus"# the audio stream in Opus format.
#url = "http://192.168.2.8:9876/videofeed"

parser = argparse.ArgumentParser(
    description='NicVision: IP Camera Facial Recognition',
)

parser.add_argument('-s, --src', action="store", dest="src", default=0, help="Source of the video stream to grab. Can be an IP camera or other video stream (url), local device (int devID), or a local file or image path (str filepath).")
parser.add_argument('-d, --device', action="store", dest="device", required=True, help="The v4l2loopback device to use for the stream's local device node (v4l2).")
args = parser.parse_args()
try:
	#test to see if input can be assigned as an integer. If so, it's a local video device id.
	src = int(args.src)
except:
	#if not, it's probably a filepath or network string.
	src = str(args.src)

device = str(args.device)

cap = cv2.VideoCapture(src)
ret,img = cap.read()
height,width,channels = img.shape
global DEVICE
DEVICE = open(device, 'wb')
format = v4l2.v4l2_format()
format.type = v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT
format.fmt.pix.field = v4l2.V4L2_FIELD_NONE
format.fmt.pix.pixelformat = v4l2.V4L2_PIX_FMT_RGB24
format.fmt.pix.width = width
format.fmt.pix.height = height
format.fmt.pix.bytesperline = width * channels
format.fmt.pix.sizeimage = width * height * channels
print ("set format result (0 is good):{}".format(fcntl.ioctl(DEVICE, v4l2.VIDIOC_S_FMT, format)))
while True:
	try:
		ret,img = cap.read()
		if ret:
			DEVICE.write(img)
	except:
		continue
#TODO: Create audio capture method using pyaudio to write to a sound device.
# v4l2loopback doesn't separate audio streams unless muxed into the video stream. Best option is 'chunk' style distribution if stream has audio.
#	audio_stream = urllib.request.urlretrieve(wav, "stream.wav")
#	loop = AudioSegment.from_wav("stream.wav")
#	try:
#		for block in r.iter_content(1024):
#			DEVICE.write(loop)
#	except:
#		continue
#"Content-Type": "audio/vnd.wav;codec=1" for regular PCM.
#set <audio>preload="none"</audio>prevent browser buffering/caching.



