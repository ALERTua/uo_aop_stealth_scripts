from .base_object import Object, stealth
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
            if self._id != 0 and not self._name:  # clickonobject doesn't work on id 0
                stealth.ClickOnObject(self._id)
                self._name = self._get_name()
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def quantity(self):
        return stealth.GetQuantity(self._id)

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
