from entities.item import Item
from tools import constants
from py_stealth import *
from .base_object import Object

log = AddToSystemJournal


class Container(Object):
    def __init__(self, _id, **kwargs):
        super().__init__(_id, **kwargs)

    @property
    def is_empty(self):
        items = FindType(-1, self._id)
        return not items

    @property
    def is_container(self):
        return IsContainer(self._id)


if __name__ == '__main__':
    container = Container.instantiate('0x4A8F022F')
    empty = container.is_empty
    pass
