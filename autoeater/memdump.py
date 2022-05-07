import procmaps
from time import sleep
import struct
import sys
import os

norm_funcs = {
    'b': lambda x, n: x / 0x7f * n,
    'B': lambda x, n: x / 0xff * n,
    'h': lambda x, n: x / 0x7fff * n,
    'H': lambda x, n: x / 0xffff * n,
    'i': lambda x, n: x / 0x7fffffff * n,
    'I': lambda x, n: x / 0xffffffff * n,
    'f': lambda x, n: max(-n, min(n, x))
}

MAX_INT64 = 2**31 - 1

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class ProcMapsDump():

    def __init__(self, pid='self', format='b', loop=False, normalize=1):
        self.f = None
        if not self.open(pid):
            eprint('No memory to read')

        self.loop, self.format, self.normalize = loop, format, normalize
        self.stdout_block_size = 2048 * 4 * 2
        self.skip_request = None
        self.skip_files = False
        self.stdout  = os.fdopen(sys.stdout.fileno(), 'w', self.stdout_block_size)

    def __del__(self):
        self.close()
    
    def read_maps(self, pid='self'):
        if pid == 'self':
            pid = os.getpid()
        elif isinstance(pid, str):
            pid = int(pid)
        eprint('Opening maps for pid', pid)
        maps = None
        try:
            maps = procmaps.from_pid(pid)[:-1]
        except OSError as err:
            eprint(f'Error reading maps for pid {pid}: {err}')
            return False
        if len(maps) == 0:
            eprint(f'Empty memory maps for pid {pid}.')
            return False
        return maps

    def get_maps_len(self, pid):
        maps = self.read_maps(pid)
        if maps == False: return 0
        return len(maps)

    def open(self, pid='self'):
        self.maps = self.read_maps(pid)
        if self.maps == False: return False
        self.current_map_i = 0
        self.close()

        if pid == 'self':
            pid = os.getpid()
        elif isinstance(pid, str):
            pid = int(pid)

        try:
            self.f = os.open(f"/proc/{pid}/mem", os.O_RDONLY | os.O_SYNC)
        except PermissionError:
            eprint(f"/proc/{pid}/mem: permission denied")
            exit()
        except FileNotFoundError:
            eprint(f"/proc/{pid}/mem: file not found")
            return False
        return True

    def close(self):
        if self.f is not None:
            os.close(self.f)
            self.f = None

    def inc_curr_block(self, increment = 1):
        self.current_map_i += increment
        if self.current_map_i >= len(self.maps):
            self.current_map_i = 0

    def seek(self, pos):
        try:
            os.lseek(self.f, pos, os.SEEK_SET)
        except OverflowError:
            rest = pos - MAX_INT64
            eprint('seek_set', MAX_INT64)
            os.lseek(self.f, MAX_INT64, os.SEEK_SET)
            while rest > 0:
                increment = rest
                if increment > MAX_INT64:
                    increment = MAX_INT64
                rest -= increment
                eprint('seek_cur', rest, increment)
                os.lseek(self.f, increment, os.SEEK_CUR)

    def skip_maps_with_pathname(self):
        while self.maps[self.current_map_i].pathname:
            self.inc_curr_block()

    def read(self):
        res = [0]
        if self.skip_files:
            self.skip_maps_with_pathname()
        m = self.maps[self.current_map_i]
        start, end = m.begin_address, m.end_address
        length = end - start
        eprint('block', self.current_map_i, len(self.maps), start, length)
        self.seek(start)
        while length > 0:
            readlen = min(self.stdout_block_size, length)
            length -= readlen
            try:
                res = os.read(self.f, readlen)
                self.stdout.buffer.write(self.repack(res))
                if self.skip_request is not None:
                    self.perform_skip()
                    return
            except OSError as err:
                eprint('OSError', err)

        if not self.loop:
            self.inc_curr_block()
        return res

    def request_skip(self, pid, map_n=0):
        self.skip_request = [pid, map_n]

    def perform_skip(self):
        pid, map_n = self.skip_request
        self.skip_request = None
        if pid is not None:
            success = self.open(pid)
            if not success:
                return
        if map_n is None:
            map_n = 0
        self.current_map_i = map_n % len(self.maps)
        eprint('skipped', self.current_map_i)

    def run(self):
        self.running = True
        while self.running:
            if self.f is not None:
                self.read()
            else:
                sleep(1)

    def repack(self, data):
        size = struct.calcsize(self.format)
        length = len(data) // size
        res = struct.unpack(f'{length}{self.format}', data[:length*size])
        if self.normalize  > 0 and self.format in norm_funcs:
            fn = norm_funcs[self.format]
            res = [max(-1, min(1, fn(x, self.normalize))) for x in res]
        return struct.pack(f'{len(res)}f', *res)

    def stop(self):
        self.running = False
