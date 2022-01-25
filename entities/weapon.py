from base_weapon import LeftHandWeapon, RightHandWeapon
from tools import constants
from py_stealth import *

log = AddToSystemJournal


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
