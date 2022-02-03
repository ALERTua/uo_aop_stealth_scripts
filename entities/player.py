from collections import namedtuple
from collections.abc import Iterable
from copy import copy
from functools import wraps
from typing import List

import pendulum

from entities.base_object import Object
from entities.item import Item
from py_stealth import *
from tools import constants, tools
from .base_creature import Creature
from .base_weapon import WeaponBase
from .container import Container
from tools.tools import log


def alive_action(func):
    @wraps(func)
    def wrapper_alive_action(self, *args, **kwargs):
        if isinstance(self, Player):
            player = self
        else:
            player = self.player

        if player.dead:
            return

        return func(self, *args, **kwargs)

    return wrapper_alive_action


def _cooldown(class_instance, cooldown_field, cooldown, func, *args, **kwargs):
    previous = getattr(class_instance, cooldown_field)
    left = pendulum.now() - previous
    milliseconds_left = left.microseconds / 1000
    time_left = cooldown - milliseconds_left
    if time_left > 0:
        Wait(time_left)

    output = func(class_instance, *args, **kwargs)
    setattr(class_instance, cooldown_field, pendulum.now())
    return output


def skill_cd(func):
    @wraps(func)
    def wrapper_skill_cd(self, *args, **kwargs):
        return _cooldown(self, '_skill_cd', constants.SKILL_COOLDOWN, func, *args, **kwargs)

    return wrapper_skill_cd


def drag_cd(func):
    @wraps(func)
    def wrapper_drag_cd(self, *args, **kwargs):
        return _cooldown(self, '_drag_cd', constants.DRAG_COOLDOWN, func, *args, **kwargs)

    return wrapper_drag_cd


def use_cd(func):
    @wraps(func)
    def wrapper_use_cd(self, *args, **kwargs):
        return _cooldown(self, '_use_cd', constants.USE_COOLDOWN, func, *args, **kwargs)

    return wrapper_use_cd


def bandage_cd(func):
    @wraps(func)
    def wrapper_use_cd(self, *args, **kwargs):
        return _cooldown(self, '_use_cd', constants.BANDAGE_COOLDOWN, func, *args, **kwargs)

    return wrapper_use_cd


def mining_cd(func):
    @wraps(func)
    def wrapper_use_cd(player, *args, **kwargs):
        return _cooldown(player, '_use_cd', constants.MINING_COOLDOWN, func, *args, **kwargs)

    return wrapper_use_cd


# noinspection PyMethodMayBeStatic
class Player(Creature):
    def __init__(self):
        super().__init__(_id=Self(), _direct=False)
        self._skill_cd = pendulum.now()
        self._drag_cd = pendulum.now()
        self._use_cd = pendulum.now()

    @property
    def hp(self):
        return HP()

    @property
    def max_hp(self):
        return MaxHP()

    @property
    def mana(self):
        return Mana()

    @property
    def max_mana(self):
        return MaxMana()

    @property
    def stamina(self):
        return Stam()

    @property
    def max_stamina(self):
        return MaxStam()

    @property
    def hidden(self):
        return Hidden()

    @skill_cd
    def hide(self):
        UseSkill('hiding')

    def hide_until_hidden(self):
        while not self.hidden:
            # noinspection PyArgumentList
            self.hide()

    @property
    def name(self):
        return CharName()

    @property
    def last_target(self):
        return Object.instantiate(LastTarget())

    @property
    def last_object(self):
        return Object.instantiate(LastObject())

    @property
    def last_container(self):
        return Container.instantiate(LastContainer())

    def get_type_id(self, object_id):
        return GetType(object_id)

    @property
    def backpack(self):
        return Container.instantiate(Backpack(), name=f"{self.name}'s Backpack")

    @alive_action
    def equip_weapon_type(self, weapon: WeaponBase):
        return Equipt(weapon.layer, weapon.type_id)

    @drag_cd
    def _use_self(self):
        UseObject(self._id)

    @alive_action
    def dismount(self):
        while self.mounted:
            # noinspection PyArgumentList
            self._use_self()

    @alive_action
    def open_backpack(self):
        return self.use_object(self.backpack)

    def _open_container(self, container):
        container = Container.instantiate(container)
        if self.last_container == container and not container.is_empty:
            return True

        self.use_object(container)
        for _ in range(1):  # double check result
            tools.result_delay()
            if self.last_container == container:
                return True

        return False

    def open_container(self, container, max_tries=10):
        container = Container.instantiate(container)
        if self.last_container == container and not container.is_empty:
            return

        if not container.exists or not container.is_container:
            log.info(f"Cannot open non-container {container}")
            return

        i = 0
        while not self._open_container(container):
            i += 1
            if i >= max_tries:
                log.info(f"Couldn't open {container} after {max_tries} tries")
                return False

        log.debug(f"Successfuly opened {container}")
        tools.result_delay()
        return True

    @alive_action
    def attack(self, target_id):
        target_id = Creature.instantiate(target_id)
        return Attack(target_id.id_)

    @property
    def war_mode(self):
        return WarMode()

    @war_mode.setter
    def war_mode(self, value):
        if self.war_mode != value:
            SetWarMode(value)

    def move_to_object(self, obj, optimized=True, accuracy=1, running=True):
        obj = Object.instantiate(obj)
        return self.move(obj.x, obj.y, optimized=optimized, accuracy=accuracy, running=running)

    def move(self, x, y, optimized=True, accuracy=1, running=True):
        if self.overweight:
            log.info(f"{self} Cannot move: overweight")
            return

        if x <= 0 or y <= 0:
            return

        while self.paralyzed:
            log.info(f"Waiting until unParalyzed")
            tools.result_delay()

        # Xdst, Ydst, Optimized, Accuracy, Running
        return newMoveXY(x, y, optimized, accuracy, running)

    @alive_action
    @drag_cd
    def move_item(self, item_id, quantity=-1, target_id=None, x=0, y=0, z=0, max_tries=10, allow_same_container=False):
        # ItemID, Count, MoveIntoID, X, Y, Z
        item = Item.instantiate(item_id)
        if not item.exists:
            log.info(f"Cannot move nonexistent {item}")
            return

        container = Container.instantiate(target_id) if target_id else self.backpack
        if not container.exists:
            log.info(f"Cannot move {item} to nonexistent {container}")
            return

        if not container.is_container:
            log.info(f"Cannot move {item} to non-container {container}")
            return

        item_container = copy(item.parent)
        if not allow_same_container and item_container == container:
            log.info(f"Not allowed to move {item} within the same {item_container}")
            return

        i = 0
        log.info(f"Moving {quantity}×{item} to {container}.")
        while not (move_result := MoveItem(item.id_, quantity, container.id_, x, y, z)) \
                and item.parent == item_container and (i := i + 1) < max_tries:
            log.info(f".")
            tools.result_delay()
        log.debug(f"done. Moving success: {move_result}")
        return move_result

    @alive_action
    @drag_cd
    def grab(self, item_id, quantity=-1, max_tries=10):
        item = Item.instantiate(item_id)
        item_container = copy(item.parent)
        if quantity == 0:
            log.info(f"Cannot grab quantity {quantity} of {item}")
            return

        if not item.exists:
            log.info(f"Cannot grab {quantity} of nonexisting {item}")
            return

        i = 0
        log.info(f"Grabbing {quantity}×{item}.")
        while not (grab_result := Grab(item.id_, quantity)) and item.parent == item_container \
                and (i := i + 1) < max_tries:
            log.info(f".")
        log.debug(f"done. Grabbing success: {grab_result}")
        return grab_result

    @alive_action
    @drag_cd
    def drop_item(self, item_id, quantity=-1, max_tries=10):
        item = Item.instantiate(item_id)
        item_container = copy(item.parent)
        if quantity == 0:
            log.info(f"Cannot drop quantity {quantity} of {item}")
            return

        if not item.exists:
            log.info(f"Cannot drop {quantity} of nonexisting {item}")
            return

        i = 0
        log.info(f"Dropping {quantity}×{item}")
        while not (drop_result := Drop(item.id_, quantity, 0, 0, 0)) and item.parent == item_container \
                and (i := i + 1) < max_tries:
            log.info(f".")
        log.debug(f"done. Dropping success: {drop_result}")
        return drop_result

    @use_cd
    def use_object(self, obj, announce=True):
        obj = Object.instantiate(obj)
        if obj.id_ in (0, None, -1):
            log.info(f"Cannot use {obj}")
            return

        if not obj.exists:
            log.info(f"Cannot use nonexistent {obj}")
            return

        if announce:
            log.info(f"Using {obj}")
        return UseObject(obj.id_)

    @alive_action
    def use_object_on_object(self, obj, target):
        obj = Object.instantiate(obj)
        target = Object.instantiate(target)
        log.info(f"Using {obj} on {target}")
        CancelWaitTarget()
        self.use_object(obj, announce=False)
        WaitTargetObject(target.id_)

    @alive_action
    def use_object_on_tile(self, obj, tile_type, x, y, z):
        obj = Object.instantiate(obj)
        log.info(f"Using {obj} on tile {tile_type}:({x}, {y}, {z})")
        CancelWaitTarget()
        self.use_object(obj, announce=False)
        WaitTargetTile(tile_type, x, y, z)

    @property
    def max_weight(self):
        return Str() * 3 + 30

    @property
    def near_max_weight_value(self):
        return self.max_weight - 30

    @property
    def weight(self):
        return Weight()

    @property
    def near_max_weight(self):
        return self.weight >= self.near_max_weight_value

    @property
    def overweight(self):
        return self.weight > self.max_weight

    @alive_action
    def unload_types(self, item_types, container_id):
        for unload_type in item_types:
            got_type = FindType(unload_type)
            if got_type:
                log.info(f"Moving {got_type}")
                while got_type := FindType(unload_type):
                    self.move_item(got_type, GetQuantity(got_type), container_id, 0, 0, 0)
                log.info(f"Moving {got_type} Done")

    def say(self, text):
        return UOSay(text)

    @alive_action
    @mining_cd
    def mine(self, direction):
        command = f"'pc mine {direction}"
        log.info(f"Mining {direction}")
        self.say(command)

    @alive_action
    def break_action(self):
        self.war_mode = True
        tools.ping_delay()
        self.war_mode = False

    def find_type(self, type_id, container=None):
        container = Container.instantiate(container)
        return FindType(type_id, container.id_)

    def find_type_ground(self, type_id, distance=2):
        previous_distance = GetFindDistance()
        SetFindDistance(distance)
        output = FindType(type_id, 0)
        SetFindDistance(previous_distance)
        return output

    def find_types_ground(self, type_ids, colors=None, distance=2):
        if not isinstance(type_ids, Iterable):
            type_ids = [type_ids]
        colors = colors or [0xFFFF]
        previous_distance = GetFindDistance()
        SetFindDistance(distance)
        # noinspection PyArgumentList
        output = self.find_types_container(type_ids=type_ids, colors=colors, container_ids=[0])
        SetFindDistance(previous_distance)
        return output

    @alive_action
    def find_types_container(self, type_ids, colors=None, container_ids=None, recursive=False):
        colors = colors or [0xFFFF]
        if not isinstance(container_ids, Iterable):
            container_ids = [container_ids]
        container_ids = container_ids or [self.backpack]
        containers = [Container.instantiate(i) for i in container_ids]
        container_ids = [i.id_ for i in containers]
        FindTypesArrayEx(type_ids, colors, container_ids, recursive)
        output = GetFoundList()
        output = [Item.instantiate(i) for i in output]
        return output

    def find_types_backpack(self, type_ids, colors=None, recursive=False):
        # noinspection PyArgumentList
        return self.find_types_container(type_ids=type_ids, colors=colors, container_ids=[self.backpack],
                                         recursive=recursive)

    @alive_action
    def find_type_backpack(self, type_id, color_id=None, recursive=True):
        color_id = color_id or -1
        return FindTypeEx(type_id, color_id, self.backpack.id_, recursive)

    def got_item_type(self, item_type, color_id=None):
        return self.find_type_backpack(item_type, color_id=color_id)

    def nearest_object_type(self, object_type, distance=None):
        distance = distance or constants.USE_GROUND_RANGE
        return self.find_type_backpack(object_type) or self.find_type_ground(object_type, distance)

    @alive_action
    def smelt_ore(self, forge):
        forge = Item.instantiate(forge)
        if self.distance_to(*forge.xy) > constants.USE_GROUND_RANGE:
            self.move(*forge.xy, accuracy=1)
        for ore_type in [constants.TYPE_ID_ORE, ]:
            while ore := Item.instantiate(self.nearest_object_type(ore_type)):  # todo: break possible infinite loop
                if not ore.exists:
                    break

                ore_quantity_before = copy(ore.quantity)
                if not ore_quantity_before:
                    break

                log.info(f"Smelting {ore}")
                self.use_object_on_object(ore, forge)
                tools.ping_delay()
                ore_quantity_after = copy(ore.quantity)
                if (ore.exists and ore_quantity_after) and ore_quantity_before == ore_quantity_after:
                    log.info(f"Smelt unsuccessful! {ore_quantity_before} x {ore}")
                else:
                    log.debug(f"Smelt successful: {ore_quantity_before} x {ore}")

    @alive_action
    @bandage_cd
    def bandage_self(self):
        if self.hp < self.max_hp:
            cmd = "'pc heal self"
            log.info(f"Healing self with {cmd}")
            self.say(cmd)

    @alive_action
    def bandage_self_if_hurt(self):
        if self.hp < self.max_hp - 60:
            # noinspection PyArgumentList
            return self.bandage_self()

    @property
    def got_bandages(self):
        return self.got_item_type(constants.TYPE_ID_BANDAGE)

    def loot_container(self, container_id, destination_id=None, delay=constants.LOOT_COOLDOWN,
                       use_container_before_looting=True):
        container = Container.instantiate(container_id)
        if not container.is_container:
            log.info(f"Cannot loot container {container}. It is not a container.")
            return False

        destination = Container.instantiate(destination_id) if destination_id else self.backpack
        delay = delay or constants.LOOT_COOLDOWN
        if use_container_before_looting:
            if not self.open_container(container):
                return

        return EmptyContainer(container.id_, destination.id_, delay)

    def move_item_types(self, item_types, source_container=None, destination_container=None, max_quantity=0,
                        items_color=None, x=0, y=0, z=0, delay=None):
        if not isinstance(item_types, Iterable):
            item_types = [item_types]
        items_color = items_color or -1
        source_container = Container.instantiate(source_container) if source_container else self.backpack
        destination_container = destination_container or Ground()
        destination_container = Container.instantiate(destination_container)
        delay = delay or constants.DRAG_COOLDOWN
        for item_type in item_types:
            log.info(f"Moving item type {item_type} from {source_container} to {destination_container}")
            MoveItems(source_container.id_, item_type, items_color, destination_container.id_, x, y, z, delay,
                      max_quantity)

    @alive_action
    def drop_item_types(self, item_types, **kwargs):
        return self.move_item_types(item_types=item_types, **kwargs)

    @alive_action
    def drop_trash_items(self, trash_item_ids=None):
        trash_item_ids = trash_item_ids or constants.ITEM_IDS_TRASH
        trash_items = self.find_types_backpack(trash_item_ids)
        for item in trash_items:
            self.drop_item(item)

    def loot_nearest_corpse(self, corpse_id=None, range_=constants.USE_GROUND_RANGE, cut_corpse=True,
                            drop_trash_items=True, trash_items=None, hide_corpse=True, skip_innocent=True):
        # todo: notoriety check
        range_ = range_ or constants.USE_GROUND_RANGE
        corpse_id = corpse_id or self.find_type_ground(constants.TYPE_ID_CORPSE, range_)
        if not corpse_id:
            return False

        corpse = Container.instantiate(corpse_id)
        if skip_innocent and corpse.innocent:
            log.info(f"Skipping innocent corpse {corpse}")
            return

        if cut_corpse:
            self.move_to_object(corpse)
            self.cut_corpse(corpse_id)
            tools.result_delay()
        self.loot_container(corpse)
        if drop_trash_items:
            # noinspection PyArgumentList
            self.drop_trash_items(trash_item_ids=trash_items)
        if hide_corpse:
            corpse.hide()

    def hide_object(self, obj):
        obj = Object.instantiate(obj)
        return obj.hide()

    def find_types(self, types, container_ids=None, colors=None, recursive=True):
        if not isinstance(types, Iterable):
            types = [types]
        colors = colors or [0xFFFF]
        container_ids = container_ids or [0, RhandLayer(), LhandLayer(), self.backpack.id_]
        FindTypesArrayEx(types, colors, container_ids, recursive)
        output = [Object.instantiate(i) for i in GetFoundList()]
        return output

    @property
    def corpse_cutting_tool(self):
        output = self.find_types(constants.TYPE_IDS_CORPSE_CUT_TOOLS)
        if output:
            return output[0]

    def cut_corpse(self, corpse_or_id, cutting_tool=None):  # todo: notoriety check
        corpse = Container.instantiate(corpse_or_id)  # todo: corpse entity
        cutting_tool = cutting_tool or self.corpse_cutting_tool
        if not cutting_tool:
            log.info(f"Cannot cut corpse {corpse_or_id}. No cutting tool.")
            return

        log.info(f"Cutting {corpse_or_id}")
        self.use_object_on_object(cutting_tool, corpse)

    def path_to_coords(self, x, y, optimized=True, accuracy=1):  # accuracy must be 1 for creatures
        return GetPathArray(x, y, optimized, accuracy)

    def path_distance_to(self, x, y, optimized=True, accuracy=1):  # accuracy must be 1 for creatures
        return len(self.path_to_coords(x, y, optimized=optimized, accuracy=accuracy))

    def get_closest_coords(self, coords, optimized=True, accuracy=1):
        Coords = namedtuple('Coords', ['x', 'y', 'distance'])
        spots = []
        for spot in coords:
            coords = Coords(*spot, self.path_distance_to(*spot, optimized=optimized, accuracy=accuracy))
            spots.append(coords)
        spots = sorted(spots, key=lambda i: i.distance)
        closest_spot = spots[0]
        return closest_spot.x, closest_spot.y

    @property
    def weapon_equipped(self):
        if self.dead:
            return

        layers = (LhandLayer(), RhandLayer())
        weapon_type_ids = constants.TYPE_IDS_WEAPONS
        equipped_weapons = []
        for layer in layers:
            layer_object_id = ObjAtLayer(layer)
            equipped_weapons.append(layer_object_id)
        equipped_types = [GetType(i) for i in equipped_weapons]
        output = any(e for e in equipped_types if e in weapon_type_ids)
        return output

    def equip_object(self, item_or_id, layer):
        if isinstance(item_or_id, Item):
            item_or_id = item_or_id.id_
        return Equip(layer, item_or_id)

    def equip_weapon_id(self, weapon_or_id):
        return self.equip_object(weapon_or_id, RhandLayer())

    def equip_armor_id(self, armor_or_id):
        return self.equip_object(armor_or_id, ShirtLayer())

    def use_type(self, type_id):
        if not type_id:
            return

        return UseType2(type_id)

    def distance_to(self, x, y):
        return Dist(self.x, self.y, x, y)

    def find_creatures(self, distance: int = 20, path_distance: bool = True, creature_types: List[int] = None,
                       notorieties: List[int] or List[constants.Notoriety] = None,
                       condition: callable = None) -> List[Creature]:
        if notorieties and not isinstance(notorieties, Iterable):
            notorieties = [notorieties]
        if creature_types and not isinstance(creature_types, Iterable):
            creature_types = [creature_types]
        previous_distance = GetFindDistance()
        SetFindDistance(distance)
        FindType(-1, 0)
        found = GetFindedList()
        output = [Creature.instantiate(i) for i in found if i]
        SetFindDistance(previous_distance)
        if creature_types:
            output = [i for i in output if i.type_id in creature_types]
        if notorieties:
            output = [i for i in output if i.notoriety in notorieties]
        if path_distance:
            output = [i for i in output if i.path_distance(accuracy=1) <= distance]

        return list(filter(condition, output)) if condition else output

    @property
    def paralyzed(self):
        return Paralyzed()

    @property
    def poisoned(self):
        return Poisoned()


if __name__ == '__main__':
    pass
