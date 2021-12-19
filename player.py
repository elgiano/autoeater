from time import sleep
import argparse
from autoeater.player import StdinPlayer

parser = argparse.ArgumentParser()
parser.add_argument('rate', type=int, nargs='?', default='48000')
parser.add_argument('block_size', type=int, nargs='?', default='2048')
args = parser.parse_args()

player = StdinPlayer(args.rate, args.block_size)

try:
    player.start()
    while True:
        sleep(1)
except KeyboardInterrupt:
    player.stop()
    print('')
finally:
    print('Exit.')
