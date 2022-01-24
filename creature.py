from functools import cached_property, wraps

import pendulum

import constants
from py_stealth import *

log = AddToSystemJournal


class Creature:
    def __init__(self, _id):
        self._id = _id

    def __str__(self):
        return f"[{self.__class__.__name__}]({self._id}){self.name}"

    @property
    def id_(self):
        return self._id

    @property
    def exists(self):
        return IsObjectExists(self._id)

    @property
    def name(self):
        return GetName(self._id) or ''

    @property
    def hp(self):
        return GetHP(self._id)

    @property
    def max_hp(self):
        return GetMaxHP(self._id)

    @property
    def stamina(self):
        return GetStam(self._id)

    @property
    def hidden(self):
        return IsHidden(self._id)

    @property
    def coords(self):
        return self.x, self.y, self.z, WorldNum()

    @property
    def x(self):
        return GetX(self._id)

    @property
    def y(self):
        return GetY(self._id)

    @property
    def z(self):
        return GetZ(self._id)

    @property
    def alive(self):
        return self.hp > 0

    @property
    def dead(self):
        return self.hp <= 0
