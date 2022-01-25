from py_stealth import *

log = AddToSystemJournal


class Object:
    def __init__(self, _id):
        self._id = _id
        self._name = None

    def __str__(self):
        return f"[{self.__class__.__name__}]({self._id}){self.name}"

    @property
    def id_(self):
        return self._id

    @property
    def type_(self):
        return GetType(self._id)

    @property
    def color(self):
        return GetColor(self._id)

    @property
    def exists(self):
        return IsObjectExists(self._id)

    def _get_name(self):
        output = GetName(self._id)
        return output or ''

    @property
    def name(self):
        if self._name is None:
            name = self._get_name()
            if name:
                self._name = name
        return self._name

    @property
    def x(self):
        return GetX(self._id)

    @property
    def y(self):
        return GetY(self._id)

    @property
    def z(self):
        return GetZ(self._id)

    @property
    def coords(self):
        return self.x, self.y, self.z, WorldNum()

    @property
    def distance(self):
        player_id = Self()
        player_x = GetX(player_id)
        player_y = GetY(player_id)
        return Dist(player_x, player_y, self.x, self.y)

    def path(self, optimized=True, accuracy=0):
        return GetPathArray(self.x, self.y, optimized, accuracy)

    def path_distance(self, optimized=True, accuracy=0):
        return len(self.path(optimized=optimized, accuracy=accuracy))
