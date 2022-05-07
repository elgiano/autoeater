import pyaudio
import struct
import sys
import os
import threading
from io import BufferedReader, BytesIO
from autoeater.memdump import norm_funcs
from autoeater.player import asciiart
from math import log10

class FilePlayer(threading.Thread):
    def __init__(self, rate=48000, block_size=2048, output_device=None, format='b', out_win=None, err_win=None):
        super(FilePlayer, self).__init__()
        self.format = format
        self.normalize = 10
        self.loop = False

        self.out_win, self.err_win = out_win, err_win
        self.rate, self.block_size = rate, block_size
        self.output_device = output_device
        self.list = []
        self.list_pos = 0
        self.f_name = 'No file'
        self.f_size = 0
        self.f = None

    def print_error(self, msg):
        self.err_win.clear()
        self.err_win.addstr(0,0,msg)
        self.err_win.refresh()
    def print_info(self, msg):
        self.err_win.addstr(0,0,'\n' + msg)
        self.err_win.refresh()

    def print_output(self, msg):
        self.out_win.addstr(msg)
        self.out_win.refresh()

    def __del__(self):
        self.close()

    def open(self, path_or_list):
        if isinstance(path_or_list, list):
            self.open_list(path_or_list)
        else:
            self.open_list([path_or_list])

    def open_list(self, paths):
        self.list = paths
        self.list_pos = 0
        self.open_file(self.list[0])

    def open_next(self):
        self.list_pos += 1
        if self.list_pos >= len(self.list):
            self.list_pos = 0
        return self.open_file(self.list[self.list_pos])

    def open_file(self, path):
        if not os.path.isfile(path):
            return False
        self.close()
        try:
            self.f_size = os.stat(path).st_size
            if self.f_size > 0:
                with open(path, 'rb') as f:
                    bytes = f.read()
                    self.f = BufferedReader(BytesIO(bytes))
            else:
                self.f = open(path, 'rb', self.block_size * 4 * 2)
        except PermissionError:
            self.print_error(f"{path}: permission denied")
            return False
        except FileNotFoundError:
            self.print_error(f"{path}: not found")
            return False
        self.print_info(f"{path}")
        self.f_name = path
        return True

    def close(self):
        if self.f is not None:
            self.f.close()
            self.f = None

    def run(self):
        self.init_audio()

    def stop(self):
        self.audio_stream.close()

    def init_audio(self):
        self.audio_driver = pyaudio.PyAudio()
        if self.output_device:
            (self.output_device, device_rate) = self.find_device(self.output_device)
            if self.output_device:
                self.rate = device_rate
        self.print_info(f"[AudioDriver] starting at {self.rate} Hz (blockSize: {self.block_size})")
        self.audio_stream = self.audio_driver.open(
            output_device_index=self.output_device,
            format=pyaudio.paFloat32,
            channels=2,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.block_size,
            stream_callback=self.audio_callback
        )

    def find_device(self, device_name):
        num_devices = self.audio_driver.get_device_count()
        for i in range(num_devices):
            info = self.audio_driver.get_device_info_by_index(i)
            if info['name'] == device_name:
                self.print_info(f'[AudioDriver] output device = {i}: {device_name}')
                print(info)
                return (i, int(info['defaultSampleRate']))
        self.print_error(f'[AudioDriver] device {device_name} not found. Using default')
        return (None, None)

    def unpack(self, data):
        size = struct.calcsize(self.format)
        length = len(data) // size
        res = struct.unpack(f'{length}{self.format}', data[:length*size])
        if self.normalize  > 0 and self.format in norm_funcs:
            fn = norm_funcs[self.format]
            res = [max(-1, min(1, fn(x, self.normalize))) for x in res]
        return res

    def get_nowplaying(self):
        list_len = len(self.list)
        list_pos = str(self.list_pos).zfill(int(log10(list_len)))
        return f"[{list_pos}/{list_len}] {self.f_name}: {self.f.tell()}/{self.f_size}"

    def audio_callback(self, in_frames, frame_count, time_info, status_flag):
        num_floats = self.block_size * 2
        out_bytes = bytearray(num_floats * 4)
        has_data = False
        if self.f is not None:
            has_data = self.f.readinto(out_bytes)
            self.print_info(self.get_nowplaying())
            if not has_data:
                if self.loop:
                    self.f.seek(0, os.SEEK_SET)
                else:
                    succ = self.open_next()
                    while not succ:
                       succ = self.open_next()

        floats = self.unpack(out_bytes)
        out_bytes = struct.pack(f'{len(floats)}f', *floats)

        self.print_output(asciiart(floats))
        return (out_bytes, pyaudio.paContinue)
