from entities.player import Player
from tools import tools
from py_stealth import *

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
