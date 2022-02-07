from entities.journal_line import LineColor
from .base_object import Object, stealth
from tools import constants, tools
from tools.tools import log


class Item(Object):
    def __init__(self, _id, weight=None, **kwargs):
        super().__init__(_id, **kwargs)
        self.weight_one = weight

    def __str__(self):
        return f"[{self.__class__.__name__}]({hex(self._id)}){self.quantity}×{self.name}"

    @property
    def total_weight(self):
        if not self.weight_one:
            log.info(f"Cannot get {self} total weight. Weight of one is unknown")
            return

        return self.quantity * self.weight_one

    @property
    def movable(self):  # Only returns value for the items on the ground. Otherwise always returns False
        if self.parent == stealth.Ground():
            return stealth.IsMovable(self.id_)

        return True

    @property
    def is_container(self):
        return stealth.IsContainer(self._id)

    @property
    def innocent(self):
        return any(i for i in self._get_click_info() if i.color == LineColor.INNOCENT)

    @property
    def locked(self):
        return any(i for i in self._get_click_info()
                   if i.color == LineColor.WHITE
                   and 'locked down' in i.text.lower())

    @property
    def secure(self):
        return any(i for i in self._get_click_info()
                   if i.color == LineColor.WHITE
                   and 'secure' in i.text.lower())


if __name__ == '__main__':
    pass
