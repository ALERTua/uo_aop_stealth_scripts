from .base_object import Object
from py_stealth import *

log = AddToSystemJournal


class Creature(Object):
    def __init__(self, _id):
        super().__init__(_id)

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
    def mounted(self):
        return ObjAtLayerEx(HorseLayer(), self._id)

    @property
    def alive(self):
        return self.hp > 0

    @property
    def dead(self):
        return self.hp <= 0
