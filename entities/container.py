from entities.item import Item
from entities.player import alive_action
from tools import constants
from py_stealth import *
from .base_object import Object

log = AddToSystemJournal


class Container(Object):
    def __init__(self, _id):
        super().__init__(_id)

    @property
    def is_empty(self):
        items = FindType(-1, self._id)
        return not items

    @alive_action
    def open(self, force=False):
        if force or self.is_empty:
            return UseObject(self._id)

    @alive_action
    def put_item(self, item_or_id, quantity, x=0, y=0, z=0):  # todo: delay
        if isinstance(item_or_id, Item):
            item_or_id = item_or_id.id_
        return MoveItem(item_or_id, quantity, self._id, x, y, z)

    @alive_action
    def loot_all(self, destination_or_id=None, delay=constants.DRAG_COOLDOWN):
        if isinstance(destination_or_id, Container):
            destination_or_id = destination_or_id.id_
        return EmptyContainer(self._id, destination_or_id, delay)

    @alive_action
    def find_type(self, type_id, color_id=None, recursive=True):
        color_id = color_id or -1
        return FindTypeEx(type_id, color_id, self.id_, recursive)


if __name__ == '__main__':
    container = Container('0x4A8F022F')
    empty = container.is_empty
    pass
