import re
from copy import copy
import pendulum

from tools import constants, tools
from entities.base_script import ScriptBase
from py_stealth import *

log = AddToSystemJournal

debug = False
MINE_IRON = True

MINE_ENTRANCE_COORDS = (2427, 177)
MINING_CONTAINER_ID = 0x728BAB4E
MINING_CONTAINER_COORDS = (2462, 183)
MINE_FORGE_COORDS = (2413, 184)
MINING_SPOTS = [
    (2410, 184),
    (2410, 181),
    (2412, 178),
    (2414, 176),
    (2415, 173),
    (2416, 171),
    (2417, 169),
    (2420, 169),
    (2422, 170),
    (2424, 170),
    (2424, 173),
    (2421, 173),
    (2418, 173),
    (2417, 175),
    (2420, 175),
    (2423, 175),
    (2426, 175),
    (2426, 178),
    (2423, 178),
    (2419, 178),
    (2416, 178),
    (2413, 181),
    (2416, 181),
    (2419, 181),
    (2422, 180),
    (2425, 180),
    (2415, 183),
    (2412, 185),
]
DIRECTIONS = [
    'CENTER',
    'N',
    'NE',
    'E',
    'SE',
    'S',
    'SW',
    'W',
    'NW',
]
MINING_ERRORS = [
    'Здесь нет больше руды..',
    'Вы не можете копать в этом месте.',
    'Вы находитесь слишком далеко!',
]
if not MINE_IRON:
    MINING_ERRORS.append('Вы выкопали немного руды.')


class Miner(ScriptBase):
    def __init__(self):
        super().__init__()
        self._mining_spots = []
        self._directions = []
        self._mining_spot = None
        self._direction = None

    def move_to_unload(self):
        log("Moving to unload")
        if self.in_mine:
            self.go_to_mine_entrance()
        self.wait_stamina()
        self.player.move(*MINING_CONTAINER_COORDS)
        UseObject(MINING_CONTAINER_ID)
        UseObject(MINING_CONTAINER_ID)
        log("Moving to unload done")

    def eat(self):
        return self._eat(MINING_CONTAINER_ID)

    @property
    def pickaxe(self):
        return self.player.find_type_backpack(constants.TYPE_ID_TOOL_PICKAXE)

    def check_pickaxes(self):
        if self.pickaxe:
            return True
        else:
            log("Moving to grab a Pickaxe")
            if self.in_mine:
                return False

            self.move_to_unload()
            pickaxes = FindType(constants.TYPE_ID_TOOL_PICKAXE, MINING_CONTAINER_ID)
            if not pickaxes:
                log("WARNING! NO SPARE PICKAXES FOUND!")
                self.quit()
                return

            log("Grabbing a Pickaxe")
            self.player.move_item(pickaxes)
            return True

    def check_bandages(self):
        return self._check_bandages(2, MINING_CONTAINER_ID)

    def unload(self):
        log("Unloading")
        self.move_to_unload()
        unload_types = [
            constants.TYPE_ID_ORE,
            constants.TYPE_ID_INGOT,
            *constants.TYPE_IDS_LOOT,
            *constants.TYPE_IDS_MINING_LOOT
        ]
        self.player.unload_types(unload_types, MINING_CONTAINER_ID)
        self.check_pickaxes()
        self.check_bandages()
        self.eat()

    def go_to_mine_entrance(self):
        self.check_overweight()
        self.wait_stamina()
        log(f"Going to the mine")
        self.player.move(*MINE_ENTRANCE_COORDS)
        log(f"Going to the mine done")
        self.wait_stamina(5)

    @property
    def mining_spots(self):
        if not self._mining_spots:
            log(f"Mining spots depleeted. Refreshing.")
            self._mining_spots = copy(MINING_SPOTS)
        return self._mining_spots

    def mining_spot_depleeted(self):
        old_mining_spot = copy(self._mining_spot)
        self._mining_spot = self.mining_spots.pop(0)
        log(f"Mining spot {old_mining_spot} depleeted. New mining spot: {self._mining_spot}")

    @property
    def mining_spot(self):
        # if not self._mining_spot:
        #     self.mining_spot_depleeted()
        return self._mining_spot

    @property
    def directions(self):
        if not self._directions:
            self._directions = copy(DIRECTIONS)
            self.mining_spot_depleeted()
        return self._directions

    @property
    def direction(self):
        if not self._direction:
            self.direction_depleeted()
        return self._direction

    def direction_depleeted(self):
        old_direction = copy(self._direction)
        self._direction = self.directions.pop(0)
        log(f"Direction {self._mining_spot} {old_direction} depleeted. New direction: {self._direction}")
        ClearJournal()

    @property
    def in_mine(self):
        x, _, _, _ = self.player.coords
        mine_entrance_x, _ = MINE_ENTRANCE_COORDS
        return x <= mine_entrance_x

    def pick_up_items(self):
        type_ids = constants.TYPE_IDS_MINING_LOOT
        return self._pick_up_items(type_ids)

    def mine_check_pickaxes(self):
        if self.check_pickaxes():
            pass
        else:
            self.player.break_action()
            self.check_overweight()
            self.unload()
            self.check_pickaxes()
            self.go_to_mine_entrance()
            self.move_mining_spot()

    def mine_check_health(self):
        if self.check_health():
            pass
        else:
            self.player.break_action()
            self.check_overweight()
            self.unload()
            self.check_health()
            self.go_to_mine_entrance()

    def move_mining_spot(self):
        self.check_overweight()
        self.wait_stamina(5)
        running = self.player.near_max_weight is False and self.player.stamina > 10
        _ = self.direction
        self.player.move(*self.mining_spot, running=running)
        self.pick_up_items()
        self.check_overweight()
        self.general_weight_check()

    def mine_direction(self):
        ClearJournal()
        while self.player.near_max_weight:
            self.general_weight_check()
        while self.in_mine and self.player.near_max_weight and self.move_mining_spot() is None and self.got_ore:
            self.smelt()
            self.move_mining_spot()

        # self.check_overweight()
        # while self.player.overweight:
        #     self.check_overweight()
        # while self.in_mine and self.player.near_max_weight and self.got_ore:
        #     self.smelt()
        #     self.move_mining_spot()
        # if self.in_mine and self.player.near_max_weight and not self.got_ore:
        #     log(f"Mining direction halted. Need to unload.")
        #     self.unload()
        #     self.go_to_mine_entrance()
        self.move_mining_spot()
        self.player.mine(self.direction)

    def do_mining(self):
        self.mine_direction()
        i = 0
        while True:
            if tools.in_journal(r'skip \d+ spots', regexp=True):
                spots_quantity = tools.in_journal(r'skip \d+ spots', regexp=True, return_re_value=True)
                spots_quantity = int(re.findall(r'\d+', spots_quantity[0])[0])
                log(f"Skipping {spots_quantity} spots")
                for i in range(spots_quantity):
                    self.mining_spot_depleeted()
                self._directions = []
                i = 0
                self.mine_direction()
                continue
            elif tools.in_journal('skip spot'):
                log(f"Skipping spot")
                self._directions = []
                i = 0
                self.mine_direction()
                continue
            elif any(_ for _ in MINING_ERRORS if tools.in_journal(_)):
                self.direction_depleeted()
                i = 0
                self.check_overweight()
                self.mine_check_health()
                self.mine_check_pickaxes()
                self.general_weight_check()
                self.mine_direction()
                continue

            self.mine_check_health()
            self.mine_check_pickaxes()
            self.general_weight_check()
            i += 1
            if i > 10:
                self.mine_direction()
                i = 0

            Wait(constants.USE_COOLDOWN)

    @property
    def nearest_forge(self):
        return self.player.find_type_ground(constants.TYPE_ID_FORGE, 20)

    def smelt(self):
        forge = self.nearest_forge
        if not forge:
            return

        self.check_overweight()
        if not self.got_ore:
            return

        log(f"Smelting Ore")
        self.wait_stamina()
        self.player.move(*MINE_FORGE_COORDS, accuracy=1)
        self.player.smelt_ore(forge)

    @property
    def got_ore(self):
        # noinspection PyProtectedMember
        return self.player.got_item_type(constants.TYPE_ID_ORE)

    def drop_overweight_items(self):
        drop_types = [
            (constants.TYPE_ID_ORE, constants.COLOR_ORE_IRON, constants.WEIGHT_ORE),
            (constants.TYPE_ID_INGOT, constants.COLOR_INGOT_IRON, constants.WEIGHT_INGOT),
            (constants.TYPE_ID_ORE, -1, constants.WEIGHT_ORE),
            (constants.TYPE_ID_INGOT, -1, constants.WEIGHT_INGOT)
        ]
        return self._drop_overweight_items(drop_types)

    def check_overweight(self):
        if not self.player.near_max_weight:
            return

        self.player.break_action()
        self.drop_overweight_items()

    def unload_and_return(self):
        self.unload()
        if not self.in_mine:
            self.go_to_mine_entrance()

    def general_weight_check(self):
        if self.got_ore and self.player.near_max_weight:
            if self.in_mine:
                self.smelt()
                if self.player.near_max_weight:
                    self.unload()
            else:
                self.unload()

    def start(self):
        self._start_time = pendulum.now()
        self.general_weight_check()
        if not self.in_mine:
            self.go_to_mine_entrance()

        self.do_mining()


if __name__ == '__main__':
    if debug:
        tools.debug()
    Miner().start()
    print("")
