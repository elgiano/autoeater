import pyaudio
import numpy as np
from queue import Queue, Empty, Full

class AudioOutputBuffer():
    def __init__(self, block_size, max_blocks):
        self.block_size, max_blocks = block_size, max_blocks
        self.buffer = np.zeros(block_size)
        self.buffer_pos = 0
        self.frames = Queue(max_blocks)
        self.incomplete_block = None
        self.last_was_empty = False
    
    def queue_audio(self, audio, clear = False):
        blocks = np.split(audio, np.arange(
            self.block_size, len(audio), self.block_size))

        if self.incomplete_block is not None:
            self.incomplete_block = np.concatenate((self.incomplete_block, blocks[0]))
            i_len = len(self.incomplete_block)
            if i_len == self.block_size:
                self.frames.put(self.incomplete_block[:self.block_size])    
                self.incomplete_block = None
            elif i_len > self.block_size:
                self.frames.put(self.incomplete_block[:self.block_size])
                self.incomplete_block = self.incomplete_block[self.block_size:]
            blocks = blocks[1:]

        if len(audio) % self.block_size != 0 and len(blocks) > 0:
            remainder = blocks[-1]
            self.incomplete_block = remainder
            blocks = blocks[:-1]

        if clear:
            with self.frames.mutex:
                del self.frames
                self.frames = Queue()
        try:
            for b in blocks:
                self.frames.put(b)
        except KeyboardInterrupt:
            return

    def get_audio_block(self):
        try:
            ret = self.frames.get_nowait()
            self.last_was_empty = False
            return ret
        except Empty:
            if not self.last_was_empty:
                print("Warning: out buffer is empty")
            self.last_was_empty = True
            return np.zeros(self.block_size)

class CircularBuffer():
    def __init__(self, data):
        self.data = data
        self.len = len(data)
        self.buffer_pos = 0
    
    def get_block(self, block_size):
        if self.pos + block_size < self.len:
            self.pos += block_size
            return self.data[self.pos-block_size:self.pos]

class AudioOutput():
    def __init__(self, rate=48000, block_size=2048, output_device=None):
        self.output_device = output_device
        self.rate, self.block_size = rate, block_size
        self.buffer = AudioOutputBuffer(self.block_size, 8)

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
        out_frames = self.buffer.get_audio_block()
        return (out_frames, pyaudio.paContinue)

