from functools import cached_property, wraps

import pendulum

import constants
from creature import Creature
from py_stealth import *
from weapons import WeaponBase

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
    def wrapper_skill_cd(player, *args, **kwargs):
        return _cooldown(player, '_skill_cd', constants.SKILL_COOLDOWN, func, *args, **kwargs)

    return wrapper_skill_cd


def drag_cd(func):
    @wraps(func)
    def wrapper_drag_cd(player, *args, **kwargs):
        return _cooldown(player, '_drag_cd', constants.DRAG_COOLDOWN, func, *args, **kwargs)

    return wrapper_drag_cd


def use_cd(func):
    @wraps(func)
    def wrapper_use_cd(player, *args, **kwargs):
        return _cooldown(player, '_use_cd', constants.USE_COOLDOWN, func, *args, **kwargs)

    return wrapper_use_cd


def bandage_cd(func):
    @wraps(func)
    def wrapper_use_cd(player, *args, **kwargs):
        return _cooldown(player, '_use_cd', constants.BANDAGE_COOLDOWN, func, *args, **kwargs)

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
        return LastTarget()

    def get_type_id(self, object_id):
        return GetType(object_id)

    @property
    def backpack(self):
        return Backpack()

    @alive_action
    def equip_weapon_type(self, weapon: WeaponBase):
        return Equipt(weapon.layer, weapon.type_id)

    @property
    def mounted(self):
        return ObjAtLayerEx(HorseLayer(), self._id)

    @drag_cd
    def _use_self(self):
        UseObject(self._id)

    @alive_action
    def dismount(self):
        while self.mounted:
            # noinspection PyArgumentList
            self._use_self()

    def move(self, x, y, optimized=True, accuracy=1, running=True):
        if x <= 0 or y <= 0:
            return

        # Xdst, Ydst, Optimized, Accuracy, Running
        return newMoveXY(x, y, optimized, accuracy, running)

    @alive_action
    @drag_cd
    def move_item(self, item_id, quantity=-1, target_id=None, x=0, y=0, z=0):
        # ItemID, Count, MoveIntoID, X, Y, Z
        target_id = target_id or self.backpack
        log(f"Moving {quantity} of {item_id} to {target_id} {x} {y} {z}")
        return MoveItem(item_id, quantity, target_id, x, y, z)

    @alive_action
    @drag_cd
    def loot_ground(self, item_id, quantity=-1):
        log(f"Looting {quantity} of {item_id} from ground.")
        return Grab(item_id, quantity)

    @alive_action
    @drag_cd
    def drop_item(self, item_id, quantity=-1):
        if quantity == 0:
            return

        x, y, z, _ = self.coords
        log(f"Dropping {quantity} of {item_id}")
        return Drop(item_id, quantity, x, y, z)

    @use_cd
    def use_object(self, object_id):
        if object_id == 0:
            return

        log(f"Using {object_id}")
        return UseObject(object_id)

    @alive_action
    def backpack_find_type(self, type_id, color_id=-1, recursive=True):
        return FindTypeEx(type_id, color_id, self.backpack, recursive)

    @alive_action
    def _got_item_type(self, item_type):
        return self.backpack_find_type(item_type)

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
                while got_type:
                    self.move_item(got_type, GetQuantity(got_type), container_id, 0, 0, 0)
                    got_type = FindType(unload_type)
                log(f"Moving {got_type} Done")

    def _nearest_ore(self, ore_type):
        return self.backpack_find_type(ore_type) or self.find_type_ground(ore_type, 3)

    @alive_action
    def smelt_ore(self, forge_id):
        for ore_type in [constants.TYPE_ID_ORE, ]:
            ore = self._nearest_ore(ore_type)
            while ore:
                log(f"Smelting {ore}")
                self.use_object(ore)
                WaitTargetObject(forge_id)
                Wait(500)
                ore = self._nearest_ore(ore_type)

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
        colors = colors or [0]
        previous_distance = GetFindDistance()
        SetFindDistance(distance)
        FindTypesArrayEx(type_ids, colors, [0], False)
        output = GetFoundList()
        SetFindDistance(previous_distance)
        return output

    @alive_action
    @bandage_cd
    def bandage_self(self):
        if self.hp < self.max_hp:
            self.say("'pc heal self")

    def bandage_self_if_hurt(self):
        if self.hp < self.max_hp - 50:
            return self.bandage_self()

    @property
    def got_bandages(self):
        return self._got_item_type(constants.TYPE_ID_BANDAGE)


if __name__ == '__main__':
    pass
