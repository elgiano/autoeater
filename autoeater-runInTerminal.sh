#!/bin/bash
cd /home/giano/dev/autoeater;
. .venv/bin/activate;
sudo python dump.py -f b -o 57130 | python player.py
