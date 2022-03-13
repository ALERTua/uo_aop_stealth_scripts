import random
import re
from copy import copy

from entities.base_weapon import Weapon
from entities.container import Container
from entities.item import Item
from entities.weapon import FishingPole
from tools import tools, constants
from entities.base_script import ScriptBase, log, stealth
from py_stealth import *

ROAM_COORDS = [
    (2434, 234),
    (2437, 244),
    (2443, 252),
    (2447, 260),
    (2442, 269),
    (2436, 277),
    (2446, 274),
    (2455, 274),
    (2463, 269),
    (2473, 265),
    (2464, 254),
]
MOUNT_ID = 0x0770DDB1
FISHING_MAX_RANGE = 5
MAX_RANGE = 25
MOB_FIND_DISTANCE = 40
ENGAGE_MOBS = True
NOTIFY_ONLY_MUTATED_MOBS = False
NOTIFY_RANGED_MOBS = True
USE_RANGED_WEAPON = True
NOTIFY_MOB_ERRORS = True
MAX_WEAPON_SEARCH_DISTANCE = 20
RANGED_WEAPON_TYPES = [constants.TYPE_ID_CROSSBOW, ]
RANGED_AMMO = constants.TYPE_ID_BOLTS
RANGED_AMMO_ENSURE_QUANTITY = 200
RANGED_AMMO_MINIMUM = 30
RANGED_UNMOUNT = True
RANGED_KEEP_DISTANCE = 8
LOOT_CORPSES = True
CUT_CORPSES = True
MAX_ITERATIONS = 8  # starting from 0
MAX_FAIL_SAFE = MAX_ITERATIONS * 5  # starting from 0
LOOT_CONTAINER_ID = 0x7292F926
LOOT_CONTAINER_COORDS = (2467, 182)
HOLD_BANDAGES = 7
WATER_TILE_TYPE_IDS = [0x179A, 0x179B, 0x179C, 0x1797, 0x1799, ]

FISHING_ERRORS = [
    'А рыбы больше нет.',
    'Рыба покинула эти места.',
    'Жара, все рыба ушла из лимана',
    'Вы распугали всю рыбу.',
    'Вся рыба на нересте.',
    'Тут только тина морская.',
    'Кроме воды вы тут ничего не поймаете.',
    'Эта местность исчерпала себя.',
    'Тут рыба не водится.',
    'Вы выловили всю рыбу.',
]
FISHING_SUCCESS_MESSAGES = [
    'А вот и рыбка!',
    'Вы выловили ',
]
ERRORS_TOO_MUCH_FISH = [
    'Вы поймали рыбу, но вам некуда ее положить',
]

FISHING_TRASH = [
    0x0FC7,
    0x0FC6,
    0x0EA8,
    0x0EA4,
    0x0EA1,
    0x0EA7,
    0x0EA2,
    0x0EA5,
    0x0FCC,
    0x0FCA,
    0x1AE1,
    0x1AE2,
    0x1AE4,
    0x0EA3,
    0x1EA3,
    0x1EA5,
    0x0EC8,
    0x0FC4,
    0x0FC7,
    0x0FC8,
    0x1AE0,
    0x0FC9,
    0x0FCB,
    0x0EC8,
    0x0EA0,
    0x0FC5,
    0x1AD8,
    0x0EC9,
    constants.TYPE_ID_SHIELD_BRONZE,
]
FISHING_LOOT = [
    constants.TYPE_ID_RAW_FISHSTEAKS,
    *constants.TYPE_IDS_LOOT,
]
if USE_RANGED_WEAPON:
    FISHING_LOOT = [i for i in FISHING_LOOT if i not in [RANGED_AMMO, *RANGED_WEAPON_TYPES]]
FISHING_LOOT = [i for i in FISHING_LOOT if i not in FISHING_TRASH]


class Fishing(ScriptBase):
    def __init__(self):
        super().__init__()
        self.roam_spots = ROAM_COORDS or [self.player.coords]
        self.max_range = MAX_RANGE
        self._spots = []
        self._current_spot = None
        self.i = 0
        self.fail_safe_i = 0
        self.unload_itemids = FISHING_LOOT
        x, y = LOOT_CONTAINER_COORDS
        self.loot_container = Container.instantiate(LOOT_CONTAINER_ID, x=x, y=y, fixed_coords=True)
        self.trash_item_ids = FISHING_TRASH
        self.player._mount = MOUNT_ID
        self.spot_coords = self.player.xy
        self._hold_bandages = HOLD_BANDAGES
        self.tool_typeid = constants.TYPE_ID_TOOL_FISHING_POLE

    @property
    def current_spot(self):
        if not self._current_spot:
            if not self._spots:
                self._spots = copy(self.roam_spots)
            closest_spot = self.player.get_closest_coords(self._spots)
            spot_index = self._spots.index(closest_spot)
            self._current_spot = self._spots.pop(spot_index)
            log.debug(f"New Closest Spot: {self._current_spot}. Spots left: {len(self._spots)}/{len(self.roam_spots)}")
        return self._current_spot

    @current_spot.setter
    def current_spot(self, value):
        self._current_spot = value

    @property
    def fishing_pole(self):
        obj_id = ObjAtLayer(LhandLayer())
        if obj_id and stealth.GetType(obj_id) == constants.TYPE_ID_TOOL_FISHING_POLE:
            output_id = obj_id
        else:
            output_id = self.player.find_type_backpack(constants.TYPE_ID_TOOL_FISHING_POLE)
        if output_id:
            return FishingPole.instantiate(output_id)

    @property
    def got_fishing_pole(self):
        return self.fishing_pole and self.fishing_pole.exists

    def equip_fishing_pole(self):
        if not self.fishing_pole:
            return False

        if not self.fishing_pole.equipped:
            self.player.disarm()
            self.player.equip_weapon_id(self.fishing_pole)
        return True

    def _get_tiles(self):
        x = self.player.x
        y = self.player.y
        max_coord = FISHING_MAX_RANGE
        xmin = x - max_coord
        xmax = x + max_coord
        ymin = y - max_coord
        ymax = y + max_coord
        tiles = GetStaticTilesArray(xmin, ymin, xmax, ymax, WorldNum(), WATER_TILE_TYPE_IDS)
        return tiles

    def no_fishing_pole_loop(self):
        while not self.got_fishing_pole:
            self.unload_and_return()
        pass  # todo: overweight, stamina, go to unload, unload, get pole, return

    def fish_check_health(self):
        if not self.check_health():
            self.unload_and_return()

    @property
    def ranged_weapon(self):
        if not USE_RANGED_WEAPON:
            return

        weapons = self.player.find_types_character(RANGED_WEAPON_TYPES)
        if not weapons:
            return

        return Weapon.instantiate(weapons[0])

    def process_mobs(self, **kwargs):
        return super(Fishing, self).process_mobs(
            engage=ENGAGE_MOBS, notify_mutated=NOTIFY_ONLY_MUTATED_MOBS, notify_ranged=NOTIFY_RANGED_MOBS,
            notify_errors=NOTIFY_MOB_ERRORS, loot=LOOT_CORPSES, cut=CUT_CORPSES, mob_find_distance=MOB_FIND_DISTANCE,
            drop_overweight_items=False, ranged=USE_RANGED_WEAPON, check_health_func=self.fish_check_health,
            ranged_weapon=self.ranged_weapon, ranged_unmount=RANGED_UNMOUNT, ranged_keep_distance=RANGED_KEEP_DISTANCE,
            drop_trash_items=True, trash_items=self.trash_item_ids, path_distance=False, **kwargs)

    def check_weapon_loop(self):
        if not USE_RANGED_WEAPON:
            return self.check_weapon(max_weapon_search_distance=MAX_WEAPON_SEARCH_DISTANCE)

        if self.ranged_weapon:
            if ammo := self.player.find_type_backpack(RANGED_AMMO):
                ammo = Item.instantiate(ammo)
                if ammo.quantity > RANGED_AMMO_MINIMUM:
                    return

        log.debug(f"Entering {tools.get_function_name()}")
        self.unload_and_return()
        log.debug(f"Exiting {tools.get_function_name()}")

    def checks(self, break_action=True):
        # log.debug(f"Entering checks")
        output = True
        self.parse_commands()
        self.overweight_loop()
        if not self.check_health():
            self.unload_and_return()
        if not self.got_fishing_pole or not self.equip_fishing_pole():
            self.no_fishing_pole_loop()
        if self.process_mobs():
            output = False  # force fish again after a mob is killed
        if break_action:
            self.cut_fish()
            self.loot_corpses(trash_items=self.trash_item_ids)
        self.check_weapon_loop()
        if break_action:
            self.pick_up_items()
            self.drop_trash()
            if self.player.stamina < self.player.max_stamina / 4:
                self.player.drink_potion_refresh()
        self.overweight_loop()
        # log.debug(f"Exiting checks: {output}")
        return output

    def _fishing_iteration(self, tile_type, tile_x, tile_y, tile_z):
        self.parse_commands()
        use = self.player.use_object_on_tile(self.fishing_pole, tile_type, tile_x, tile_y, tile_z)
        tools.result_delay()
        return use

    def rearm_from_container(self, **kwargs):
        return  # todo:

    def fishing_iteration(self, tile_type, tile_x, tile_y, tile_z):
        # distance = self.player.distance_to(tile_x, tile_y)
        # if distance > FISHING_MAX_RANGE:
        #     continue
        while self.player.overweight:
            self.move_to_unload()
            self.unload()
        # self.move_to_spot_loop(tile_x, tile_y, accuracy=FISHING_MAX_RANGE)
        self.parse_commands()
        self.checks()
        self._fishing_iteration(tile_type, tile_x, tile_y, tile_z)
        tools.result_delay()
        tools.result_delay()  # todo: investigate
        output = stealth.HighJournal()
        return output

    def tile_reset(self):
        self._processed_mobs = []
        self.i = 0
        self.fail_safe_i = 0
        if self.player.stamina < self.player.max_stamina * 0.2:
            self.player.break_action()
            self.checks(break_action=True)
            self.wait_stamina(0.2)
            self.i = MAX_ITERATIONS

    def cut_fish(self, search_distance=constants.USE_GROUND_RANGE):
        cutting_tool = self.player.corpse_cutting_tool
        if not cutting_tool:
            return  # todo:

        fish = self.player.find_types_ground(constants.TYPE_IDS_FISH, distance=search_distance)
        if fish:
            tools.delay(constants.USE_COOLDOWN)
            for fish_item in fish:
                self.player.use_object_on_object(cutting_tool, fish_item)
                tools.delay(constants.USE_COOLDOWN)

    def unload_get_weapon(self):
        if USE_RANGED_WEAPON:
            if not self.ranged_weapon:
                for item_type in RANGED_WEAPON_TYPES:
                    self._unload_get_item(item_type, self.loot_container)
                    if self.ranged_weapon:
                        break

            self._unload_get_item(RANGED_AMMO, self.loot_container, quantity=RANGED_AMMO_ENSURE_QUANTITY)
        else:
            self._unload_get_item(constants.TYPE_IDS_WEAPONS, self.loot_container)

    def unload_and_return(self):
        self.mount()
        self.player.break_action()
        self.check_overweight()
        self.move_to_unload(self.loot_container)
        self.unload()
        self.move_to_spot_loop(*self.spot_coords)

    def loop(self):
        roam_coords = ROAM_COORDS or [self.player.xy]
        for spot_x, spot_y in roam_coords:
            self.spot_coords = (spot_x, spot_y)
            log.debug(f"Entering spot for {spot_x} {spot_y}")
            self.move_to_spot_loop(spot_x, spot_y)
            tiles = self._get_tiles()
            if not tiles:
                pass  # todo:

            random.shuffle(tiles)
            for tile_type, tile_x, tile_y, tile_z in tiles:
                # log.debug(f"Entering tile loop {tile_type} {tile_x} {tile_y} {tile_z}")
                if not self.checks():
                    self.move_to_spot_loop(spot_x, spot_y)
                    self.equip_fishing_pole()
                previous_journal_index = self.fishing_iteration(tile_type, tile_x, tile_y, tile_z)
                self.tile_reset()
                while True:
                    if self.player.xy != (spot_x, spot_y):
                        self.move_to_spot_loop(spot_x, spot_y)
                        self.equip_fishing_pole()

                    if not self.checks(break_action=False):
                        self.move_to_spot_loop(spot_x, spot_y)
                        self.equip_fishing_pole()
                        self.tile_reset()
                        continue

                    highjournal = stealth.HighJournal()
                    journal_contents = []
                    if previous_journal_index != highjournal:
                        journal_contents = tools.journal(start_index=highjournal)

                    skip = [j for j in journal_contents if j.contains(r'skip \d+', regexp=True, return_re_value=True)]
                    if any(skip):
                        text = skip[0].text
                        numbers = re.findall(r'\d+', text)
                        quantity = int(numbers[0])
                        quantity = min((quantity, len(tiles)))
                        log.info(f"Skipping {quantity}")
                        for i in range(quantity):
                            tiles.pop(0)
                        # self.tile_reset()
                        break

                    successes = [e for e in FISHING_SUCCESS_MESSAGES if any([j.contains(e) for j in journal_contents])]
                    if successes:
                        self.tile_reset()
                        previous_journal_index = highjournal

                    errors = [e for e in FISHING_ERRORS if any([j.contains(e) for j in journal_contents])]
                    if errors:
                        log.debug(f"Depletion message detected: {errors[0]}")
                        # self.tile_reset()
                        break

                    too_much_fish = [e for e in ERRORS_TOO_MUCH_FISH if any([j.contains(e) for j in journal_contents])]
                    if too_much_fish:
                        log.debug(f"Too much fish message detected: {too_much_fish[0]}")
                        if not self.checks():
                            self.move_to_spot_loop(spot_x, spot_y)
                            self.equip_fishing_pole()
                        self.tile_reset()
                        self.cut_fish()
                        previous_journal_index = stealth.HighJournal()
                        continue

                    self.fail_safe_i += 1
                    if self.fail_safe_i > MAX_FAIL_SAFE:
                        log.warning(f"Failsafe: {self.fail_safe_i}. Reconnecting")
                        self.fail_safe_i = 0
                        self.i = MAX_ITERATIONS
                        tools.reconnect()

                    self.i += 1
                    if self.i > MAX_ITERATIONS:
                        log.debug(f'{self.i} > {MAX_ITERATIONS}')
                        self.i = 0
                        previous_journal_index = self.fishing_iteration(tile_type, tile_x, tile_y, tile_z)

                    fail_safe_str = ''
                    if self.fail_safe_i > MAX_FAIL_SAFE * 0.75:
                        fail_safe_str = f' ({self.fail_safe_i}/{MAX_FAIL_SAFE}) '

                    line_contents = ''
                    if journal_contents:
                        line_contents = f" : {len(journal_contents)} : {journal_contents[-1].text_clean}"

                    log.info(f"{self.i}/{MAX_ITERATIONS + 1} {self.player.weight:>3}/{self.player.max_weight} "
                             f"{fail_safe_str}{line_contents}")
                    tools.result_delay()

                # log.debug(f"Exiting tile loop {tile_type} {tile_x} {tile_y} {tile_z}")
            # log.debug(f"Exiting spot for {spot_x} {spot_y}")
            self.checks()
            self.unload_and_return()

    def unload(self, **kwargs):
        super().unload(self.unload_itemids, self.loot_container)
        if not self.player.corpse_cutting_tool:
            self._unload_get_item(constants.TYPE_IDS_CORPSE_CUT_TOOLS, self.loot_container,
                                  condition=lambda i: Weapon.instantiate(i).magic)

    def start(self):
        super(type(self), self).start()
        self.check_overweight(self.unload_itemids, self.trash_item_ids)
        dist_to_container = self.player.path_distance_to_object(self.loot_container)
        if dist_to_container < 20:
            self.unload()

        self.loop()


if __name__ == '__main__':
    Fishing().start()
    print("")
