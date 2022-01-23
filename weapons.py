from abc import ABCMeta, abstractmethod
from py_stealth import *
import constants
log = AddToSystemJournal


class WeaponBase:
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def layer(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()


class LeftHandWeapon(WeaponBase):
    def layer(self):
        return LhandLayer()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()


class RightHandWeapon(WeaponBase):
    def layer(self):
        return RhandLayer()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()


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
