#!/bin/bash

installtobin() {
	hasgit=$(which git)
	if [ -z "$hasgit" ]; then
		sudo apt-get install -y git
	fi
	if [ -f "$USER/Nicole/nv/v4l2sink.py" ]; then
		git clone "https://github.com/darthmonkey2004/NicVision.git"
		cd NicVision
	else
		cd "$USER/Nicole/nv"
	fi
	sudo cp v4l2sink.py /usr/local/bin/v4l2sink
	sudo chmod a+rwx /usr/local/bin/v4l2sink.py
	echo "Setting up dependencies."
	echo "Installing v4l2 for python3..."
	pip3 install "opencv-python opencv-contrib-python v4l2"
	sudo pip3 install "opencv-python opencv-contrib-python v4l2"
	echo "Patching v4l2 python bug..."
	hasbzr=$(which bzr)
	if [ -z "$hasbzr" ]; then
		sudo apt-get install -y bzr
	fi
	bzr branch "lp:~jgottula/python-v4l2/fix-for-bug-1664158"
	cd "fix-for-bug-1664158"
	cp v4l2.py "$HOME/.local/lib/python3.6/site-packages/v4l2.py"
	sudo pip3 install "opencv-python opencv-contrib-python v4l2"
	sudo cp v4l2.py "/usr/local/lib/python3.6/dist-packages/v4l2.py"
	echo "python-v4l2 library installed in both local and system user space."
}
mkloopbackdev() {
	echo "Creating device..."
	devs=$(ls /dev/video*)
	ary=($devs)
	ct = "${#devs[@]}"
	ct = $(( devs + 1 ))
	dev="/device/video$ct"
	read -p "Press to create device..." any_key
	sudo modprobe v4l2loopback video_nr=$ct and card_label="Zosi DVR loopback sync"
	echo "$dev"
}
if [ -z "$1" ]; then
	read -p "Enter source string: " src
else
	src="$1"
fi
if [ -z "$2" ]; then
	read -p "Enter device id (number) of v4l2loopback device: " dev
else
	dev="$2"
fi

devexists=$(ls /dev/video$dev)
if [ -z "$devexists" ]; then
	echo "Device $dev not found. Creating..."
	read -p "Press a key..." any_key
	dev=$(mkloopbackdev)
	echo "Device: $dev created."
else
	dev="/dev/video$dev"
	echo "Using loopback device: $dev"
fi
isinpath=$(which v4l2sink)
if [ -z "$isinpath" ]; then
	installtobin;
fi
runpath="$HOME/Nicole/nv/run.sh"
if [ -f "$runpath" ]; then
	rm "$runpath"
fi
echo '#!/bin/bash' > "$runpath"
echo '' >> "$runpath"
echo "v4l2sink -s $src -d $dev" >> "$runpath"
echo "exit" >> "$runpath"
sudo chmod a+rwx "$runpath"
gnome-terminal --working-directory="$HOME/Nicole/nv" -- bash $runpath
sleep 2
width=$(v4l2-ctl -d /dev/video$dev --all | grep "Width/Height" | cut -d ':' -f 2 | cut -d ' ' -f 2 | cut -d '/' -f 1)
height=$(v4l2-ctl -d /dev/video$dev --all | grep "Width/Height" | cut -d ':' -f 2 | cut -d ' ' -f 2 | cut -d '/' -f 2)
#vlc v4l2://$dev:width=$width:height=$height:v4l2-standard=NTSC:input-slave=alsa://hw:2,0
vlc v4l2://$dev:width=$width:height=$height:v4l2-standard
