from entities.item import Item
from py_stealth import *

log = AddToSystemJournal


class Container(Item):
    def __init__(self, _id, **kwargs):
        super().__init__(_id, **kwargs)

    def __str__(self):
        return f"[{self.__class__.__name__}]({hex(self._id)}){self.name}"

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
