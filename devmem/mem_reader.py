# import mmap
import os
import struct
import threading
import procmaps


norm_funcs = {
    'b': lambda x: x / 127,
    'B': lambda x: x / 256,
    'h': lambda x: x / 32768,
    'H': lambda x: x / 65536,
    'i': lambda x: x / 2147483648,
    'I': lambda x: x / 4294967296,
}

class ProcMaps(threading.Thread):

    def __init__(self, pid=None, format='f'):
        super(ProcMaps, self).__init__()
        if pid is None:
            pid = os.getpid()
        self.f = None
        self.format = format
        success = self.open(pid)
        if not success:
            print('No memory to read')
            exit()

    def open(self, pid):
        try:
            self.maps = procmaps.from_pid(pid)
            self.current_map_i = 0
            self.close()
            self.f = os.open(f"/proc/{pid}/mem", os.O_RDONLY | os.O_SYNC)
        except OSError:
            print(f"Can't find maps for pid {pid}")
            return False
        if len(self.maps) == 0:
            return False
        return True

    def close(self):
        if self.f is not None:
            os.close(self.f)
            self.f = None

    def unpack(self, data, format='b', norm = True):
        size = struct.calcsize(format)
        length = len(data) // size
        res = struct.unpack(f'{length}{format}', data[:length*size])
        if norm and format in norm_funcs:
            fn = norm_funcs[format]
            res = [fn(x) for x in res]
        return res

    def read(self):
        res = [0]
        m = self.maps[self.current_map_i]
        start, end = m.begin_address, m.end_address
        os.lseek(self.f, start, os.SEEK_SET)
        length = end - start
        print(self.current_map_i, length)
        try:
            res = self.unpack(os.read(self.f, length), self.format)
        except OSError:
            print('OSError')
        
        self.current_map_i += 1
        if self.current_map_i >= len(self.maps):
            self.current_map_i = 0
        return res

    def run(self):
        self.running = True
        while self.running:
            res = self.read()
            self.out_buffer.queue_audio(res)

    def stop(self):
        self.running = False

class DevMem(threading.Thread):

    def __init__(self, fname="/dev/random", length=2**33):
        super(DevMem, self).__init__()
        self.fname = fname
        self.f = os.open(fname, os.O_RDONLY | os.O_SYNC)
        # self.mem = mmap.mmap(self.f, length, prot=mmap.PROT_READ)

    def close(self):
        # self.mem.close()
        if self.f is not None:
            os.close(self.f)
            self.f = None

    def change_file(self, fname):
        self.close()
        self.f = os.open(fname, os.O_RDONLY | os.O_SYNC)

    def read(self, length=1):
        try:
            res = os.read(self.f, length)
            return struct.unpack('b', res)
        except:
            print('error')
            return [0] * length

    def run(self):
        self.running = True
        while self.running:
            res = self.read()
            try:
                self.out_buffer.queue_audio(res)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.running = False

