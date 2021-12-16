from devmem.audio import AudioOutput
from devmem.mem_reader import ProcMaps
from time import sleep
import argparse
from sys import exit

parser = argparse.ArgumentParser()
parser.add_argument('pid', type=int, nargs='?', default=None)
parser.add_argument('--format', '-f', type=str, nargs='?', default='f')
args = parser.parse_args()

m = ProcMaps(args.pid, args.format)
a = AudioOutput()

m.out_buffer = a.buffer
m.start()

try:
    a.start()
    while True:
        sleep(1)
except KeyboardInterrupt:
    a.stop()
    m.stop()
    print('')
finally:
    print('Exit.')

m.close()


'''
m = DevMem(length=10**7)
b = bytearray(2**31)
i = 0
for n in range(0, 2**33, 4096):
    x = os.read(m.f, 4096)
    b[i] = sum(struct.unpack('4096B', x)) >> 12
    i += 1

print('done')

os.lseek(m.f, int(2**33.15), os.SEEK_SET)
x = os.read(m.f, 0);
print(x)

m.close()

import pygame as pg
import numpy as np
def draw_mem(window):
    size = window.get_size();
    pixel_array = pg.PixelArray(window)
    for x in range(size[0]):
        for y in range(size[1]):
            pixel_array[x, y] = ( int(np.random.rand() *256), 0, 0) 
    pixel_array.close()


pg.init()
pg.display.set_caption("devmem")
window = pg.display.set_mode((600, 600), pg.RESIZABLE)
running  = True
while running:

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    draw_mem(window)
    pg.display.update()
'''
