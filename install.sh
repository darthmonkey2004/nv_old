#!/bin/bash
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
hasnv=$(which nv)
if [ -z "$hasnv" ]; then
	echo "Copying executable to /usr/local/bin..."
	sudo mv "$dir/nv/nv.run" "/usr/local/bin/nv"
fi
echo "Auto detecting cameras..."
. "$dir/nv/scancams.sh"
echo "Configuring motion..."
. "$dir/nv/mkconf.sh"
sudo touch /var/log/motion/motion.log
sudo chown motion /var/log/motion/motion.log
sudo chmod a+rwx /var/log/motion/motion.log
sudo motion -c /etc/motion/motion.conf
python3 "$dir/nv/mkhtml.py"
echo "Done! To start: run 'nv'. To end: run 'nv kill'."
exit 0
