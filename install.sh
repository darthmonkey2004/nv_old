#!/bin/bash
dir="$HOME/Nicole/NicVision"
if [ ! -d "$dir" ]; then
	mkdir "$dir"
fi
cd "$dir"
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps NicVision
sudo mv "$HOME/.local/lib/python3.6/site-packages/nv/main/nv.sh" "/usr/local/bin/nv"
