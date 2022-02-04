from abc import ABCMeta, abstractmethod
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


class LeftHandWeapon(WeaponBase):
    def layer(self):
        return stealth.LhandLayer()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()


class RightHandWeapon(WeaponBase):
    def layer(self):
        return stealth.RhandLayer()

    @property
    @abstractmethod
    def type_id(self):
        raise NotImplementedError()
