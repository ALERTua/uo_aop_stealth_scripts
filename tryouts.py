import sys
import os
import constants
from Scripts.mining import Miner
from Scripts.lumberjacking import Lumberjack
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
    lj = Lumberjack(player)
    hatchet = player.backpack_find_type(constants.TYPE_ID_HATCHET)
    player.use_object(hatchet)
    WaitTargetTile(0x0CD0, 2520, 249, 0)
    # WaitForTarget(1000)
    # TargetToTile(0x0CD0, 2520, 249, 0)
    log('Done.')


if __name__ == '__main__':
    main()
