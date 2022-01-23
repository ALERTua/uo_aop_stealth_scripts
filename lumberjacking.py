import os
import re
from copy import copy

import constants
import tools
from Scripts.script_base import ScriptBase
from py_stealth import *

log = AddToSystemJournal

debug = False
LJ_SLOGS = True

LJ_CONTAINER_ID = 0x728F3B3B
LJ_CONTAINER_COORDS = (2469, 183)
WOOD_ENTRANCE = (2490, 169)
WOOD_ZONE_Y = 188

LJ_SPOTS = [
    (0x0CD0, 2512, 207, 0),
    (0x0CE3, 2516, 210, 0),
    (0x0CE3, 2516, 207, 0),
    (0x0CD0, 2512, 219, 0),
    (0x0CE0, 2512, 228, 0),
    (0x0CCD, 2516, 225, 0),
    (0x0CE0, 2520, 213, 0),
    (0x0CD0, 2520, 210, 0),
    (0x0CD6, 2524, 210, 0),
    (0x0CE3, 2524, 213, 0),
    (0x0CE3, 2520, 228, 0),
    (0x0CCD, 2520, 234, 0),
    (0x0CE0, 2528, 219, 0),
    (0x0CE3, 2528, 228, 0),
    (0x0CD0, 2528, 234, 0),
    (0x0CE6, 2528, 237, 0),
    (0x0CCD, 2528, 240, 0),
    (0x0CD6, 2524, 246, 0),
    (0x0CD0, 2520, 249, 0),
    (0x0CCD, 2520, 246, 0),
    (0x0CD0, 2527, 258, 0),
    (0x0CD6, 2528, 255, 0),
    (0x0CD6, 2528, 252, 0),
    (0x0CCD, 2528, 240, 0),
    (0x0CE6, 2528, 237, 0),
    (0x0CE3, 2528, 228, 0),
    (0x0CE0, 2528, 219, 0),
    (0x0CE3, 2532, 222, 0),
    (0x0CD6, 2532, 225, 0),
    (0x0CE0, 2532, 228, 0),
    (0x0CD0, 2532, 237, 0),
    (0x0CD0, 2532, 243, 0),
    (0x0CE0, 2532, 246, 0),
    (0x0CD6, 2532, 249, 0),
    (0x0CE6, 2532, 252, 0),
    (0x0CE0, 2532, 255, 0),
    (0x0CCD, 2534, 260, 0),
    (0x0CD3, 2537, 257, 0),
    (0x0CCD, 2536, 249, 0),
    (0x0CD6, 2536, 243, 0),
    (0x0CD6, 2536, 225, 0),
]

LJ_ERRORS = [
    'Здесь нет больше дерева для вырубки.',
    'Вы не можете использовать клинок на это.',
    'Вы находитесь слишком далеко!',
]
if not LJ_SLOGS:
    LJ_ERRORS.append('Вы положили несколько бревен в сумку.')


class Lumberjack(ScriptBase):
    def __init__(self):
        super().__init__()
        self._trees = []
        self._current_tree = None

    @property
    def current_tree(self):
        if not self._current_tree:
            if not self._trees:
                self._trees = copy(LJ_SPOTS)
            self._current_tree = self._trees.pop(0)
        return self._current_tree

    @current_tree.setter
    def current_tree(self, value):
        self._current_tree = value

    @property
    def hatchet(self):
        return self.player.backpack_find_type(constants.TYPE_ID_HATCHET)

    @property
    def got_hatchet(self):
        return self.hatchet not in (None, 0, -1)

    def pick_up_items(self):
        type_ids = constants.TYPE_IDS_LJ_LOOT
        return self._pick_up_items(type_ids)

    def move_to_tree(self):
        self.check_overweight()
        self.wait_stamina(5)
        running = self.player.near_max_weight is False and self.player.stamina > 10
        tile_type, x, y, z = self.current_tree
        self.player.move(x, y, accuracy=1, running=running)
        self.pick_up_items()
        self.check_overweight()
        self.general_weight_check()

    def move_to_unload(self):
        log("Moving to unload")
        if self.in_woods:
            self.go_woods()
        self.wait_stamina()
        self.player.move(*LJ_CONTAINER_COORDS)
        UseObject(LJ_CONTAINER_ID)
        log("Moving to unload done")

    def check_hatchet(self):
        # log("Checking Hatchets")
        if self.hatchet:
            return True
        else:
            if self.in_woods:
                return False

            log("Moving to grab a Hatchet")
            self.move_to_unload()
            hatchets = FindType(constants.TYPE_ID_HATCHET, LJ_CONTAINER_ID)
            if not hatchets:
                log("WARNING! NO SPARE HATCHETS FOUND!")
                tools.telegram_message(f"{self.player.name}: No hatchets found")
                self.quit()
                os.system('pause')
                return

            while not self.player.move_item(hatchets):
                log("Grabbing a Hatchet")
                pass

            return True

    def check_bandages(self):
        return self._check_bandages(2, LJ_CONTAINER_ID)

    def eat(self):
        return self._eat(LJ_CONTAINER_ID)

    def unload(self):
        log("Unloading")
        self.move_to_unload()
        self.move_to_unload()
        unload_types = [
            constants.TYPE_ID_LOGS,
            *constants.TYPE_IDS_LOOT,
            *constants.TYPE_IDS_LJ_LOOT
        ]
        self.player.unload_types(unload_types, LJ_CONTAINER_ID)
        self.check_hatchet()
        self.check_hatchet()
        self.check_bandages()
        self.eat()

    def tree_depleeted(self):
        depleeted_tree = copy(self.current_tree)
        self.current_tree = None
        new_tree = self.current_tree
        log(f"{depleeted_tree} Depleeted. New tree: {new_tree}")

    def _jack_tree(self, tile_type, x, y, z):
        CancelWaitTarget()
        self.player.use_object(self.hatchet)
        WaitTargetTile(tile_type, x, y, z)

    @property
    def got_logs(self):
        # noinspection PyProtectedMember
        return self.player._got_item_type(constants.TYPE_ID_LOGS)

    def general_weight_check(self):
        if self.got_logs and self.player.near_max_weight:
            self.unload_and_return()

    @property
    def in_woods(self):
        _, y, _, _ = self.player.coords
        output = y >= WOOD_ZONE_Y
        return output

    def jack_tree(self):
        ClearJournal()
        while self.player.near_max_weight:
            self.general_weight_check()
        self.move_to_tree()
        self._jack_tree(*self.current_tree)

    def drop_overweight_items(self):
        drop_types = [
            (constants.TYPE_ID_LOGS, constants.COLOR_LOGS_S, constants.WEIGHT_LOGS),
            (constants.TYPE_ID_LOGS, -1, constants.WEIGHT_LOGS),
        ]
        return self._drop_overweight_items(drop_types)

    def check_overweight(self):
        if not self.player.near_max_weight:
            return

        self.player.break_action()
        self.drop_overweight_items()

    def go_woods(self):
        self.check_overweight()
        self.wait_stamina()
        log(f"Going to the woods")
        self.player.move(*WOOD_ENTRANCE)
        log(f"Going to the woods done")
        self.wait_stamina(5)

    def lj_check_health(self):
        if not self.check_health():
            self.unload_and_return()

    def lj_check_hatchets(self):
        if not self.check_hatchet():
            self.unload_and_return()

    def unload_and_return(self):
        self.player.break_action()
        self.check_overweight()
        self.unload()
        self.go_woods()
        self.move_to_tree()

    def lumberjack_process(self):
        self.jack_tree()
        i = 0
        while True:
            if tools.in_journal(r'skip \d+ trees', regexp=True):
                trees_quantity = tools.in_journal(r'skip \d+ trees', regexp=True, return_re_value=True)
                trees_quantity = int(re.findall(r'\d+', trees_quantity[0])[0])
                log(f"Skipping {trees_quantity} trees")
                for i in range(trees_quantity):
                    self.tree_depleeted()
                i = 0
                self.jack_tree()
                continue
            elif any(_ for _ in LJ_ERRORS if tools.in_journal(_)):
                self.tree_depleeted()
                i = 0
                self.check_overweight()
                self.lj_check_health()
                self.lj_check_hatchets()
                self.general_weight_check()
                self.jack_tree()
                continue

            self.lj_check_health()
            self.lj_check_hatchets()
            self.general_weight_check()
            i += 1
            if i > 3:
                self.jack_tree()
                i = 0

            Wait(constants.USE_COOLDOWN)

    def start(self):
        self.general_weight_check()
        if not self.in_woods:
            self.go_woods()

        self.lumberjack_process()


if __name__ == '__main__':
    if debug:
        tools.debug()
    Lumberjack().start()
    print("")
