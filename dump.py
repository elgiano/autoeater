import argparse
from autoeater.memdump import ProcMapsDump
from autoeater.osc import OSCThread

parser = argparse.ArgumentParser()
parser.add_argument('pid', type=str, nargs='?', default='self')
parser.add_argument('--format', '-f', type=str, nargs='?', default='f')
parser.add_argument('--osc_port', '-o', type=int, nargs='?', default=None)
args = parser.parse_args()

memdump = ProcMapsDump(args.pid, args.format)

if args.osc_port is not None:
    osc = OSCThread(memdump, port=args.osc_port)
    osc.start()

memdump.run()
