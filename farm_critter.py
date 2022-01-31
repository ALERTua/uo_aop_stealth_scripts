from copy import copy

import pendulum

from entities.item import Item
from entities.mob import Mob
from tools import tools, constants
from tools.tools import log
from entities.base_script import ScriptBase, stealth


ROAM_COORDS = [
    (2475, 218),
    (2563, 263),
    (2564, 265),
    (2584, 242),
    (2585, 274),
    (2576, 337),
]
MAX_RANGE = 25
ENGAGE_RANGED_MOBS = True
ENGAGE_MELEE_MOBS = True
ENGAGE_CRITTERS = True
LOOT_CORPSES = True
CUT_CORPSES = True
LOOT_CONTAINER_ID = 0x728F3B3B
LOOT_CONTAINER_COORDS = (2470, 182)
TRASH_ITEM_IDS = constants.ITEM_IDS_TRASH
TRASH_ITEM_IDS.remove(constants.TYPE_ID_MACE)  # mace from trolls is useful
LOOT_ITEMS = constants.TYPE_IDS_LOOT
LOOT_ITEMS.extend([constants.TYPE_ID_MACE, constants.TYPE_ID_BATTLE_AXE])  # mace from trolls is useful
HOLD_BANDAGES = 5


class FarmCritter(ScriptBase):
    def __init__(self):
        super().__init__()
        self.roam_spots = ROAM_COORDS or [self.player.coords]
        self.max_range = MAX_RANGE
        self._spots = []
        self._current_spot = None

    @property
    def current_spot(self):
        if not self._current_spot:
            if not self._spots:
                self._spots = copy(self.roam_spots)
            closest_spot = self.player.get_closest_coords(self._spots)
            spot_index = self._spots.index(closest_spot)
            self._current_spot = self._spots.pop(spot_index)
            log.info(f"New Closest Spot: {self._current_spot}. Spots left: {len(self._spots)}/{len(self.roam_spots)}")
        return self._current_spot

    @current_spot.setter
    def current_spot(self, value):
        self._current_spot = value

    def spot_depleeted(self):
        log.info(f"{self.current_spot} Depleeted.")
        self.current_spot = None

    def move_to_unload(self):
        self.parse_commands()
        dist_to_container = stealth.Dist(self.player.x, self.player.y, *LOOT_CONTAINER_COORDS)
        if dist_to_container > 1:
            log.info("Moving to unload")
            self.wait_stamina()
            self.player.move(*LOOT_CONTAINER_COORDS, accuracy=0)
            tools.ping_delay()
            log.info("Moving to unload done")
        self.player.use_object(LOOT_CONTAINER_ID)

    def check_bandages(self):
        return self._check_bandages(HOLD_BANDAGES, LOOT_CONTAINER_ID)

    def eat(self, **kwargs):
        return super().eat(container_id=LOOT_CONTAINER_ID)

    def unload(self):
        log.info("Unloading")
        self.move_to_unload()
        self.move_to_unload()
        unload_types = [
            constants.TYPE_ID_LOGS,
            *constants.TYPE_IDS_LOOT,
            *constants.TYPE_IDS_LJ_LOOT,
            *constants.TYPE_IDS_MINING_LOOT,
        ]
        self.parse_commands()
        self.player.unload_types(unload_types, LOOT_CONTAINER_ID)
        self.check_bandages()
        self.check_weapon()
        self.eat()

    def pick_up_items(self, **kwargs):
        type_ids = [
            constants.TYPE_ID_LOGS,
            *constants.TYPE_IDS_LOOT,
            *constants.TYPE_IDS_LJ_LOOT,
            *constants.TYPE_IDS_MINING_LOOT,
        ]
        return super().pick_up_items(type_ids)

    def general_weight_check(self):
        if self.player.near_max_weight:
            self.unload_and_return()

    def move_to_spot(self):
        self.parse_commands()
        self.check_overweight()
        self.wait_stamina(5)
        running = self.player.near_max_weight is False and self.player.stamina > 10
        self.player.move(*self.current_spot, accuracy=0, running=running)
        self.pick_up_items()
        self.check_overweight()
        self.general_weight_check()

    def unload_and_return(self):
        self.player.break_action()
        self.check_overweight(constants.TYPE_IDS_LOOT)
        self.unload()
        self.move_to_spot()

    def farm_check_health(self):
        if not self.check_health():
            self.unload_and_return()

    def engage_mob(self, mob: Mob, *args, **kwargs):
        return super().engage_mob(mob=mob, check_health_func=self.farm_check_health, loot=LOOT_CORPSES, cut=CUT_CORPSES,
                                  drop_trash_items=True, notify_only_mutated=True)

    def process_mobs(self, *args, **kwargs):
        mob_type_ids = self.mob_type_ids(ranged=ENGAGE_RANGED_MOBS, melee=ENGAGE_MELEE_MOBS, critter=ENGAGE_CRITTERS)
        return super().process_mobs(mob_type_ids=mob_type_ids, engage=True)

    def check_weapon(self):
        if self.player.weapon_equipped:
            return

        weapons_type_ids = constants.TYPE_IDS_WEAPONS
        container_weapon_ids = []
        for weapon_type_id in weapons_type_ids:
            found_weapon_type = self.player.find_type(weapon_type_id, LOOT_CONTAINER_ID)
            if not found_weapon_type:
                continue
            found_weapons = stealth.GetFoundList()
            container_weapon_ids.extend(found_weapons)

        if not container_weapon_ids:
            log.info("WARNING! NO SPARE WEAPONS FOUND!")
            tools.telegram_message(f"{self.player}: No weapons found")
            self.quit()
            return

        weapon_obj = Item.instantiate(container_weapon_ids[0])
        while not self.player.weapon_equipped:
            log.info(f"Equipping weapon {weapon_obj}")
            self.player.equip_weapon_id(weapon_obj)
            tools.ping_delay()

    def farm_check_weapon(self):
        if not self.player.weapon_equipped:
            self.unload_and_return()

    def loop(self):
        self.move_to_spot()
        self.process_mobs()
        self.farm_check_weapon()
        self.spot_depleeted()

    def start(self):
        self._start_time = pendulum.now()
        self.general_weight_check()
        dist_to_container = stealth.Dist(self.player.x, self.player.y, *LOOT_CONTAINER_COORDS)
        if dist_to_container < 20:
            self.unload()

        while True:
            self.loop()


if __name__ == '__main__':
    FarmCritter().start()
    print("")
