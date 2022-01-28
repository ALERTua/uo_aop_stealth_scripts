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
    def mana(self):
        return GetMana(self._id)

    @property
    def max_mana(self):
        return GetMaxMana(self._id)

    @property
    def stamina(self):
        return GetStam(self._id)

    @property
    def max_stamina(self):
        return GetMaxStam(self._id)

    @property
    def paralyzed(self):
        return IsParalyzed(self._id)

    @property
    def poisoned(self):
        return IsPoisoned(self._id)

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
