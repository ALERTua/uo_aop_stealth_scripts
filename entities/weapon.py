from .base_weapon import LeftHandWeapon, RightHandWeapon
from tools import constants
import py_stealth as stealth
from tools.tools import log


class Katana(RightHandWeapon):
    def type_id(self):
        return constants.TYPE_ID_KATANA


class Pickaxe(RightHandWeapon):
    def type_id(self):
        return constants.TYPE_ID_TOOL_PICKAXE


class ShieldKite(LeftHandWeapon):
    def type_id(self):
        return constants.TYPE_ID_SHIELD_KITE


class FishingPole(LeftHandWeapon):
    def type_id(self):
        return constants.TYPE_ID_TOOL_FISHING_POLE


class Hatchet(RightHandWeapon):
    def type_id(self):
        return constants.TYPE_ID_HATCHET

