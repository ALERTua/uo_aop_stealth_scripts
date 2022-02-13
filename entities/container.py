from entities.journal_line import LineColor
from entities.item import Item, stealth
from tools import tools, constants
from tools.tools import log


class Container(Item):
    def __init__(self, _id, **kwargs):
        super().__init__(_id, **kwargs)
        if self._id == 0:
            self.name = 'Ground'

    def __str__(self):
        return f"[{self.__class__.__name__}]({hex(self._id)}){self.name}"

    @property
    def is_empty(self):
        items = stealth.FindType(-1, self._id)
        return not items

    @property
    def corpse_of_self(self):
        return f'corpse of {stealth.CharName()}' in self.name


if __name__ == '__main__':
    container = Container.instantiate('0x4A8F022F')
    empty = container.is_empty
    pass
