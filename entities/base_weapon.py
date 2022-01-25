from abc import ABCMeta, abstractmethod

from py_stealth import *


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