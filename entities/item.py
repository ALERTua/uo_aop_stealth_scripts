from py_stealth import *
from .base_object import Object

log = AddToSystemJournal


class Item(Object):
    def __init__(self, _id, **kwargs):
        super().__init__(_id, **kwargs)

    def __str__(self):
        return f"{self.quantity} x [{self.__class__.__name__}]({self._id}){self.name}"

    @property
    def name(self):
        if self._name is None:
            self._name = self._get_name()
            if not self._name:
                ClickOnObject(self._id)
                self._name = self._get_name()
        return self._name

    @property
    def quantity(self):
        return GetQuantity(self._id)


if __name__ == '__main__':
    pass
