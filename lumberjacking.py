import re
from copy import copy

import pendulum

from entities.base_script import ScriptBase, alive_action
from entities.container import Container
from entities.item import Item
from entities.mob import Mob
from py_stealth import *
from tools import constants, tools

log = AddToSystemJournal

debug = True
LJ_SLOGS = True
ENGAGE_RANGED_MOBS = True
ENGAGE_MELEE_MOBS = True
ENGAGE_CRITTERS = True
LOOT_CORPSES = True
CUT_CORPSES = True
HOLD_BANDAGES = 2
EQUIP_WEAPONS_FROM_GROUND = True
EQUIP_WEAPONS_FROM_LOOT_CONTAINER = True
MAX_WEAPON_SEARCH_DISTANCE = 20
LJ_CONTAINER_ID = 0x728F3B3B
LJ_CONTAINER_COORDS = (2470, 182)
WOOD_ENTRANCE = (2503, 167)
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
                self.report_stats()
            self._current_tree = self._trees.pop(0)
            log(f"New Tree: {self._current_tree}. Trees left: {len(self._trees)}/{len(LJ_SPOTS)}")
        return self._current_tree

    @current_tree.setter
    def current_tree(self, value):
        self._current_tree = value

    @property
    def hatchet(self):
        return self.player.find_type_backpack(constants.TYPE_ID_HATCHET)

    @property
    def got_hatchet(self):
        return self.hatchet not in (None, 0, -1)

    def pick_up_items(self):
        type_ids = constants.TYPE_IDS_LJ_LOOT
        return self._pick_up_items(type_ids)

    def move_to_tree(self):
        self.parse_commands()
        self.check_overweight()
        self.wait_stamina(5)
        tile_type, x, y, z = self.current_tree
        self.player.move(x, y, accuracy=1, running=self.should_run)
        self.pick_up_items()
        self.loot_corpses()
        self.check_overweight()
        self.general_weight_check()

    def move_to_unload(self):
        self.parse_commands()
        dist_to_container = Dist(self.player.x, self.player.y, *LJ_CONTAINER_COORDS)
        if dist_to_container > 1:
            log("Moving to unload")
            if self.in_woods:
                self.go_woods()
            self.wait_stamina()
            self.player.move(*LJ_CONTAINER_COORDS, accuracy=0)
            tools.ping_delay()
            log("Moving to unload done")
        self.player.use_object(LJ_CONTAINER_ID)

    @alive_action
    def check_hatchet(self):
        if self.hatchet:
            return True

        if self.in_woods:
            return False

        log("Moving to grab a Hatchet")
        self.move_to_unload()
        container_hatchet = self.player.find_type(constants.TYPE_ID_HATCHET, LJ_CONTAINER_ID)
        if not container_hatchet:
            todo = GetFindedList()
            log("WARNING! NO SPARE HATCHETS FOUND!")
            tools.telegram_message(f"{self.player}: No hatchets found: {todo}")
            self.quit()
            return

        while not self.got_hatchet and not self.player.move_item(container_hatchet):
            log("Grabbing a Hatchet")
            tools.ping_delay()

        return True

    def check_bandages(self):
        return self._check_bandages(HOLD_BANDAGES, LJ_CONTAINER_ID)

    def eat(self):
        return self._eat(LJ_CONTAINER_ID)

    def count_logs(self, recursive=True):
        logs_type_ids = (constants.TYPE_ID_LOGS,)
        logs_colors = constants.COLOR_LOGS
        logs = self.player.find_types_backpack(type_ids=logs_type_ids, colors=logs_colors, recursive=recursive)
        if not logs:
            return

        for logs_id in logs:
            log_obj = Item(logs_id)
            log_type = log_obj.type_
            log_color = log_obj.color
            log_quantity = log_obj.quantity
            if self.script_stats.get(log_type, None) is None:
                self.script_stats[log_type] = {}
            if self.script_stats[log_type].get(log_color, None) is None:
                self.script_stats[log_type][log_color] = 0
            self.script_stats[log_type][log_color] += log_quantity

    def unload(self):
        log("Unloading")
        self.move_to_unload()
        self.move_to_unload()
        unload_types = [
            constants.TYPE_ID_LOGS,
            *constants.TYPE_IDS_LOOT,
            *constants.TYPE_IDS_LJ_LOOT
        ]
        self.count_logs()
        self.parse_commands()
        self.player.unload_types(unload_types, LJ_CONTAINER_ID)
        self.check_hatchet()
        self.check_bandages()
        self.rearm_from_container()
        self.eat()

    def tree_depleeted(self):
        log(f"{self.current_tree} Depleeted.")
        self.current_tree = None

    def _jack_tree(self, tile_type, x, y, z):
        self.parse_commands()
        CancelWaitTarget()
        self.player.use_object(self.hatchet)
        WaitTargetTile(tile_type, x, y, z)

    @property
    def got_logs(self):
        # noinspection PyProtectedMember
        return self.player.got_item_type(constants.TYPE_ID_LOGS)

    def general_weight_check(self):
        if self.got_logs and self.player.overweight:
            self.unload_and_return()

    @property
    def in_woods(self):
        _, y, _, _ = self.player.coords
        output = y >= WOOD_ZONE_Y
        return output

    def jack_tree(self):
        while self.player.overweight:
            self.general_weight_check()
        self.move_to_tree()
        ClearJournal()
        self._jack_tree(*self.current_tree)

    def check_overweight(self, drop_types=None):
        drop_types = [
            (constants.TYPE_ID_LOGS, constants.COLOR_LOGS_S, constants.WEIGHT_LOGS),
            (constants.TYPE_ID_LOGS, -1, constants.WEIGHT_LOGS),
        ]
        return super().check_overweight(drop_types)

    def go_woods(self):
        self.check_overweight()
        self.wait_stamina()
        log(f"Going to the woods")
        self.player.move(*WOOD_ENTRANCE)
        self.player.open_backpack()
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

    def engage_mob(self, mob: Mob, **kwargs):
        return super().engage_mob(mob=mob, check_health_func=self.lj_check_health, loot=LOOT_CORPSES, cut=CUT_CORPSES,
                                  drop_trash_items=True)

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
                self.process_mobs()
                self.lj_check_health()
                self.check_weapon()
                self.lj_check_hatchets()
                self.general_weight_check()
                self.jack_tree()
                continue

            self.parse_commands()
            self.process_mobs()
            self.lj_check_health()
            self.check_weapon()
            self.lj_check_hatchets()
            self.general_weight_check()
            i += 1
            if i > 2:
                self.jack_tree()
                i = 0

            Wait(constants.USE_COOLDOWN)

    def loot_corpses(self):
        if not LOOT_CORPSES:
            return

        return super().loot_corpses()

    def check_weapon(self, **kwargs):
        if not EQUIP_WEAPONS_FROM_GROUND:
            return

        return super().check_weapon(max_weapon_search_distance=MAX_WEAPON_SEARCH_DISTANCE)

    def rearm_from_container(self, **kwargs):
        if not EQUIP_WEAPONS_FROM_LOOT_CONTAINER:
            return

        return super().rearm_from_container(container_id=LJ_CONTAINER_ID)

    def start(self):
        self._start_time = pendulum.now()
        self.check_health()
        self.general_weight_check()
        dist_to_container = self.player.path_distance_to(*LJ_CONTAINER_COORDS)
        if dist_to_container < 20:
            self.unload()
        if not self.in_woods:
            self.go_woods()

        self.lumberjack_process()


if __name__ == '__main__':
    if debug:
        tools.debug()

    Lumberjack().start()
    print("")
