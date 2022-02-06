from .base_object import Object, stealth
import py_stealth as stealth
from tools.tools import log


class Item(Object):
    def __init__(self, _id, weight=None, **kwargs):
        super().__init__(_id, **kwargs)
        self.weight_one = weight

    def __str__(self):
        return f"[{self.__class__.__name__}]({hex(self._id)}){self.quantity}×{self.name}"

    @property
    def name(self):
        if self._name is None:
            self._name = self._get_name()
            if not self._name and self._id not in (0, stealth.RhandLayer(), stealth.LhandLayer()):
                # clickonobject doesn't work on id 0
                stealth.ClickOnObject(self._id)
                self._name = self._get_name()
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def name_short(self):
        name = self.name
        if not name:
            return self._id

        short_name = name.split(':')[0].strip()
        return short_name

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


if __name__ == '__main__':
    pass
