import sys
import os
import constants
from mining import Miner
from lumberjacking import Lumberjack
from lastobject_lasttarget import LastObjectLastTarget
from py_stealth import *
from player import Player
import tools

log = AddToSystemJournal

debug = True
if debug:
    tools.debug()

player = Player()


def main():
    log('Start')
    log('Done.')


if __name__ == '__main__':
    main()
