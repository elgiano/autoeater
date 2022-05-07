import pyaudio
import struct
import sys
import os

def asciiart(values):
    grayscale = " .`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$" #67 levels of gray
    asciiart = ""
    for v in values:
        asciiart += grayscale[int(min(66, max(0, v * 66)))]
    return asciiart

def colorize(text, r, g, b, background = False):
    RESET = '\033[0m'
    return '\033[{};2;{};{};{}m'.format(48 if background else 38, r, g, b) + text + RESET

def asciiart_color(values):
    grayscale = " .`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$" #67 levels of gray
    asciiart = ""
    colors = [[int(v * 256) for v in i] for i in zip(*[iter(values)]*3)]
    for (v, c) in zip(values, colors):
        asciiart += colorize(grayscale[int(min(66, max(0, v * 66)))], *c)
    return asciiart

class StdinPlayer():
    def __init__(self, rate=48000, block_size=2048, output_device=None):
        self.output_device = output_device
        self.rate, self.block_size = rate, block_size
        self.stdin  = os.fdopen(sys.stdin.fileno(), 'r', block_size * 4 * 2)
    def start(self):
        self.init_audio()

    def stop(self):
        self.audio_stream.close()

    def init_audio(self):
        self.audio_driver = pyaudio.PyAudio()
        if self.output_device:
            (self.output_device, device_rate) = self.find_device(self.output_device)
            if self.output_device:
                self.rate = device_rate
        print(f"[AudioDriver] starting at {self.rate} Hz (blockSize: {self.block_size})")
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
                print(f'[AudioDriver] output device = {i}: {device_name}')
                print(info)
                return (i, int(info['defaultSampleRate']))
        print(f'[AudioDriver] device {device_name} not found. Using default')
        return (None, None)

    def audio_callback(self, in_frames, frame_count, time_info, status_flag):
        num_floats = self.block_size * 2
        out_bytes = bytearray(num_floats * 4)
        self.stdin.buffer.readinto(out_bytes)
        out_bytes = bytes(out_bytes)

        floats = struct.unpack(f'{num_floats}f', out_bytes)
        print(asciiart(floats))
        return (out_bytes, pyaudio.paContinue)
