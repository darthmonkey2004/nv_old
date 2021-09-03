#!/bin/bash

detector_mkxml() {
	if [ -n "$1" ]; then
		traindir="$1"
	else
		read -p "Enter training dir: " traindir
	fi
	dirname=$(basename "$traindir")
	xmlpath="$traindir/$dirname.xml"
	imglab -c "$xmlpath"
	mv "$xmlpath" "$HOME/Nicole/NicVision/$dirname.xml"
	echo "xml saved to $HOME/Nicole/NicVision/$dirname.xml!"
}

sudo apt-get install -y curl nmap git python3-pip python3 motion unzip
dir="$HOME/Nicole/NicVision"
if [ ! -d "$dir" ]; then
	echo "Creating data directory..."
	mkdir "$dir"
	mkdir "$dir/training_data"
	cd "$dir/training_data"
	wget "http://stnet.simiantech.biz/nv.dataset.zip"
	unzip nv.dataset.zip -d .
fi
echo "Installing packages..."
dir="$HOME/.local/lib/python3.6/site-packages"
cd "$dir"
if [ ! -d "$dir" ]; then
	echo "Cloning nv repo..."
	git clone "https://github.com/darthmonkey2004/nv.git"
fi
cd nv
echo "Installing python requirements..."
pip3 install -r nv.requirements.txt
echo "Getting dlib (for imglab)..."
cd ~/
git clone "https://github.com/davisking/dlib.git"
cd dlib/tools/imglab
mkdir build
cd build
cmake ..
cmake --build . --config Release
sudo make install
echo "imglab installed!"
cd "$dir/nv"
hasnv=$(which nv)
if [ -z "$hasnv" ]; then
	echo "Copying nv executable to /usr/local/bin..."
	sudo mv "$dir/nv/nv.run" "/usr/local/bin/nv"
	sudo chmod a+x /usr/local/bin/nv
fi
hascap=$(which cap)
if [ -z "$hascap" ]; then
	echo "Copying capture metod to /usr/local/bin..."
	sudo mv "$dir/nv/cap" "/usr/local/bin/cap"
	sudo chmod a+x /usr/local/bin/cap
echo "Auto detecting cameras..."
. "$dir/nv/scancams.sh"
echo "Configuring motion..."
. "$dir/nv/mkconf.sh"
sudo touch /var/log/motion/motion.log
sudo chown motion /var/log/motion/motion.log
sudo chmod a+rwx /var/log/motion/motion.log
sudo motion -c /etc/motion/motion.conf
echo "Creating html pages..."
python3 "$dir/nv/mkhtml.py"
read -p "Would you like to create a detector from a dataset? (y/n) :" yn
if [ "$yn" = "y" ]; then
	read -p "Enter path to dataset: " path
	detector_mkxml "$path"
else
	echo "ok. Skipping..."
fi
echo "Done! To start: run 'nv'. To end: run 'nv kill'."
exit 0
