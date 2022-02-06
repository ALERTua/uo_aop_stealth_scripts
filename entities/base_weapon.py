import re
from abc import ABCMeta, abstractmethod
from functools import cached_property

from entities.item import Item
import py_stealth as stealth


class WeaponBase(Item):
    __metaclass__ = ABCMeta

    def __str__(self):
        return f"[{self.__class__.__name__}]({hex(self._id)}){self.name}"

    @property
    @abstractmethod
    def layer(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()

    @property
    def equipped(self):
        return stealth.GetLayer(self.id_) == self.layer

    @cached_property
    def magic(self):
        magic_patterns = [
            r'.* of .*',
            r'.*magic .*',
        ]
        name = self.name
        for pattern in magic_patterns:
            if re.match(pattern, name, re.I):
                return True

        return False


class LeftHandWeapon(WeaponBase):
    @property
    def layer(self):
        return stealth.LhandLayer()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()


class RightHandWeapon(WeaponBase):
    @property
    def layer(self):
        return stealth.RhandLayer()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()


class GenericWeapon(RightHandWeapon):
    def type_id(self):
        return stealth.GetType(self.id_)
