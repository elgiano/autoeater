from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_server import OSCUDPServer
from pythonosc.osc_message import OscMessage
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_bundle import OscBundle
from typing import Union, Tuple
import socket
import threading
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class OSCServerClient(OSCUDPServer):

    def __init__(self, server_address: Tuple[str, int], dispatcher: Dispatcher, allow_broadcast=True) -> None:
        super().__init__(server_address, dispatcher)
        if allow_broadcast:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def send(self, recv_addr, content: Union[OscMessage, OscBundle]) -> None:
        self.socket.sendto(content.dgram, recv_addr)

    def send_message(self, recv_addr, address: str, value: Union[int, float, bytes, str, bool, tuple, list]) -> None:
        builder = OscMessageBuilder(address=address)
        if value is None:
            values = []
        elif not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            values = [value]
        else:
            values = value
        for val in values:
            builder.add_arg(val)
        msg = builder.build()
        self.send(recv_addr, msg)


class OSCThread(threading.Thread):
    def __init__(self, mem_reader, host='localhost', port=57130):
        super(OSCThread, self).__init__()
        self.mem_reader = mem_reader
        dispatcher = Dispatcher()
        dispatcher.map('/skip', self.respond_to_skip,
                       needs_reply_address=True)
        dispatcher.map('/loop', self.respond_to_loop,
                       needs_reply_address=True)
        dispatcher.map('/format', self.respond_to_format,
                       needs_reply_address=True)
        dispatcher.map('/norm', self.respond_to_norm,
                       needs_reply_address=True)
        eprint(f"[OSC] starting server at {host}:{port}")
        self.osc_server = OSCServerClient((host, port), dispatcher)

    def run(self):
        self.osc_server.serve_forever()

    def stop(self):
        self.osc_server.shutdown()

    def respond_to_loop(self, client_addr, cmd, *args):
        looping  = args[0] > 0
        self.mem_reader.loop = looping

    def respond_to_norm(self, client_addr, cmd, *args):
        self.mem_reader.normalize = args[0]

    def respond_to_format(self, client_addr, cmd, *args):
        format  = args[0]
        valid_formats = ['b','B','h','H','i','I','f']
        if format in valid_formats:
            self.mem_reader.format = format

    def respond_to_skip(self, client_addr, cmd, *args):
        pid, block_n = args
        if pid == 0 or pid == '0':
            pid = None
        self.mem_reader.request_skip(pid, block_n)
        # self.osc_server.send_message(client_addr, cmd, self.loaded_model_names)
