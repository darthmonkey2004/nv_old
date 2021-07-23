#!/bin/bash


#TODO: get previous cam entries from sql database instead of CONF file, until I can phase out CONF entirely in nv
testIpCam() {
	ip="$1"
	port="$2"
	readarray ary <<< $(nmap -sV --script "rtsp-*" -p $port $ip | grep -v "Nmap done:")
	go=''
	stop=''
	start="discovered:"
	end="other responses:"
	results=()
	urls=()
	for i in "${ary[@]}"; do
		line=$(echo "$i" | cut -d $'\n' -f 1)
		test=$(echo "$line" | grep "$start")
		if [ -n "$test" ]; then
			go=1
		fi
		test=$(echo "$line" | grep "$end")
		if [ -n "$test" ]; then
			stop=1
		fi
		if [ -n "$go" ] && [ -n "$stop" ]; then
			break
		fi
		if [ -n "$go" ] && [ -z "$top" ]; then
			line=$(echo "$line" | xargs | cut -d ' ' -f 2)
			d=$(echo "$line" | grep "discovered")
			if [ -z "$d" ]; then
				results+=("$line")
			fi
		fi
	done
	pos=0
	for i in "${results[@]}"; do
		pos=$(( pos + 1 ))
		fname="temp.$pos.jpg"
		ffmpeg -loglevel quiet -stats -y -rtsp_transport tcp -i "$i" -frames:v 1 $fname
		if [ -f "$fname" ]; then
			#xdg-open "$fname"
			info=$(jpeginfo "$fname" | xargs)
			h=$(echo "$info" | cut -d ' ' -f 4)
			w=$(echo "$info" | cut -d ' ' -f 2)
			urls+=("$i($h,$w)")
			rm "$fname"
		fi
	done
	first="${urls[0]}"
	if [ -z "$first" ]; then
		urls=()
	fi
	echo "${urls[@]}"
}

getPort() { 
	url="$1"
	services=$(nmap "$url")
	rtsp=$(echo "$services" | grep "rtsp" | cut -d '/' -f 1)
	rtmp=$(echo "$services" | grep "rtmp" | cut -d '/' -f 1)
	ipwebcam=$(echo "$services" | grep "sd" | cut -d '/' -f 1)
	if [ -n "$ipwebcam" ]; then
		if [ "$ipwebcam" = "9876" ]; then
			ret=$ipwebcam
		else
			export SKIP=1
			ret=''
		fi
	fi
	if [ -n "$rtmp" ]; then
		ret=$rtmp
	fi
	if [ -n "$rtsp" ]; then
		ret=$rtsp
	fi
	if [ -z "$ret" ]; then
		ret=''
	fi
	echo "$ret"
}

scanNetwork() {
	subnet="192.168.2"
	iprange="$subnet.0/24"
	readarray iplist <<< $(nmap -sn $iprange | grep "$subnet")
	hosts=()
	for i in "${iplist[@]}"; do
		testname=$(echo $i | grep "(*)")
		if [ -n "$testname" ]; then
			ip=$(echo $i | cut -d ' ' -f 6 | cut -d ')' -f 1 | cut -d '(' -f 2)
		else
			ip=$(echo $i | cut -d ' ' -f 5)
		fi
		hosts+=("$ip")
	done
echo "${hosts[@]}"
}

getLocalIp() {
	ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}'
}

ipWebCam() {
	ip="$1"
	port="$2"
	read -p "Does this camera have authentication? (y/n): " yn
	if [ "$yn" = "y" ]; then
		read -p "Enter username for video stream:" user
		read -s -p "Enter password: " pass
		addurl="rtsp://$user:$pass@$ip:$port/h264_pcm.sdp"
	else
		addurl="rtsp://$ip:$port/h264_pcm.sdp"
	fi
	echo "$addurl"
}





getDims() {
	if [ -n "$1" ]; then
		src="$1"
	fi
	data=$(mplayer -vo null -ao null -identify -frames 0 $src)
	w=$(echo "$data" | grep "ID_VIDEO_WIDTH=" | cut -d '=' -f 2)
	h=$(echo "$data" | grep "ID_VIDEO_HEIGHT=" | cut -d '=' -f 2)
	#echo "w='$w'" >> "$HOST_SRCFILE"
	#echo "h='$h'" >> "$HOST_SRCFILE"
	ret="($w, $h)"
	echo "$ret"
}

export SQLDB=$(python3 -c "import nv; print(nv.SQLDB)")
if [ -z "$SQLDB" ]; then
	SQLDB="$HOME/.local/lib/python3.6/nv/nv.db"
fi
echo "Sql Database: '$SQLDB'"
if [ -f "$SQLDB" ]; then
	echo "Database exists! Choose an option..."
	echo "1. Backup old and start fresh"
	echo "2. Merge with current database"
	read -p "Enter choice number: " pick
	if [ "$pick" = "1" ] || [ -z "$pick" ]; then
		echo "Backing up old database."
		mv "$SQLDB" "$SQLDB.bak"
	elif [ "$pick" = "2" ]; then
		echo "Keeping current database."
	else
		echo "Keeping current database."
	fi
fi
sql="CREATE TABLE IF NOT EXISTS cams (camera_id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, src TEXT NOT NULL, src_2 TEXT, src_dims TEXT, src_2_dims TEXT, host_ip TEXT NOT NULL, feed TEXT NOT NULL, motion_conf TEXT NOT NULL, ptz TEXT DEFAULT 'False');"
results=$(sqlite3 "$SQLDB" "$sql")
if [ -n "$results" ]; then
	echo "$results"
fi
#TODO: sql table insertion function
export HOST_SRCFILE="$HOME/.local/lib/python3.6/site-packages/nv/host.src"

localip=$(getLocalIp)
if [ -z "$localip" ]; then
	echo "Error: No network hardware seems to be connected. Solve this problem and try again."
	exit 1
fi
net1=$(echo "$localip" | cut -d '.' -f 1)
net2=$(echo "$localip" | cut -d '.' -f 2)
net3=$(echo "$localip" | cut -d '.' -f 3)
subnet="$net1.$net2.$net3"
echo "Executing search on local subnet ($subnet)..."
hosts=$(scanNetwork)
hosts=($hosts)
localip=$(getLocalIp)
echo "Scan complete. Found total of "${#hosts[@]}" online hosts. Beginning service discovery..."
for HOST_IP in "${hosts[@]}"; do
	if [ -f "$HOST_SRCFILE" ]; then
		rm "$HOST_SRCFILE"
	fi
	echo "Testing: '$HOST_IP'.."
	router=''
	export SKIP=0
	if [ "$HOST_IP" == "$localip" ]; then
		echo "Skipping local ip address.."
		export SKIP=1
	fi
	if [ "$HOST_IP" == "$subnet.1" ]; then
		echo "local router found. Skipping..."
		export SKIP=1
		router=1
	fi
	SQLDB=$(python3 -c "import nv; print(nv.SQLDB)")
	exists=$(sqlite3 "$SQLDB" "select camera_id from cams where host_ip = '$HOST_IP';")
	echo "Exists: '$exists'"
	#in some cases, the exists check can be ambiguous (i.e. host=192.168.2.1 inConf="192.168.2.10")..
	if [ -n "$exists" ]; then
		read -p "Ip address found in database, camera id '$exists'. Add anyway? " yn
		if [ "$yn" = "y" ]; then
			SKIP=0
		else
			SKIP=1
		fi
	fi
	echo "Skip = $SKIP"
	if [ "$SKIP" = "0" ]; then
		echo "Scanning host: '$HOST_IP'..."
		PORT=$(getPort $HOST_IP)
		if [ -z "$PORT" ]; then
			export SKIP=1
		fi
	fi
	if [ "$SKIP" = "0" ]; then
		if [ "$PORT" == "9876" ]; then
			addurl=$(ipWebCam $HOST_IP $PORT)
			dims=$(getDims "$addurl")
			TYPE='net'
			echo "export HOST_IP='$HOST_IP'" >> "$HOST_SRCFILE"
			echo "export TYPE='net'" >> "$HOST_SRCFILE"
			echo "export SRC='$addurl'" >> "$HOST_SRCFILE"
			echo "export SRC_2='None'" >> "$HOST_SRCFILE"
			echo "export SRC_DIMS='$dims'" >> "$HOST_SRCFILE"
			echo "export SRC2_DIMS='None'" >> "$HOST_SRCFILE"
			cam_id=$(sqlite3 "$SQLDB" "select Count(*) from cams;")
			if [ -z "$cam_id" ]; then
				cam_id=0
			fi
			#cam_id=$(python3 -c "import nv; print(len(nv.CAMERAS))")
			cam_id=$(( cam_id + 1 ))
			motion_conf="/etc/motion/conf.d/camera$cam_id.conf"
			feed_port=$(( 9876 + $cam_id))
			echo "export CAM_ID=$cam_id" >> "$HOST_SRCFILE"	
			feed="http://$localip:$feed_port/"
			echo "export FEED='$feed'" >> "$HOST_SRCFILE"
			echo "export PTZ='None'" >> "$HOST_SRCFILE"
			source "$HOST_SRCFILE"
			export SRC_2_DIMS=None
			if [ -n "$HOST_IP" ] && [ -n "$SRC_DIMS" ] && [ -n "$SRC" ] && [ -n "$SRC_2" ] && [ -n "$SRC_2_DIMS" ] && [ -n "$CAM_ID" ] && [ -n "$FEED" ] && [ -n "$PTZ" ] && [ -n "$TYPE" ]; then
				motion_conf="/etc/motion/conf.d/camera$CAM_ID.conf"
				echo "INSERT INTO cams(camera_id, type, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$TYPE', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
				sql="INSERT INTO cams(camera_id, type, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$TYPE', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
				results=$(sqlite3 "$SQLDB" "$sql")
				if [ -n "$results" ]; then
					echo "$results"
				else
					echo "Ok."
				fi
				SKIP=1
			else
				echo "Vars not set:"
				echo "CAM_ID='$CAM_ID', TYPE='$TYPE', SRC='$SRC', SRC_2='$SRC_2', SRC_DIMS='$SRC_DIMS', SRC_2_DIMS='$SRC_2_DIMS', HOST_IP='$HOST_IP', FEED='$FEED', motion_conf='$motion_conf', PTZ='$PTZ'"
				export SKIP=1
			fi
		
		else
			urls=$(testIpCam $HOST_IP $PORT)
			urls=($urls)
			pos=0
			ary=()
			ct="${#urls[@]}"
			if [ "$ct" = "0" ]; then
				secs=0
				attempts=1
				while [ "$attempts" != "3" ]; do
					sleep 15
					urls=$(testIpCam $HOST_IP $PORT)
					urls=($urls)
					pos=0
					ary=()
					ct="${#urls[@]}"
					if [ "$ct" = "0" ]; then
						attempts=$(( attempts + 1 ))
					else
						urls=$(testIpCam "$auth:$HOST_IP" $PORT)
						urls=($urls)
						ct="${#urls[@]}"
						if [ "$ct" = "0" ]; then
							echo "Still failed. Aborting validation for '$HOST_IP:$port' ('$user:$pass')..."
							export SKIP=1
						fi
					fi
				done
			fi
			echo "Results=$ct, ${urls[@]}'"
			echo "export HOST_IP=$HOST_IP" > "$HOST_SRCFILE"
			echo "Good urls: $ct"
			if [ "$ct" == 0 ]; then
				echo "Couldn't find good urls. Skipping..."
				export SKIP=1
			fi
		fi
	fi
	if [ "$SKIP" == "0" ]; then
		for u in "${urls[@]}"; do
			pos=$(( pos + 1 ))
			echo "$pos. $u"
		done
		read -p "Enter a number of the resolution/url to use (Primary stream): " num1
		read -p "Select secondary url: (blank for None): " num2
		#adjust entered number to account for arrays starting at 0
		num1=$(( num1 - 1 ))
		str="${urls[$num1]}"
		src1=$(echo "$str" | cut -d '(' -f 1)
		dims=$(echo "$str" | cut -d '(' -f 2 | cut -d ')' -f 1)
		w=$(echo "$dims" | cut -d ',' -f 1)
		h=$(echo "$dims" | cut -d ',' -f 2)
		src1_dims="($w, $h)"
		if [ -n "$num2" ]; then
			num2=$(( num2 - 1 )) #adjust for zero array element numbering
			str="${urls[$num2]}" #grab secondary url
			src2=$(echo "$str" | cut -d '(' -f 1)
			dims2=$(echo "$str" | cut -d '(' -f 2 | cut -d ')' -f 1)
			w2=$(echo "$dims2" | cut -d ',' -f 1)
			h2=$(echo "$dims2" | cut -d ',' -f 2)
			src2_dims="($w2, $h2)"
		else
			src2="None" #initialize default null url
		fi
		echo "export TYPE='net'" >> "$HOST_SRCFILE"
		echo "export SRC='$src1'" >> "$HOST_SRCFILE"
		echo "export SRC_2='$src2'" >> "$HOST_SRCFILE"
		echo "export SRC_DIMS='$src1_dims'" >> "$HOST_SRCFILE"
		echo "export SRC_2_DIMS='$src2_dims'" >> "$HOST_SRCFILE"
		echo "Source1: '$src' ($src1_dims), Source2: '$src2' ($src2_dims)"
		cam_id=$(sqlite3 "$SQLDB" "select Count(*) from cams;")
		if [ -z "$cam_id" ]; then
			cam_id=0
		fi
		#cam_id=$(python3 -c "import nv; print(len(nv.CAMERAS))")
		cam_id=$(( cam_id + 1 ))
		echo "export CAM_ID=$cam_id" >> "$HOST_SRCFILE"
		feed_port=$(( 9876 + $cam_id))
		feed="http://$localip:$feed_port/"
		echo "export FEED='$feed'" >> "$HOST_SRCFILE"
		read -p "Add ptz url? (n to skip)" yesno
		if [ "$yesno" == "n" ] || [ -z "$yesno" ]; then
			ptz="False"
		elif [ "$yesno" != "y" ] && [ -n "$yesno" ]; then
			ptz="$yesno"
		else
			read -p "Enter ptz url: " ptz
			isurl=$(echo "$ptz" | grep "http" | grep "://")
			if [ -z "$isurl" ]; then
				echo "PTZ url looks bad. Sorry about your luck..."
				ptz='None'
			fi
		fi
		echo "export PTZ='$ptz'" >> "$HOST_SRCFILE"
		if [ "$SKIP" = "0" ]; then
			echo "Skip = '$SKIP'. Executing addCam..."
			echo "$HOST_SRCFILE"
			if [ ! -f "$HOST_SRCFILE" ]; then
				echo "src file not found!"
			else
				cat "$HOST_SRCFILE"
				source "$HOST_SRCFILE"
				if [ -n "$HOST_IP" ] && [ -n "$SRC_DIMS" ] && [ -n "$SRC" ] && [ -n "$SRC_2" ] && [ -n "$SRC_2_DIMS" ] && [ -n "$CAM_ID" ] && [ -n "$FEED" ] && [ -n "$PTZ" ] && [ -n "$TYPE" ]; then
					motion_conf="/etc/motion/conf.d/camera$CAM_ID.conf"
					echo "INSERT INTO cams(camera_id, type, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$TYPE', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
					sql="INSERT INTO cams(camera_id, type, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$TYPE', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
					results=$(sqlite3 "$SQLDB" "$sql")
					if [ -n "$results" ]; then
						echo "$results"
					else
						echo "Ok."
					fi
				else
					echo "SQL not witten! (HOST_IP='$HOST_IP', SRC_DIMS='$SRC_DIMS', SRC='$SRC', SRC_2='$SRC_2', SRC2_DIMS='$SRC2_DIMS', CAM_ID='$CAM_ID', FEED='$FEED', PTZ='$PTZ')"
				fi
			fi
		fi
	fi
done
ok="Video input : 0 (Composite0: ok)"
readarray devs <<< $(ls /dev/video*)
ct=$(sqlite3 "$SQLDB" "select Count(*) from cams;")
localip=$(getLocalIp)
for dev in "${devs[@]}"; do
	CAM_ID=$(( ct + 1 ))
	echo "Count: $ct, id: $CAM_ID"
	dev=$(echo "$dev" | cut -d $'\n' -f 1)
	if [ -n "$dev" ]; then
		exists=$(sqlite3 "$SQLDB" "select camera_id from cams where src like '%$dev%';")
		if [ -n "$exists" ]; then
			echo "Device already in database. skipping..."
			SKIP=1
		else
			SKIP=0
		fi
		if [ "$SKIP" = "0" ]; then
			data=$(v4l2-ctl -d "$dev" --all)
			isok=$(echo "$data" | grep "Video input :" | grep ": ok")
			input=$(echo "$data" | grep "Video input :"  | cut -d ' ' -f 4)
			if [ -n "$isok" ]; then
				str=$(echo "$data" | grep "Selection: crop_default")
				w=$(echo "$str" | cut -d ' ' -f 8 | cut -d ',' -f 1)
				h=$(echo "$str" | cut -d ' ' -f 10)
				std=$(echo "$data" | grep "NTSC")
				if [ -n "$std" ]; then
					std=1
				fi
				
				echo "Device: '$dev', Input: '$input', ($w, $h), Standard: '$std'"
				FEED_PORT=$(( 9877 + $CAM_ID))
				HOST_IP='localhost'
				FEED="http://$localip:$FEED_PORT/"
				TYPE=v4l2
				SRC="$dev"
				SRC_2='None'
				SRC_DIMS="($w, $h)"
				SRC_2_DIMS='None'
				PTZ='None'
				motion_conf="/etc/motion/conf.d/camera$CAM_ID.conf"
				sql="INSERT INTO cams(camera_id, type, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$TYPE', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
				results=$(sqlite3 "$SQLDB" "$sql")
			fi
		fi
	fi
done
motionrunning=$(pgrep motion)
if [ -n "$motionrunning" ]; then
	sudo kill $(pgrep motion)
fi
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
sudo chown motion /var/log/motion/motion.log
sudo chmod a+rwx /var/log/motion/motion.log
echo "Starting motion..."
sleep 2
sudo motion -c /etc/motion/motion.conf
cd "$HOME/.local/lib/python3.6/site-packages/nv"
python3 mkhtml.py
pid=$(pgrep nv)
if [ -n "$pid" ]; then
	nv kill
fi
nv
