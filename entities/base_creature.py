from .base_object import Object
from tools import constants
from py_stealth import *

from tools.tools import log


class Creature(Object):
    def __init__(self, _id, **kwargs):
        super().__init__(_id=_id, **kwargs)

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
        return IsObjectExists(self._id) and not IsDead(self._id) and self.hp > 0

    @property
    def dead(self):
        return not IsObjectExists(self._id) or IsDead(self._id) or self.hp <= 0

    @property
    def human(self):
        output = self.type_id in constants.TYPE_IDS_HUMAN \
                 and self.name not in constants.MOB_NAMES \
                 and self.color not in constants.HUMAN_MOB_COLORS
        return output

    @property
    def mount(self):
        return self.type_id in constants.TYPE_IDS_MOUNT

    def path(self, optimized=True, accuracy=1):
        return super().path(optimized=optimized, accuracy=accuracy)

    def path_distance(self, optimized=True, accuracy=1):
        return super().path_distance(optimized=optimized, accuracy=accuracy)
