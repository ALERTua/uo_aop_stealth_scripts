from entities.player import Player
from tools import tools, constants
import py_stealth as stealth
from tools.tools import log

player = Player()


def main():
    weapons = player.find_types_backpack(constants.TYPE_IDS_WEAPONS)
    for i, weapon in enumerate(weapons):
        log.info(f"{i}/{len(weapons)}")
        if weapon.magic:
            player.move_item(weapon, target_id=0x727BE0AB)


if __name__ == '__main__':
    main()
