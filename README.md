# autoeater
jonatura!!?!?!???!??!

## What?
There are two programs:
1. `dump.py` reads memory maps and dumps mem to stdout
2. `player.py` reads stdin and plays sound and asciiart

`dump.py` also has an OSC interface.

## Requirements
- pyaudio
- procmaps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
```
usage: dump.py [-h] [--format [FORMAT]] [--osc_port [OSC_PORT]] [pid]

usage: player.py [-h] [rate] [block_size]
```

Use `dump` to read blocks into `player`
```
python dump.py | python player.py
```

Read blocks as superuser, play as your user:
```
sudo python dump.py | python player.py
```

Play something else:
```
cat /dev/urandom | python player.py
```

## OSC
Use `-o osc_port` to start an OSC server
`python dump.py -o 57130`
Messages:
- `/skip pid block_n`: pid can be an int or 'self' to open a new mem file, block_n will skip to the nth block. pid == 0 will be ignored (can be used to skip memblocks in current memfile).
- `/format f`: f can be one of these strings `['b','B','h','H','i','I','f']`. Specifies bytes format for conversion to float.
- `/loop looping`. looping can be 0 or 1, to disable or enable looping the current block.
- `/norm factor`. factor is a float. If 0, normalization is disabled, otherwise: integer formats get multiplied by factor and divided by their max absolute value (e.g. 255 for unsigned bytes, 0x7fff for signed shorts); float format gets clipped between -factor and factor
