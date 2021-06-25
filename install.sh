#!/bin/bash
dir="$HOME/Nicole/NicVision"
if [ ! -d "$dir" ]; then
	mkdir "$dir"
fi
cd "$HOME/.local/lib/python3.6/site-packages"
git clone "https://github.com/darthmonkey2004/nv.git"
sudo mv "$HOME/.local/lib/python3.6/site-packages/nv/nv.run" "/usr/local/bin/nv"
sudo apt-get install -y curl nmap
./scan.networkCameras.sh
./motion_conf.sh
python3 mkhtml.py
echo "Done! To start: run 'nv'. To end: run 'nv kill'."
exit 0
