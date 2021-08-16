#!/bin/bash


exec_dir="$HOME/.local/lib/python3.6/site-packages/nv/main"
SQLDB="$HOME/.local/lib/python3.6/site-packages/nv/main/nv.db"
process_exec="$exec_dir/process.py"
capture_exec="$exec_dir/serve.py"

ckMotion() {
	motion_running=$(pgrep motion)
	if [ -z "$motion_running" ]; then
		echo 0
	else
		echo 1
	fi
}
ckNV() {
	nv_running=$(pgrep python3)
	if [ -n "$nv_running" ]; then
		echo 1
	else
		echo 0
	fi
}
killMotion() {
	state=$(ckMotion)
	if [ "$state" = "1" ]; then
		echo "Stopping motion..."
		sudo kill $(pgrep motion)
		echo "$state"
	fi
}
killNv() {
	state=$(ckNV)
	if [ "$state" = "1" ]; then
		echo "stoping nv..."
		sudo kill $(pgrep python3)
		echo "0"
	fi
}
startMotion() {
	if [ -n "$1" ]; then
		conf = "$1"
	else
		conf="/etc/motion/motion.conf"
	fi
	echo "clearning log file..."
	echo '' > motion.log
	sudo mv motion.log /var/log/motion/motion.log
	sudo chmod a+rwx /var/log/motion/motion.log
	echo "log cleared!"
	echo "Staring Motion starting..."
	sudo motion -c "$conf"*& disown
	echo "1"
}

startNV() {
	python3 "$capture_exec"& disown
	IFS=$'\n' readarray cameras <<< $(sqlite3 "$SQLDB" "select camera_id from cams order by camera_id;")
	for cam in "${cameras[@]}"; do
		python3 "$process_exec" $cam& disown
	done
}
	
stop() {
	killMotion
	mstate=$(ckMotion)
	if [ "$mstate" = 0 ] ;then
		echo 0
	else
		echo -1
	fi
	sleep 2
	killNv
	nvstate=$(ckNV)
	if [ "$nv_state" = 0 ]; then
		echo "0"
	else
		echo -1
	fi
}
if [ -n "$1" ]; then
	func="$1"
else
	func="run"
fi
if [ "$func" = "kill" ]; then
	stop;
elif [ "$func" = "run" ]; then
	motion_state=$(ckMotion)
	if [ "$motion_state" = 0 ]; then
		echo "Starting motion daemon..."
		startMotion;
	elif [ "$motion_state" = 1 ]; then
		echo "Motion alrady running. restarting...."
		result=$(killMotion)
		if [ "$result" = 1 ]; then
			echo "Failed to kill motion (service? sudo?) aborting..."
			exit 1
		else
			echo 0
		fi
		"Starting Motion..."
		startMotion;
	fi
	python3 "$capture_exec"& disown
	IFS=$'\n' readarray cameras <<< $(sqlite3 "$SQLDB" "select camera_id from cams order by camera_id;")
	for cam in "${cameras[@]}"; do
		python3 "$process_exec" "$cam"& disown
	done
fi
