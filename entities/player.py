from collections import namedtuple
from collections.abc import Iterable
from functools import wraps
from typing import List

import pendulum

from entities.base_object import Object
from entities.item import Item
from tools import constants, tools
from .base_creature import Creature
from .base_weapon import WeaponBase
from py_stealth import *

log = AddToSystemJournal


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
        super().__init__(_id=Self())
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
        return Object(LastTarget())

    @property
    def last_object(self):
        return Object(LastObject())

    def get_type_id(self, object_id):
        return GetType(object_id)

    @property
    def backpack(self):
        from entities.container import Container  # avoid circular import
        return Container(Backpack())

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

    @alive_action
    def attack(self, target_id):
        return Attack(target_id)

    def move(self, x, y, optimized=True, accuracy=1, running=True):
        if x <= 0 or y <= 0:
            return

        # todo: check frozen
        # Xdst, Ydst, Optimized, Accuracy, Running
        return newMoveXY(x, y, optimized, accuracy, running)

    @alive_action
    @drag_cd
    def move_item(self, item_id, quantity=-1, target_id=None, x=0, y=0, z=0):
        # ItemID, Count, MoveIntoID, X, Y, Z
        target_id = target_id or self.backpack.id_
        target_id = getattr(target_id, 'id_', target_id)
        item_id = getattr(item_id, 'id_', item_id)
        if not IsObjectExists(item_id):
            return

        # if not IsMovable(item_id):
        #     log(f"Cannot move {item_id}. Unmovable")
        #     return

        log(f"Moving {quantity} of {item_id} to {target_id} {x} {y} {z}")
        return MoveItem(item_id, quantity, target_id, x, y, z)

    @alive_action
    @drag_cd
    def grab(self, item_id, quantity=-1):
        if isinstance(item_id, Object):
            item_id = item_id.id_
        if not IsObjectExists(item_id):
            return

        # if not IsMovable(item_id):
        #     log(f"Cannot grab {item_id}. Unmovable")
        #     return

        quantity_str = 'all' if quantity == -1 else quantity
        log(f"Looting {quantity_str} of {item_id}.")
        return Grab(item_id, quantity)

    @alive_action
    @drag_cd
    def drop_item(self, item_id, quantity=-1):
        item_id = getattr(item_id, 'id_', item_id)
        if quantity == 0:
            log(f"cannot drop quantity {quantity} of {item_id}")
            return

        if not IsObjectExists(item_id):
            log(f"cannot drop {quantity} of nonexisting {item_id}")
            return

        x, y, z, _ = self.coords
        log(f"Dropping {quantity} of {item_id}")
        return Drop(item_id, quantity, x, y, z)

    @use_cd
    def use_object(self, object_id):
        object_id = getattr(object_id, 'id_', object_id)
        if object_id in (0, None, -1):
            return

        if not IsObjectExists(object_id):
            return

        log(f"Using {object_id}")
        return UseObject(object_id)

    @property
    def max_weight(self):
        return Str() * 3 + 30 - 1

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
        return self.weight >= self.max_weight

    @alive_action
    def unload_types(self, item_types, container_id):
        for unload_type in item_types:
            got_type = FindType(unload_type)
            if got_type:
                log(f"Moving {got_type}")
                while got_type := FindType(unload_type):
                    self.move_item(got_type, GetQuantity(got_type), container_id, 0, 0, 0)
                log(f"Moving {got_type} Done")

    @property
    def stamina(self):
        return Stam()

    def say(self, text):
        return UOSay(text)

    @alive_action
    @mining_cd
    def mine(self, direction):
        command = f"'pc mine {direction}"
        log(f"Mining {direction}")
        self.say(command)

    @alive_action
    def break_action(self):
        SetWarMode(True)
        Wait(50)
        SetWarMode(False)

    def find_type(self, type_id, container=None):
        return FindType(type_id, container)

    def find_type_ground(self, type_id, distance=2):
        previous_distance = GetFindDistance()
        SetFindDistance(distance)
        output = FindType(type_id, 0)
        SetFindDistance(previous_distance)
        return output

    def find_types_ground(self, type_ids, colors=None, distance=2):
        if not isinstance(type_ids, Iterable):
            type_ids = [type_ids]
        colors = colors or [0]
        previous_distance = GetFindDistance()
        SetFindDistance(distance)
        # noinspection PyArgumentList
        output = self.find_types_container(type_ids=type_ids, colors=colors, container_ids=[0])
        SetFindDistance(previous_distance)
        return output

    @alive_action
    def find_types_container(self, type_ids, colors=None, container_ids=None, recursive=False):
        colors = colors or [0]  # no -1 here
        container_ids = container_ids or [self.backpack]
        if not isinstance(container_ids, (list, tuple)):
            container_ids = [container_ids]
        container_ids = [getattr(i, 'id_', i) for i in container_ids]
        FindTypesArrayEx(type_ids, colors, container_ids, recursive)
        output = GetFoundList()
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
    def smelt_ore(self, forge_id):
        for ore_type in [constants.TYPE_ID_ORE, ]:
            while ore := self.nearest_object_type(ore_type):
                log(f"Smelting {ore}")
                CancelWaitTarget()
                self.use_object(ore)
                WaitTargetObject(forge_id)
                tools.ping_delay()

    @alive_action
    @bandage_cd
    def bandage_self(self):
        if self.hp < self.max_hp:
            self.say("'pc heal self")

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
        if isinstance(container_id, Object):
            container_id = container_id.id_
        if not IsContainer(container_id):
            log(f"Cannot loot container {container_id}. It is not a container.")
            return False

        destination_id = destination_id or self.backpack
        delay = delay or constants.LOOT_COOLDOWN
        if use_container_before_looting:
            self.use_object(container_id)
            tools.ping_delay()

        destination_id = getattr(destination_id, 'id_', destination_id)
        return EmptyContainer(container_id, destination_id, delay)

    def drop_trash_items(self, trash_item_ids=None, recursive=False):
        trash_item_ids = trash_item_ids or constants.ITEM_IDS_TRASH
        for item_id in trash_item_ids:
            while item := self.find_type_backpack(item_id, recursive=recursive):
                if item:
                    self.drop_item(item)

    def loot_nearest_corpse(self, corpse_id=None, range_=constants.USE_GROUND_RANGE, cut_corpse=True,
                            drop_trash_items=True):
        # todo: notoriety check
        range_ = range_ or constants.USE_GROUND_RANGE
        corpse_id = corpse_id or self.find_type_ground(constants.TYPE_ID_CORPSE, range_)
        if not corpse_id:
            return False

        if cut_corpse:
            corpse_obj = Object(corpse_id)
            self.move(corpse_obj.x, corpse_obj.y)
            self.cut_corpse(corpse_id)
        self.loot_container(corpse_id)
        if drop_trash_items:
            self.drop_trash_items()

    def cut_corpse(self, corpse_id):  # todo: notoriety check
        containers = [RhandLayer(), LhandLayer(), self.backpack]
        cut_tool_type_ids = constants.TYPE_IDS_CORPSE_CUT_TOOLS
        cut_tool = None
        break_ = False
        for type_id in cut_tool_type_ids:
            if break_:
                break

            for container_id in containers:
                cut_tool = self.find_type(type_id, container_id)
                if cut_tool:
                    break_ = True
                    break

        if not cut_tool:
            log(f'Cannot cut corpse {corpse_id}. No cutting tool.')
            return

        CancelWaitTarget()
        WaitTargetObject(corpse_id)
        self.use_object(cut_tool)

    def path_to_coords(self, x, y, optimized=True, accuracy=0):
        return GetPathArray(x, y, optimized, accuracy)

    def path_distance_to(self, x, y):
        return len(self.path_to_coords(x, y))

    def get_closest_coords(self, coords):
        Coords = namedtuple('Coords', ['x', 'y', 'distance'])
        spots = []
        for spot in coords:
            coords = Coords(*spot, self.path_distance_to(*spot))
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

    def find_red_creatures(self, distance=20, path_distance: bool = True, condition=None):
        return self.find_creatures(distance=distance, path_distance=path_distance,
                                   notorieties=[constants.Notoriety.Murderer], condition=condition)

    def find_humans(self, distance=20, path_distance: bool = True, condition=None, notorieties=None):
        return self.find_creatures(distance=distance, path_distance=path_distance, condition=condition,
                                   creature_types=[constants.TYPE_ID_HUMAN], notorieties=notorieties)

    def find_red_humans(self, distance=20, path_distance: bool = True, condition=None):
        return self.find_humans(distance=distance, path_distance=path_distance,
                                notorieties=[constants.Notoriety.Murderer], condition=condition)

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
        output = [Creature(i) for i in found if i]
        SetFindDistance(previous_distance)
        if creature_types:
            output = [i for i in output if i.type_ in creature_types]
        if notorieties:
            output = [i for i in output if i.notoriety in notorieties]
        if path_distance:
            output = [i for i in output if i.path_distance(accuracy=1) <= distance]

        return list(filter(condition, output)) if condition else output


if __name__ == '__main__':
    pass
