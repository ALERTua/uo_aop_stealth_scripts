import re  # todo: weapon check and restock
from copy import copy
import pendulum

from entities.container import Container
from entities.item import Item
from entities.mob import Mob
from tools import constants, tools
from entities.base_script import ScriptBase, condition, stealth, alive_action
from tools.tools import log

MINE_IRON = True
SMELT = True
ENGAGE_MOBS = True
LOOT_CORPSES = True
CUT_CORPSES = True
GET_FREE_PICKAXE = True
EQUIP_WEAPONS_FROM_GROUND = True
EQUIP_WEAPONS_FROM_LOOT_CONTAINER = True
RESURRECT_AND_RETURN = True
MAX_WEAPON_SEARCH_DISTANCE = 20
MOB_FIND_DISTANCE = 25
FREE_PICKAXE_CONTAINERS = {
    0x48EA69BC: (2411, 187),
}
MINE_MAX_ITERATIONS = 12
MINE_ENTRANCE_COORDS = (2427, 177)
MINING_CONTAINER_ID = 0x728BAB4E
MINING_CONTAINER_COORDS = (2462, 183)
MINE_FORGE_COORDS = (2413, 184)
MINING_LOOT = [
    *constants.TYPE_IDS_LOOT,
    constants.TYPE_ID_INGOT,
    constants.TYPE_ID_ORE,
    constants.TYPE_ID_BANDAGE,
    constants.TYPE_ID_TOOL_PICKAXE,
    constants.TYPE_ID_HIDE,
    constants.TYPE_ID_HATCHET,  # mobs occasionaly drop hatchets
    constants.TYPE_ID_SCEPTER,
    constants.TYPE_ID_WAND,
]
ITEM_IDS_MINING_TRASH = [
    *constants.ITEM_IDS_TRASH,
    *constants.TYPE_IDS_ARMOR_BONE,
    *constants.TYPE_IDS_ARMOR_PLATE,
    constants.TYPE_ID_SHIELD_WOODEN,
    constants.TYPE_ID_HELMET,
    constants.TYPE_ID_NOSE_HELM,
    constants.TYPE_ID_CLOSE_HELM,
    constants.TYPE_ID_SKINNING_KNIFE,
    constants.TYPE_ID_MEAT_CLEAVER,
    constants.TYPE_ID_BUTCHER_KNIFE,
    constants.TYPE_ID_SCIMITAR,
    *constants.TYPE_ID_STAFFS,
    constants.TYPE_ID_MACE,
    constants.TYPE_ID_DAGGER,
    *constants.TYPE_ID_SCROLLS,
    0x1AE0,  # skull
]
MINING_LOOT = [i for i in MINING_LOOT if i not in ITEM_IDS_MINING_TRASH]
MINING_SPOTS = [
    (2414, 185),
    (2412, 186),
    (2410, 184),
    (2410, 181),
    (2414, 182),
    (2417, 182),
    (2412, 179),
    (2415, 179),
    (2418, 179),
    (2420, 181),
    (2412, 176),
    (2415, 176),
    (2418, 176),

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
        self.mining_i = 0
        x, y = MINING_CONTAINER_COORDS
        self.loot_container = Container.instantiate(MINING_CONTAINER_ID, x=x, y=y, z=None, fixed_coords=True)
        self.drop_types = [
            (constants.TYPE_ID_ORE, constants.COLOR_ORE_IRON, constants.WEIGHT_ORE),
            (constants.TYPE_ID_INGOT, constants.COLOR_INGOT_IRON, constants.WEIGHT_INGOT),
            (constants.TYPE_ID_ORE, -1, constants.WEIGHT_ORE),
            (constants.TYPE_ID_INGOT, -1, constants.WEIGHT_INGOT)
        ]

    @alive_action
    @condition(LOOT_CORPSES)
    def loot_corpses(self, **kwargs):
        return super().loot_corpses(drop_trash_items=True, trash_items=ITEM_IDS_MINING_TRASH)

    def move_to_unload(self):
        self.parse_commands()
        dist_to_container = stealth.Dist(self.player.x, self.player.y, *MINING_CONTAINER_COORDS)
        if dist_to_container > 1:
            log.info("Moving to unload")
            if self.in_mine:
                self.go_to_mine_entrance()
            self.wait_stamina()
            self.player.move(*self.loot_container.xy, accuracy=1)
            tools.ping_delay()
        if self.loot_container.exists and self.player.last_container != self.loot_container \
                and not self.player.open_container(self.loot_container):
            tools.telegram_message(f"Failed to open {self.loot_container}")
        log.info("Moving to unload done")

    @alive_action
    def eat(self, **kwargs):
        return super().eat(MINING_CONTAINER_ID)

    @property
    def pickaxe(self):
        return self.player.find_type_backpack(constants.TYPE_ID_TOOL_PICKAXE)

    @alive_action
    def mine_check_pickaxes(self):
        if self.check_pickaxes():
            pass
        else:
            self.player.break_action()
            self.check_overweight()
            self.unload()
            self.check_pickaxes()
            self.go_to_mine_entrance()
            # self.get_free_pickaxe()
            self.move_mining_spot()

    @alive_action
    def check_pickaxes(self):
        if self.pickaxe:
            return True
        else:
            log.info("Moving to grab a Pickaxe")
            if self.in_mine:
                self.get_free_pickaxe()
                self.move_mining_spot()  # todo: consider this
                self.mine_direction()
                return self.pickaxe

            self.move_to_unload()
            pickaxe = self.player.find_type(constants.TYPE_ID_TOOL_PICKAXE, MINING_CONTAINER_ID)
            if not pickaxe:
                log.info("WARNING! NO SPARE PICKAXES FOUND!")
                if not GET_FREE_PICKAXE:
                    self.quit()

            log.info("Grabbing a Pickaxe")
            return self.player.grab(pickaxe)

    @alive_action
    def check_bandages(self):
        return self._check_bandages(2, MINING_CONTAINER_ID)

    @alive_action
    def unload(self):
        log.info("Unloading")
        self.move_to_unload()
        self.move_to_unload()
        self.player.unload_types(MINING_LOOT, MINING_CONTAINER_ID)
        self.check_pickaxes()
        self.check_bandages()
        self.rearm_from_container()
        self.eat()

    def go_to_mine_entrance(self):
        self.parse_commands()
        self.wait_stamina()
        self.check_overweight()
        log.info(f"Going to the mine")
        self.check_overweight()
        self.player.move(*MINE_ENTRANCE_COORDS)
        log.info(f"Going to the mine done")
        self.wait_stamina(5)

    @property
    def mining_spots(self):
        if not self._mining_spots:
            log.info(f"Mining spots depleeted. Refreshing.")
            self._mining_spots = copy(MINING_SPOTS)
        return self._mining_spots

    def mining_spot_depleeted(self):
        old_mining_spot = copy(self._mining_spot)
        self._mining_spot = self.mining_spots.pop(0)
        log.info(f"Mining spot {old_mining_spot} depleeted. New mining spot: {self._mining_spot}. "
            f"Spots left: {len(self._mining_spots)}/{len(MINING_SPOTS)}")

    @property
    def mining_spot(self):
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
        log.info(f"{len(self._mining_spots)}/{len(MINING_SPOTS)} {self._mining_spot} {old_direction} depleeted. "
            f"Going: {len(self.directions)}/{len(DIRECTIONS)} {self._direction}.")
        stealth.ClearJournal()

    @property
    def in_mine(self):
        x, _, _, _ = self.player.coords
        mine_entrance_x, _ = MINE_ENTRANCE_COORDS
        return x <= mine_entrance_x

    def pick_up_items(self, **kwargs):
        return super().pick_up_items(MINING_LOOT)

    def engage_mob(self, mob: Mob, *args, **kwargs):
        return super().engage_mob(mob=mob, check_health_func=self.mine_check_health, loot=LOOT_CORPSES, cut=CUT_CORPSES,
                                  drop_trash_items=True, notify_only_mutated=True)

    def check_health(self, **kwargs):
        return super().check_health(resurrect=RESURRECT_AND_RETURN)

    def process_mobs(self, **kwargs):
        return super().process_mobs(engage=ENGAGE_MOBS, notify_only_mutated=True, mob_find_distance=MOB_FIND_DISTANCE,
                                    drop_overweight_items=self.drop_types)

    def mine_check_health(self):
        if self.check_health():
            pass
        else:
            self.player.break_action()
            self.check_overweight()
            self.unload()
            self.check_health()
            self.go_to_mine_entrance()
            # self.get_free_pickaxe()
            self.move_mining_spot()

    def _checks(self, check_overweight=True, loot_corpses=True):
        self.parse_commands()
        self.mine_check_health()
        if check_overweight:
            self.general_weight_check()
        if self.process_mobs():
            self.mining_i = MINE_MAX_ITERATIONS  # force dig again after a mob is killed
        if loot_corpses:
            self.loot_corpses()
        self.check_weapon()
        self.pick_up_items()
        if check_overweight:
            self.drop_trash()
        if self.in_mine:
            self.mine_check_pickaxes()
        if check_overweight:
            self.general_weight_check()

    def move_mining_spot(self):
        self._checks()
        _ = self.direction
        while self.player.xy != self.mining_spot:
            log.info(f"Moving to the next mining spot: {self.mining_spot}")
            self.wait_stamina(5)
            self.player.move(*self.mining_spot, running=self.should_run, accuracy=0)
            self._checks()

    def mine_direction(self):
        while self.player.overweight:  # consider near_max_weight
            self.parse_commands()
            self.drop_trash()
            self.general_weight_check()
            self.check_overweight()
        if SMELT:  # consider near_max_weight
            while self.in_mine and self.player.overweight and self.move_mining_spot() is None and self.got_ore:
                self.smelt()

        self.move_mining_spot()
        stealth.ClearJournal()
        self.player.mine(self.direction)
        self.parse_commands()

    def do_mining(self):
        self.mine_direction()
        self.mining_i = 0
        while True:
            if tools.in_journal(r'skip \d+ spot[s]', regexp=True):
                spots_quantity = tools.in_journal(r'skip \d+ spot[s]', regexp=True, return_re_value=True)
                spots_quantity = int(re.findall(r'\d+', spots_quantity[0])[0])
                log.info(f"Skipping {spots_quantity} spots")
                for i in range(spots_quantity):
                    self.mining_spot_depleeted()
                self._directions = []
                self.mining_i = 0
                self.mine_direction()
                continue
            elif tools.in_journal('skip spot'):
                log.info(f"Skipping spot")
                self._directions = []
                self.mining_i = 0
                self.mine_direction()
                continue
            elif any(_ for _ in MINING_ERRORS if tools.in_journal(_)):
                # self.player._use_cd = pendulum.now()  # todo: tryout
                self.direction_depleeted()
                self.mining_i = 0
                self._checks()
                if self.general_weight_check():
                    self.mining_i = MINE_MAX_ITERATIONS  # force mine direction after smelt or unload
                self.mine_direction()
                continue

            self._checks(check_overweight=False, loot_corpses=False)
            # if self.general_weight_check():
            #     i = MINE_MAX_ITERATIONS  # force mine direction after smelt or unload
            self.mining_i += 1
            if self.mining_i > MINE_MAX_ITERATIONS:
                self.player._use_cd = pendulum.now()
                self.mine_direction()
                self.mining_i = 0

            last_journal_message = stealth.LastJournalMessage()
            log.info(f"{self.mining_i}/{MINE_MAX_ITERATIONS} Waiting for mining to complete: {last_journal_message}")
            stealth.Wait(constants.USE_COOLDOWN)

    @property
    def nearest_forge(self):
        return Item.instantiate(self.player.find_type_ground(constants.TYPE_ID_FORGE, 20))

    def smelt(self):
        if not SMELT:
            return

        forge = self.nearest_forge
        if not forge.exists:
            log.info(f"Cannot smelt. No forge found.")
            return

        self.check_overweight()
        if not self.got_ore:
            return

        log.info(f"Smelting Ore")
        self.wait_stamina()
        self.player.move(*MINE_FORGE_COORDS, accuracy=1)
        self.player.smelt_ore(forge)
        self._checks()

    @property
    def got_ore(self):
        # noinspection PyProtectedMember
        return self.player.got_item_type(constants.TYPE_ID_ORE)

    def drop_overweight_items(self, **kwargs):
        return super().drop_overweight_items(self.drop_types)

    def check_overweight(self, **kwargs):
        return super().check_overweight(drop_types=self.drop_types)

    @alive_action
    @condition(GET_FREE_PICKAXE)
    def get_free_pickaxe(self):
        self.check_overweight()
        self.wait_stamina()
        for container_id, container_coords in FREE_PICKAXE_CONTAINERS.items():
            x, y = container_coords
            container = Container.instantiate(container_id, x=x, y=y, fixed_coords=True)
            log.info(f"Getting free pickaxe from {container}")
            self.player.move_to_object(container, accuracy=1, running=self.should_run)
            self.player.loot_container(container)

    def unload_and_return(self):
        self.unload()
        if not self.in_mine:
            self.go_to_mine_entrance()
            # self.get_free_pickaxe()

    def general_weight_check(self):
        if self.got_ore and self.player.overweight:  # consider near_max_weight
            if self.in_mine:
                self.smelt()
                if self.player.near_max_weight:
                    self.unload()
            else:
                self.unload()
            return True  # to force mine next direction after smelting

    @condition(EQUIP_WEAPONS_FROM_GROUND)
    def check_weapon(self, **kwargs):
        return super().check_weapon(max_weapon_search_distance=MAX_WEAPON_SEARCH_DISTANCE)

    @condition(EQUIP_WEAPONS_FROM_LOOT_CONTAINER)
    def rearm_from_container(self, **kwargs):
        return super().rearm_from_container(container_id=MINING_CONTAINER_ID)

    def start(self):
        # stealth.SetEventProc('evtimer1', self.callback_command_parser)
        log.info(f"Starting {self.scenario_name}")
        self._start_time = pendulum.now()
        dist_to_container = self.player.path_distance_to(*MINING_CONTAINER_COORDS)
        if dist_to_container < 20:
            self.move_to_unload()
            self.unload()

        self.general_weight_check()
        if self.in_mine:
            if not self.pickaxe:
                self.get_free_pickaxe()
        else:
            self.go_to_mine_entrance()
            if not self.pickaxe:
                self.get_free_pickaxe()

        self.do_mining()


if __name__ == '__main__':
    Miner().start()
    print("")
