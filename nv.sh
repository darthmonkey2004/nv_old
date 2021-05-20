#!/bin/bash

stop() {
	sudo kill $(pgrep python3)
	exit
}
if [ -n "$1" ]; then
	func="$1"
else
	func="run"
fi
if [ "$func" = "kill" ]; then
	stop;
elif [ "$func" = "run" ]; then
	exec_dir="$HOME/.local/lib/python3.6/site-packages/nv/main/"
	process_exec="$exec_dir/process_test.py"
	capture_exec="$exec_dir/capture.py"
	pypid=$(pgrep python3)
	if [ -z "$pypid" ]; then
		echo "Capture not running. Starting..."
		python3 "$capture_exec"& disown
	fi
	cameras=(1 2 3)
	for cam in "${cameras[@]}"; do
		python3 "$process_exec" $cam& disown
	done
fi
