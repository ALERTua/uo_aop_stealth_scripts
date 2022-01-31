import re
from copy import copy

import pendulum

from entities.base_script import ScriptBase, alive_action, condition, stealth
from entities.container import Container
from entities.item import Item
from entities.mob import Mob
from entities.weapon import Hatchet
from tools import constants, tools
from tools.tools import log

LJ_SLOGS = True
ENGAGE_MOBS = True
ENGAGE_CRITTERS = True
MOB_FIND_DISTANCE = 20
LOOT_CORPSES = True
CUT_CORPSES = True
HOLD_BANDAGES = 2
RESURRECT_AND_RETURN = True
EQUIP_WEAPONS_FROM_GROUND = True
EQUIP_WEAPONS_FROM_LOOT_CONTAINER = True
MAX_WEAPON_SEARCH_DISTANCE = 20
MAX_LJ_ITERATIONS = 2
LJ_DISTANCE_TO_TREE = 1
LJ_CONTAINER_ID = 0x728F3B3B
LJ_CONTAINER_COORDS = (2470, 182)
WOOD_ENTRANCE = (2503, 167)
WOOD_ZONE_Y = 188
LJ_TRASH = [
    *constants.ITEM_IDS_TRASH,
    constants.TYPE_ID_ARMOR_LEATHER_BUSTIER,
    constants.TYPE_ID_ARMOR_LEATHER_SKIRT,
]
LJ_LOOT = [
    constants.TYPE_ID_LOGS,
    constants.TYPE_ID_HIDE,
    *constants.TYPE_IDS_LOOT,
    # constants.TYPE_ID_BANDAGE,
    # constants.TYPE_ID_HATCHET,
]
LJ_LOOT = [i for i in LJ_LOOT if i not in LJ_TRASH]

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
        x, y = LJ_CONTAINER_COORDS
        self.loot_container = Container.instantiate(LJ_CONTAINER_ID, x=x, y=y, z=None, fixed_coords=True)
        self._trees = []
        self._current_tree = None
        self.lj_i = 0
        self.drop_types = [
            (constants.TYPE_ID_LOGS, constants.COLOR_LOGS_S, constants.WEIGHT_LOGS),
            (constants.TYPE_ID_LOGS, -1, constants.WEIGHT_LOGS),
        ]

    @property
    def current_tree(self):
        if not self._current_tree:
            if not self._trees:
                self._trees = copy(LJ_SPOTS)
                self.report_stats()
            self._current_tree = self._trees.pop(0)
            log.info(f"{len(self._trees)}/{len(LJ_SPOTS)} New Tree: {self._current_tree}.")
        return self._current_tree

    @current_tree.setter
    def current_tree(self, value):
        self._current_tree = value

    @property
    def hatchet(self):
        return Hatchet.instantiate(self.player.find_type_backpack(constants.TYPE_ID_HATCHET))

    @property
    def got_hatchet(self):
        return self.hatchet not in (None, 0, -1)

    def pick_up_items(self, **kwargs):
        return super().pick_up_items(LJ_LOOT)

    def process_mobs(self, **kwargs):
        return super().process_mobs(engage=ENGAGE_MOBS, notify_only_mutated=True, mob_find_distance=MOB_FIND_DISTANCE,
                                    drop_overweight_items=self.drop_types)

    def move_to_tree(self):
        self._checks()
        tile_type, x, y, z = self.current_tree
        while self.player.distance_to(x, y) > LJ_DISTANCE_TO_TREE:
            log.info(f"Moving to the next tree: {self.current_tree}")
            self.wait_stamina(5)
            self.player.move(x, y, accuracy=LJ_DISTANCE_TO_TREE, running=self.should_run)
            self._checks()

    def move_to_unload(self):
        self.parse_commands()
        if self.player.path_distance_to(*self.loot_container.xy) > 1:
            log.info("Moving to unload")
            if self.in_woods:
                self.go_woods()
            self.wait_stamina()
            self.player.move(*self.loot_container.xy, accuracy=0)
        tools.ping_delay()
        self.player.use_object(self.loot_container)
        log.info("Moving to unload done")

    @alive_action
    def check_hatchet(self):
        if self.hatchet:
            return True

        if self.in_woods:
            return False

        log.info("Moving to grab a Hatchet")
        self.move_to_unload()
        container_hatchet = self.player.find_type(constants.TYPE_ID_HATCHET, self.loot_container)
        if not container_hatchet:
            todo = stealth.GetFindedList()
            log.info("WARNING! NO SPARE HATCHETS FOUND!")
            tools.telegram_message(f"{self.player}: No hatchets found: {todo}")
            self.quit()
            return

        while not self.got_hatchet and not self.player.move_item(container_hatchet):
            log.info("Grabbing a Hatchet")
            tools.ping_delay()

        return True

    def check_bandages(self):
        return self._check_bandages(HOLD_BANDAGES, self.loot_container)

    def eat(self, **kwargs):
        return super().eat(container_id=self.loot_container)

    def count_logs(self, recursive=True):
        logs_type_ids = (constants.TYPE_ID_LOGS,)
        logs = self.player.find_types_backpack(type_ids=logs_type_ids, colors=constants.COLOR_LOGS, recursive=recursive)
        if not logs:
            return

        for logs_id in logs:
            log_obj = Item.instantiate(logs_id)
            log_type = log_obj.type_id
            log_color = log_obj.color
            log_quantity = log_obj.quantity
            if self.script_stats.get(log_type, None) is None:
                self.script_stats[log_type] = {}
            if self.script_stats[log_type].get(log_color, None) is None:
                self.script_stats[log_type][log_color] = 0
            self.script_stats[log_type][log_color] += log_quantity

    def unload(self):
        log.info("Unloading")
        self.move_to_unload()
        self.move_to_unload()
        self.count_logs()
        self.parse_commands()
        self.player.unload_types(LJ_LOOT, self.loot_container)
        self.check_hatchet()
        self.check_bandages()
        self.rearm_from_container()
        self.eat()

    def tree_depleeted(self):
        log.info(f"{len(self._trees)}/{len(LJ_SPOTS)} Tree depleeted: {self.current_tree}.")
        self.current_tree = None

    def _jack_tree(self, tile_type, x, y, z):
        while self.player.overweight:  # consider near_max_weight
            self.parse_commands()
            self.drop_trash()
            self.general_weight_check()
            self.check_overweight()

        self.player.use_object_on_tile(self.hatchet, tile_type, x, y, z)
        self.parse_commands()

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
        stealth.ClearJournal()
        self._jack_tree(*self.current_tree)

    def check_overweight(self, **kwargs):
        return super().check_overweight(self.drop_types)

    def go_woods(self):
        self.check_overweight()
        self.wait_stamina()
        log.info(f"Going to the woods")
        self.player.move(*WOOD_ENTRANCE)
        self.player.open_backpack()
        log.info(f"Going to the woods done")
        self.wait_stamina(5)

    def check_health(self, **kwargs):
        return super().check_health(resurrect=RESURRECT_AND_RETURN)

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
                                  drop_trash_items=True, trash_items=LJ_TRASH)

    def _checks(self, check_overweight=True, loot_corpses=True):
        self.parse_commands()
        self.lj_check_health()
        if check_overweight:
            self.general_weight_check()
        if self.process_mobs():
            self.lj_i = MAX_LJ_ITERATIONS  # force dig again after a mob is killed
        if loot_corpses:
            self.loot_corpses()
        self.check_weapon()
        self.pick_up_items()
        if check_overweight:
            self.drop_trash()
        self.lj_check_hatchets()
        if check_overweight:
            self.general_weight_check()

    def lumberjack_process(self):
        self.jack_tree()
        self.lj_i = 0
        while True:
            if msg := tools.in_journal(r'skip \d+ tree[s]', regexp=True, return_re_value=True):
                trees_quantity = int(re.findall(r'\d+', msg[0])[0])
                log.info(f"Skipping {trees_quantity} trees")
                for i in range(trees_quantity):
                    self.tree_depleeted()
                self.lj_i = 0
                self.jack_tree()
                continue
            elif any(_ for _ in LJ_ERRORS if tools.in_journal(_)):
                self.tree_depleeted()
                self.lj_i = 0
                self._checks()
                if self.general_weight_check():
                    self.lj_i = MAX_LJ_ITERATIONS
                self.jack_tree()
                continue

            self._checks()  # check for overweight too, and loot corpses
            self.lj_i += 1
            if self.lj_i > MAX_LJ_ITERATIONS:
                self.player._use_cd = pendulum.now()
                self.jack_tree()
                self.lj_i = 0

            last_journal_message = stealth.LastJournalMessage()
            log.info(f"{self.lj_i}/{MAX_LJ_ITERATIONS} Waiting for lumberjacking to complete: {last_journal_message}")
            stealth.Wait(constants.USE_COOLDOWN)

    @condition(LOOT_CORPSES)
    def loot_corpses(self, **kwargs):
        return super().loot_corpses(drop_trash_items=True, trash_items=LJ_TRASH)

    def drop_trash(self, **kwargs):
        return super(Lumberjack, self).drop_trash(trash_items=LJ_TRASH)

    @condition(EQUIP_WEAPONS_FROM_GROUND)
    def check_weapon(self, **kwargs):
        return super().check_weapon(max_weapon_search_distance=MAX_WEAPON_SEARCH_DISTANCE)

    @condition(EQUIP_WEAPONS_FROM_LOOT_CONTAINER)
    def rearm_from_container(self, **kwargs):
        return super().rearm_from_container(container_id=self.loot_container)

    def start(self):
        log.info(f"Starting {self.scenario_name}")
        self._start_time = pendulum.now()
        self.check_health()
        self.general_weight_check()
        dist_to_container = self.player.path_distance_to(*self.loot_container.xy)
        if dist_to_container < 20:
            self.unload()
        if not self.in_woods:
            self.go_woods()

        self.lumberjack_process()


if __name__ == '__main__':
    Lumberjack().start()
    print("")
