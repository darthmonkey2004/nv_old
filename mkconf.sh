#!/bin/bash
SQLDB=$(python3 -c "import nv; print(nv.SQLDB)")
cam_ids=$(sqlite3 "$SQLDB" "select camera_id from cams;")
confpath="/etc/motion/motion.conf"
if [ -f "$confpath" ]; then
	sudo mv "$confpath" "confpath.bak"
fi
mainconf="motion.conf"
if [ -f "$mainconf" ]; then
	rm "$mainconf"
fi
user="$USER"
password=$(secret-tool lookup bubblecam password)
data='daemon on
process_id_file /var/run/motion/motion.pid
setup_mode off
logfile /var/log/motion/motion.log
log_level 6
log_type all
videodevice /dev/video3
v4l2_palette 17
; tunerdevice /dev/tuner0
input 0
norm 1
frequency 0
power_line_frequency 2
rotate 0
width 640
height 480
framerate 10
minimum_frame_time 0
netcam_keepalive off
netcam_tolerant_check off
rtsp_uses_tcp on
auto_brightness off
brightness 0
contrast 0
saturation 0
hue 0
roundrobin_frames 1
roundrobin_skip 1
switchfilter off
threshold 1500
threshold_tune off
noise_level 32
noise_tune on
despeckle_filter EedDl
minimum_motion_frames 1
pre_capture 0
post_capture 0
event_gap 60
max_movie_time 0
emulate_motion off
output_pictures off
output_debug_pictures off
quality 75
picture_type jpeg
ffmpeg_output_movies off
ffmpeg_output_debug_movies off
ffmpeg_timelapse 0
ffmpeg_timelapse_mode daily
ffmpeg_bps 400000
ffmpeg_variable_bitrate 0
ffmpeg_video_codec mpeg4
ffmpeg_duplicate_frames true
use_extpipe off
snapshot_interval 0
locate_motion_mode on
locate_motion_style redcross
text_right %Y-%m-%d\n%T-%q
; text_left CAMERA %t
text_changes off
text_event %Y%m%d%H%M%S
text_double off
;exif_text %i%J/%K%L
snapshot_filename %v-%Y%m%d%H%M%S-snapshot
picture_filename %v-%Y%m%d%H%M%S-%q
movie_filename %v-%Y%m%d%H%M%S
timelapse_filename %Y%m%d-timelapse
ipv6_enabled off
stream_quality 50
stream_motion off
stream_maxrate 100
stream_localhost off
stream_limit 0
stream_auth_method 0
stream_authentication admin:password
'
data2="webcontrol_port 8080
webcontrol_localhost off
webcontrol_html_output on
webcontrol_authentication $user:$password
"
data3='track_type 0
track_auto off
;track_port /dev/ttyS0
;track_motorx 0
;track_motorx_reverse 0
;track_motory 1
;track_motory_reverse 0
;track_maxx 200
;track_minx 50
;track_maxy 200
;track_miny 50
;track_homex 128
;track_homey 128
track_iomojo_id 0
track_step_angle_x 10
track_step_angle_y 10
track_move_wait 10
track_speed 255
track_stepsize 40
quiet on
; camera /etc/motion/conf.d/camera1.conf'
echo "$data" > "$mainconf"
echo "$data1" >> "$mainconf"
echo "$data2" >> "$mainconf"
cams=($cam_ids)
if [ ! -d /etc/motion/conf.d ]; then
	sudo mkdir /etc/motion/conf.d
fi
for cam_id in "${cams[@]}"; do
	conf="camera$cam_id.conf"
	data=$(sqlite3 "$SQLDB" "select type,src,src_dims,feed from cams where camera_id = '$cam_id';")
	type=$(echo "$data" | cut -d '|' -f 1)
	src=$(echo "$data" | cut -d '|' -f 2)
	src_dims=$(echo "$data" | cut -d '|' -f 3)
	h=$(echo "$src_dims" | cut -d ' ' -f 1 | cut -d ',' -f 1 | cut -d '(' -f 2)
	w=$(echo "$src_dims" | cut -d ' ' -f 2 | cut -d ')' -f 1)
	echo "height $h" > "$conf"
	echo "width $w" >> "$conf"
	echo "camera_id $cam_id" >> "$conf"
	echo "Type: '$type'"
	stream_port=$(echo "$data" | cut -d '|' -f 4 | cut -d ':' -f 3 | cut -d '/' -f 1)
	echo "stream_port $stream_port" >> "$conf"
	echo "stream_quality 50" >> "$conf"
	echo "stream_localhost off" >> "$conf"
	echo "stream_limit 0" >> "$conf"
	if [ "$type" == 'net' ]; then
		echo "netcam_url $src" >> "$conf"
		echo "netcam_keepalive yes" >> "$conf"
		echo "netcam_tolerant_check on" >> "$conf"

	elif [ "$type" == "v4l2" ]; then
		echo "videodevice $src" >> "$conf"
		echo "input 0" >> "$conf"
		echo "norm = 1" >> "$conf"
		echo "v4l2_palette = 17" >> "$conf"
	fi
	echo "camera /etc/motion/conf.d/$conf" >> motion.conf
	sudo mv "$conf" "/etc/motion/conf.d/$conf"
done
if [ -n $(pgrep motion) ]; then
	sudo kill $(pgrep motion)
fi
if [ -f /etc/motion/motion.conf ]; then
	sudo mv /etc/motion/motion.conf /etc/motion/motion.conf.bak
fi
sudo mv motion.conf /etc/motion/motion.conf
if [ -f /var/log/motion.log ]; then
	sudo rm /var/log/motion.log
fi
sudo touch /var/log/motion/motion.log
sudo chown /var/log/motion/motion.log motion
sudo chmod a+rwx /var/log/motion/motion.log
sudo motion -c /etc/motion/motion.conf
