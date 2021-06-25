testauth() {
	curl -v "$url" --stderr moo.txt
	auth=$(cat moo.txt | grep "401 Unauthorized")
	if [ -n "$auth" ]; then
		auth=1
	else
		auth=0
	fi
	rm moo.txt
}

mkheader() {
	echo "<!doctype html>" > index.html
	echo "<html lang=\"en\">" >> index.html
	echo "<head>" >> index.html
	echo "	<!-- Required meta tags -->" >> index.html
	echo "	<meta charset=\"utf-8\">" >> index.html
	echo "	<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=yes\">" >> index.html
	echo "" >> index.html
	echo "	<!-- Bootstrap CSS -->" >> index.html
	echo "	<link rel=\"stylesheet\" href=\"https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css\"" >> index.html
	echo "		  integrity=\"sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO\" crossorigin=\"anonymous\">" >> index.html
	echo "" >> index.html
	echo "	<title>NicVision Stream Viewer</title>" >> index.html
	echo "<style>" >> index.html
	echo "div.gallery {" >> index.html
	echo "  margin: 5px;" >> index.html
	echo "  border: 1px solid #ccc;" >> index.html
	echo "  float: left;" >> index.html
	echo "  width: 180px;" >> index.html
	echo "}" >> index.html
	echo "" >> index.html
	echo "div.gallery:hover {" >> index.html
	echo "  border: 1px solid #777;" >> index.html
	echo "}" >> index.html
	echo "" >> index.html
	echo "div.gallery img {" >> index.html
	echo "  width: 100%;" >> index.html
	echo "  height: auto;" >> index.html
	echo "}" >> index.html
	echo "" >> index.html
	echo "div.desc {" >> index.html
	echo "  padding: 15px;" >> index.html
	echo "  text-align: center;" >> index.html
	echo "}" >> index.html
	echo "</style>" >> index.html
	echo "</head>" >> index.html
	echo "<body>" >> index.html
	echo "" >> index.html
}
if [ -d "/etc/motion/conf.d" ]; then
	sudo rm -rf /etc/motion/conf.d
fi
mkdir conf.d
cd conf.d
cams=$(python3 -c "import nv; nv.readConfToShell()")
IFS=$'\n' ary=($cams)
cam_id=0
cam_startport=9875
for item in "${ary[@]}"; do
	cam_id=$(( cam_id + 1 ))
	cam_port=$(( $cam_startport + $cam_id ))
	conffile="camera$cam_id.conf"
	local=$(echo "$item" | grep "/dev/video")
	rtsp=$(echo "$item" | grep "rtsp://")
	http=$(echo "$item" | grep "http://")
	if [ -n "$local" ]; then
		data="videodevice $item
input 0
norm 1
power_line_frequency 2
camera_id $cam_id
text_left CAMERA $cam_id
locate_motion_mode on
locate_motion_style redcross
picture_filename CAM$cam_id-%v-%Y%m%d%H%M%S-%q
stream_port $cam_port"
	elif [ -n "$rtsp" ] || [ -n "$http" ]; then
		testauth
		if [ "$auth" = 1 ]; then
			if [ -z "$user" ] || [ -z "$pass" ]; then
				read -p "Enter username: " user
				read -s -p "Enter password: " pass
			fi
			data="netcam_url $item
netcam_userpass $user:$pass
netcam_keepalive on
netcam_tolerant_check on
camera_id $cam_id
text_left CAMERA $cam_id
locate_motion_mode on
locate_motion_style redcross
picture_filename CAM$cam_id-%v-%Y%m%d%H%M%S-%q
stream_port $cam_port"
		else
			data="netcam_url $item
netcam_keepalive on
netcam_tolerant_check on
camera_id $cam_id
text_left CAMERA $cam_id
locate_motion_mode on
locate_motion_style redcross
picture_filename CAM$cam_id-%v-%Y%m%d%H%M%S-%q
stream_port $cam_port"
		fi
	fi
	if [ "$cam_id" = "1" ]; then
		conf="daemon on
process_id_file /var/run/motion/motion.pid
setup_mode off
logfile /var/log/motion/motion.log
log_level 6
log_type all
v4l2_palette 17
rotate 0
width 640
height 480
framerate 30
minimum_frame_time 0
rtsp_uses_tcp on
auto_brightness off
roundrobin_frames 1
roundrobin_skip 1
switchfilter off
threshold 1500
threshold_tune off
noise_level 32
noise_tune on
despeckle_filter EedDl
smart_mask_speed 0
lightswitch 0
minimum_motion_frames 1
pre_capture 1
post_capture 1
event_gap 60
max_movie_time 0
emulate_motion off
output_pictures off
output_debug_pictures off
quality 75
picture_type jpeg
ffmpeg_output_movies on
ffmpeg_output_debug_movies off
ffmpeg_bps 400000
ffmpeg_variable_bitrate 0
ffmpeg_video_codec mp4
ffmpeg_duplicate_frames true
snapshot_interval 0
locate_motion_mode on
locate_motion_style redcross
text_right %Y-%m-%d\n%T-%q
text_changes off
text_event %Y%m%d%H%M%S
text_double off
target_dir /var/lib/motion
snapshot_filename %v-%Y%m%d%H%M%S-snapshot
picture_filename %v-%Y%m%d%H%M%S-%q
movie_filename %v-%Y%m%d%H%M%S
timelapse_filename %Y%m%d-timelapse
ipv6_enabled off
stream_port 9876
stream_quality 50
stream_motion off
stream_maxrate 30
stream_localhost off
stream_limit 0
stream_auth_method 0
; stream_authentication user:pass
webcontrol_port 8080
webcontrol_localhost off
webcontrol_html_output on
webcontrol_authentication $user:$pass
track_type 0
track_auto off
quiet on"
		echo "$conf" > motion.conf
	fi
	echo "$data" > "$conffile"
	dir="/etc/motion/conf.d"
	echo "camera $dir/$conffile" >> motion.conf
done
cd ..
sudo mv conf.d /etc/motion/
mkheader;
cd /etc/motion/conf.d
subnet=$(ifconfig | grep "192.168" | cut -d '.' -f 3)
dev=$(ifconfig | grep "192.168" | cut -d '.' -f 4 | cut -d ' ' -f 1)
localip="192.168.$subnet.$dev"
cam_id=0
width=640
height=480
data="<!doctype html>
<html lang=\"en\">
<head>
	<!-- Required meta tags -->
	<meta charset=\"utf-8\">
	<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=yes\">

	<!-- Bootstrap CSS -->
	<link rel=\"stylesheet\" href=\"https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css\"
		  integrity=\"sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO\" crossorigin=\"anonymous\">

	<title>NicVision Stream Viewer</title>
<style>
div.gallery {
  margin: 5px;
  border: 1px solid #ccc;
  float: left;
  width: 180px;
}

div.gallery:hover {
  border: 1px solid #777;
}

div.gallery img {
  width: 100%;
  height: auto;
}

div.desc {
  padding: 15px;
  text-align: center;
}
</style>
</head>
<body>"
echo "$data" > ~/index.html

for i in $(ls *.conf | grep "camera"); do
	cam_id=$(( cam_id + 1 ))
	port=$(cat "$i" | grep "stream_port" | cut -d ' ' -f 2)
	url="http://$localip:$port"
	data="<div class=\"gallery\">
  <a target=\"_blank\" href=\"$url\">
    <img src=\"$url\" alt=\"Camera $cam_id\" width=\"$width\" height=\"$height\">
  </a>
</div>"
	echo "$data" >> ~/index.html
done
echo "</body>" >> ~/index.html
echo "</html>" >> ~/index.html
oldhtml="/var/www/html/index.html"
if [ -f "$oldhtml" ]; then
	sudo mv "$oldhtml" "$oldhtml.bak"
fi
sudo mv ~/index.html "$oldhtml"
for file in $(ls *.conf | grep "camera"); do
	port=$(cat "$file" | grep "stream_port" | cut -d ' ' -f 2)
	subnet=$(ifconfig | grep "192.168" | cut -d '.' -f 3)
	dev=$(ifconfig | grep "192.168" | cut -d '.' -f 4 | cut -d ' ' -f 1)
	url="http://192.168.$subnet.$dev:$port/"
	cam_id=$(cat "$file" | grep "camera_id" | cut -d ' ' -f 2)
	if [ -z "$line" ]; then
		line="{$cam_id: '$url'"
	else
		line="$line, $cam_id: '$url'"
	fi
done
python3 -c "import nv; motionfeeds = $line}; nv.writeConf(motionfeeds, nv.MOTION_CONF)"

