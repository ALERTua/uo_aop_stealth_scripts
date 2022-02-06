from .base_weapon import LeftHandWeapon, RightHandWeapon
from tools import constants
import py_stealth as stealth
from tools.tools import log


class Katana(RightHandWeapon):
    @property
    def type_id(self):
        return constants.TYPE_ID_KATANA


class Pickaxe(RightHandWeapon):
    @property
    def type_id(self):
        return constants.TYPE_ID_TOOL_PICKAXE


class ShieldKite(LeftHandWeapon):
    @property
    def type_id(self):
        return constants.TYPE_ID_SHIELD_KITE


class FishingPole(LeftHandWeapon):
    @property
    def type_id(self):
        return constants.TYPE_ID_TOOL_FISHING_POLE


class Hatchet(RightHandWeapon):
    @property
    def type_id(self):
        return constants.TYPE_ID_HATCHET

