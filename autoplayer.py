#!/bin/env python
import curses
from time import sleep
from autoeater.file_player import FilePlayer
import argparse


def main(stdscr, win, status, args):
    a = FilePlayer(format=args.format, out_win=win, err_win=status)
    a.open(args.filenames)
    a.start()
    while 1:
        try:
            sleep(0.001)
        except KeyboardInterrupt:
            break

def curses_main(stdscr, path):
    curses.curs_set(0)

    win = stdscr.subwin(curses.LINES - 1, curses.COLS, 0,0)
    status = stdscr.subwin(1, curses.COLS, curses.LINES - 1, 0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    status.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
    win.scrollok(True)
    status.scrollok(True)
    # status.attron(curses.A_REVERSE)
    main(stdscr, win, status, args)
    curses.endwin()



parser = argparse.ArgumentParser()
parser.add_argument('--rate', '-r', type=int, nargs='?', default='48000')
parser.add_argument('--block_size', '-b', type=int, nargs='?', default='2048')
parser.add_argument('--format', '-f', type=str, nargs='?', default='b')
parser.add_argument('filenames', type=str, nargs='+')
args = parser.parse_args()

curses.wrapper(curses_main, args)
