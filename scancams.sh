#!/bin/bash


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
	ret="$w,$h"
	echo "$ret"
}

export SQLDB=$(python3 -c "import nv; print(nv.SQLDB)")
if [ -z "$SQLDB" ]; then
	SQLDB="$HOME/.local/lib/python3.6/nv/nv.db"
fi
echo "Sql Database: '$SQLDB'"
if [ ! -f "$SQLDB" ]; then
	sql="CREATE TABLE IF NOT EXISTS cams (camera_id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, src TEXT NOT NULL, src_2 TEXT, src_dims TEXT, src_2_dims TEXT, host_ip TEXT NOT NULL, feed TEXT NOT NULL, motion_conf TEXT NOT NULL, ptz TEXT DEFAULT 'False');"
	results=$(sqlite3 "$SQLDB" "$sql")
	if [ -n "$results" ]; then
		echo "$results"
	fi
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
	cams=$(python3 -c "import nv; print (nv.readConfToShell())" | grep -v "None")
	exists=$(echo "$cams" | grep "$HOST_IP")
	#in some cases, the exists check can be ambiguous (i.e. host=192.168.2.1 inConf="192.168.2.10")..
	if [ -n "$exists" ] && [ -z "$router" ]; then # if so...
		#do further breakdown of the first result and ensure it's a match
		IFS=$'\n' readarray checks <<< "$exists"
		for check in "${checks[@]}"; do
			chunk=$(dirname "$check")
			base_address=$(basename "$chunk" | cut -d ':' -f 1)
			if [ "$base_address" == "$HOST_IP" ]; then
				read -p "Base address in config file already. Add anyway?" yesno
				if [ "$yesno" = "y" ]; then
					export SKIP=0
				else
					export SKIP=1
				fi
			fi
		done			
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
			addurl=$(ipWebCam)
			dims=$(getDims "$addurl")
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
			feed_port=$(( 9877 + $cam_id))
			echo "export CAM_ID=$cam_id" >> "$HOST_SRCFILE"	
			feed="http://$localip:$feed_port/"
			echo "export FEED='$feed'" >> "$HOST_SRCFILE"
			echo "export PTZ='None'" >> "$HOST_SRCFILE"
			source "$HOST_SRCFILE"
			if [ -n "$HOST_IP" ] && [ -n "$SRC_DIMS" ] && [ -n "$SRC" ] && [ -n "$SRC_2" ] && [ -n "$SRC2_DIMS" ] && [ -n "$CAM_ID" ] && [ -n "$FEED" ] && [ -n "$PTZ" ]; then
				motion_conf="/etc/motion/conf.d/camera$CAM_ID.conf"
				echo "INSERT INTO cams(camera_id, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
				sql="INSERT INTO cams(camera_id, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
				results=$(sqlite3 "$SQLDB" "$sql")
				if [ -n "$results" ]; then
					echo "$results"
				else
					echo "Ok."
				fi
			fi
			export SKIP=1
		
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
							break
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
		echo "export SRC2_DIMS='$src2_dims'" >> "$HOST_SRCFILE"
		echo "Source1: '$src' ($src1_dims), Source2: '$src2' ($src2_dims)"
		cam_id=$(sqlite3 "$SQLDB" "select Count(*) from cams;")
		if [ -z "$cam_id" ]; then
			cam_id=0
		fi
		#cam_id=$(python3 -c "import nv; print(len(nv.CAMERAS))")
		cam_id=$(( cam_id + 1 ))
		echo "export CAM_ID=$cam_id" >> "$HOST_SRCFILE"
		feed_port=$(( 9876 + $cam_id))
		feed="http://$HOST_IP:$feed_port/"
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
				if [ -n "$HOST_IP" ] && [ -n "$SRC_DIMS" ] && [ -n "$SRC" ] && [ -n "$SRC_2" ] && [ -n "$SRC2_DIMS" ] && [ -n "$CAM_ID" ] && [ -n "$FEED" ] && [ -n "$PTZ" ]; then
					motion_conf="/etc/motion/conf.d/camera$CAM_ID.conf"
					echo "INSERT INTO cams(camera_id, type, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$TYPE', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
					sql="INSERT INTO cams(camera_id, type, src, src_2, src_dims, src_2_dims, host_ip, feed, motion_conf, ptz) VALUES('$CAM_ID', '$TYPE', '$SRC', '$SRC_2', '$SRC_DIMS', '$SRC_2_DIMS', '$HOST_IP', '$FEED', '$motion_conf', '$PTZ');"
					results=$(sqlite3 "$SQLDB" "$sql")
					if [ -n "$results" ]; then
						echo "$results"
					else
						echo "Ok."
					fi
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
done
