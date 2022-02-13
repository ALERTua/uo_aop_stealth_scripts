import re
from copy import copy
from typing import Iterable

import pendulum

from entities.base_script import ScriptBase, alive_action, condition, stealth
from entities.container import Container
from entities.item import Item
from entities.mob import Mob
from entities.weapon import Hatchet
from tools import constants, tools
from tools.tools import log

LJ_SLOGS = True  # simple logs
ENGAGE_MOBS = True
ENGAGE_CRITTERS = True
MOB_FIND_DISTANCE = 25
LOOT_CORPSES = True
CUT_CORPSES = True
HOLD_BANDAGES = 2
RESURRECT_AND_RETURN = True
EQUIP_WEAPONS_FROM_GROUND = True
EQUIP_WEAPONS_FROM_LOOT_CONTAINER = True
RESET_PROCESSED_MOBS_ON_UNLOAD = True
MAX_WEAPON_SEARCH_DISTANCE = 20
CORPSE_FIND_DISTANCE = 20
MAX_LJ_ITERATIONS = 4  # starting from 0
LJ_DISTANCE_TO_TREE = 1
LJ_CONTAINER_ID = 0x728F3B3B
LOOT_CONTAINER_OPEN_SUBCONTAINERS = True
LJ_CONTAINER_COORDS = (2470, 182)
WOOD_ENTRANCE = (2503, 167)
WOOD_ZONE_Y = 188
MOUNT_ID = 0x076C4894
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
LJ_SLOGS_SUCCESS = [
    'Вы положили несколько бревен в сумку.',
]
LJ_SUCCESS_MESSAGES = [
    *LJ_SLOGS_SUCCESS,
    'Вы нарубили ',
    'Вы рубите, но бревна у Вас не получаются.',
]
LJ_ERRORS = [
    'Здесь нет больше дерева для вырубки.',
    'Вы не можете использовать клинок на это.',
    'Вы находитесь слишком далеко!',
]
if not LJ_SLOGS:
    LJ_ERRORS.extend(LJ_SLOGS_SUCCESS)
    [LJ_SUCCESS_MESSAGES.remove(i) for i in LJ_SLOGS_SUCCESS]


class Lumberjack(ScriptBase):
    def __init__(self):
        super().__init__()
        x, y = LJ_CONTAINER_COORDS
        self.loot_container = Container.instantiate(LJ_CONTAINER_ID, x=x, y=y, z=None, fixed_coords=True)
        self._trees = []
        self._current_tree = None
        self.lj_i = 0
        self.unload_itemids = LJ_LOOT
        self.trash_item_ids = LJ_TRASH
        self.drop_types = [
            (constants.TYPE_ID_LOGS, constants.COLOR_LOGS_S, constants.WEIGHT_LOGS),
            (constants.TYPE_ID_LOGS, -1, constants.WEIGHT_LOGS),
        ]
        self.player._mount = MOUNT_ID

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
        return self.hatchet.exists

    @alive_action
    def pick_up_items(self, **kwargs):
        return super().pick_up_items(self.unload_itemids)

    @alive_action
    def process_mobs(self, **kwargs):
        return super().process_mobs(engage=ENGAGE_MOBS, notify_mutated=True, mob_find_distance=MOB_FIND_DISTANCE,
                                    drop_overweight_items=self.drop_types)

    @alive_action
    def move_to_tree(self):
        self._checks()
        tile_type, x, y, z = self.current_tree
        while self.player.distance_to(x, y) > LJ_DISTANCE_TO_TREE:
            log.info(f"{len(self._trees)}/{len(LJ_SPOTS)} Moving to the next tree: {self.current_tree}")
            self.wait_stamina(5)
            self.player.move(x, y, accuracy=LJ_DISTANCE_TO_TREE, running=self.should_run)
            self._checks()

    @alive_action
    def move_to_unload(self, **kwargs):
        self.parse_commands()
        if self.player.path_distance_to(*self.loot_container.xy) > 1:
            log.info("Moving to unload")
            if self.in_woods:
                self.go_woods()
            self.wait_stamina()
            self.player.move_to_object(self.loot_container, accuracy=1)
            log.info("Moving to unload done")
        tools.ping_delay()
        if self.loot_container.is_empty:
            self.player.open_container(self.loot_container)
        subcontainers = LOOT_CONTAINER_OPEN_SUBCONTAINERS
        if subcontainers:
            if isinstance(subcontainers, Iterable):
                subcontainers = [Container.instantiate(i, force_class=True) for i in subcontainers]
            else:
                subcontainers = self.player.find_types_container(
                    constants.TYPE_IDS_CONTAINER, container_ids=self.loot_container, recursive=True)
            for container in subcontainers:
                if container.is_empty:
                    self.player.open_container(container)

    @alive_action
    def check_hatchet(self):
        if self.got_hatchet:
            return True

        if self.in_woods:
            return False

        log.info("Moving to grab a Hatchet")
        self.move_to_unload()
        container_hatchet = self.player.find_types_container(
            constants.TYPE_ID_HATCHET, container_ids=self.loot_container, recursive=True)
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

    @alive_action
    def check_bandages(self, **kwargs):
        return self._check_bandages(HOLD_BANDAGES, self.loot_container)

    @alive_action
    def eat(self, **kwargs):
        return super().eat(container_id=self.loot_container)

    def record_stats(self):
        items = self.player.find_types_backpack(type_ids=self.unload_itemids, recursive=True)
        if not items:
            return

        for item in items:
            items_obj = Item.instantiate(item)
            type_id = items_obj.type_id
            color = items_obj.color
            quantity = items_obj.quantity
            name = items_obj.name_short
            entry_name = f"{type_id}({color}){name}"
            log.debug(f"StatLogging {item}")
            self.script_stats[entry_name] = self.script_stats.get(entry_name, 0) + quantity

    @alive_action
    def unload(self, **kwargs):
        log.info("Unloading")
        self.move_to_unload()
        self.record_stats()
        self.parse_commands()
        self.player.unload_types(self.unload_itemids, self.loot_container)
        self.check_hatchet()
        self.check_bandages()
        self.rearm_from_container()
        self.eat()
        if RESET_PROCESSED_MOBS_ON_UNLOAD:
            self._processed_mobs = []
        self.report_stats()

    def tree_depleeted(self):
        log.info(f"{len(self._trees)}/{len(LJ_SPOTS)} Tree depleeted: {self.current_tree}.")
        self.current_tree = None
        self._processed_mobs = []

    def _jack_tree(self, tile_type, x, y, z):
        while self.player.overweight:  # consider near_max_weight
            self.parse_commands()
            self.drop_trash()
            self.general_weight_check()
            self.check_overweight()

        self.parse_commands()
        self.player.use_object_on_tile(self.hatchet, tile_type, x, y, z)
        tools.result_delay()

    @property
    def got_logs(self):
        # noinspection PyProtectedMember
        return self.player.got_item_type(constants.TYPE_ID_LOGS)

    @alive_action
    def general_weight_check(self):
        if self.got_logs and self.player.overweight:
            self.unload_and_return()

    @property
    def in_woods(self):
        _, y, _, _ = self.player.coords
        output = y >= WOOD_ZONE_Y
        return output

    @alive_action
    def jack_tree(self):
        while self.player.overweight:
            self.general_weight_check()
        # self.lj_check_hatchets()
        self.move_to_tree()
        self.parse_commands()
        self._jack_tree(*self.current_tree)
        output = stealth.HighJournal()
        return output

    @alive_action
    def check_overweight(self, **kwargs):
        return super().check_overweight(self.drop_types, self.trash_item_ids)

    @alive_action
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

    @alive_action
    def unload_and_return(self):
        self.player.break_action()
        self.check_overweight()
        self.unload()
        self.go_woods()
        self.move_to_tree()
        self.lj_i = MAX_LJ_ITERATIONS

    @alive_action
    def engage_mob(self, mob: Mob, **kwargs):
        return super().engage_mob(mob=mob, check_health_func=self.lj_check_health, loot=False, cut=False,
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
        self.lj_check_hatchets()
        self.check_weapon()
        self.pick_up_items()
        if check_overweight:
            self.drop_trash()
        self.lj_check_hatchets()
        if check_overweight:
            self.general_weight_check()

    def lumberjack_process(self):
        previous_journal_index = self.jack_tree()
        self.lj_i = 0
        while True:
            highjournal = stealth.HighJournal()
            journal_contents = []
            if previous_journal_index != highjournal:
                journal_contents = tools.journal(start_index=highjournal)

            skip = [j for j in journal_contents if j.contains(r'skip \d+', regexp=True, return_re_value=True)]
            if any(skip):
                text = skip[0].text
                numbers = re.findall(r'\d+', text)
                trees_quantity = int(numbers[0])
                log.info(f"Skipping {trees_quantity} trees")
                for i in range(trees_quantity):
                    self.tree_depleeted()
                previous_journal_index = self.jack_tree()
                self.lj_i = 0
                continue

            successes = [e for e in LJ_SUCCESS_MESSAGES if any([j.contains(e) for j in journal_contents])]
            if successes:
                previous_journal_index = highjournal
                self.lj_i = 0

            errors = [e for e in LJ_ERRORS if any([j.contains(e) for j in journal_contents])]
            if errors:
                log.debug(f"{len(self._trees)}/{len(LJ_SPOTS)} Depletion message detected: {errors[0]}")
                self.tree_depleeted()
                self._checks()
                if self.general_weight_check():
                    self.lj_i = MAX_LJ_ITERATIONS
                previous_journal_index = self.jack_tree()
                self.lj_i = 0
                continue

            self._checks(loot_corpses=False)
            self.lj_i += 1
            if self.lj_i > MAX_LJ_ITERATIONS:
                previous_journal_index = self.jack_tree()
                self.lj_i = 0

            line_contents = ''
            if journal_contents:
                line_contents = f" : {len(journal_contents)} : {journal_contents[-1].text_clean}"
            log.info(f"{len(self._trees)}/{len(LJ_SPOTS)} {self.player.weight:>3}/{self.player.max_weight} "
                     f"{self.lj_i}/{MAX_LJ_ITERATIONS + 1}{line_contents}")
            stealth.Wait(constants.USE_COOLDOWN / 6)

    @condition(LOOT_CORPSES)
    def loot_corpses(self, **kwargs):
        return super().loot_corpses(cut_corpses=CUT_CORPSES, trash_items=LJ_TRASH,
                                    corpse_find_distance=CORPSE_FIND_DISTANCE)

    def drop_trash(self, **kwargs):
        return super(Lumberjack, self).drop_trash(trash_items=self.trash_item_ids)

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
