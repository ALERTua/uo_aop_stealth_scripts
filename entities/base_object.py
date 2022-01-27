from tools import constants
from py_stealth import *

log = AddToSystemJournal


class Object:
    def __init__(self, _id, color=None):
        self._id = _id
        self._color = color
        self._name = None

    def __eq__(self, other):
        try:
            return self.id_ == other.id_
        except:
            return False

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
        if self._color is None:
            self._color = GetColor(self._id)
        return self._color

    @color.setter
    def color(self, value):
        self._color = value

    @property
    def exists(self):
        return IsObjectExists(self._id)

    def _get_name(self):
        output = GetName(self._id)
        return output or ''

    @property
    def name(self):
        if not self._name:
            self._name = self._get_name() or ''
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
    def xy(self):
        return self.x, self.y

    @property
    def coords(self):
        return self.x, self.y, self.z, WorldNum()

    @property
    def _player_id(self):
        return Self()

    @property
    def player_x(self):
        return GetX(self._player_id)

    @property
    def player_y(self):
        return GetY(self._player_id)

    @property
    def distance(self):
        if self.coords == (0, 0, 0, 0):  # creature coords unknown
            return 99999

        return Dist(self.player_x, self.player_y, self.x, self.y)

    def path(self, optimized=True, accuracy=0):
        output = GetPathArray(self.x, self.y, optimized, accuracy)
        return output

    def path_distance(self, optimized=True, accuracy=0):
        if self.coords == (0, 0, 0, 0):  # creature coords unknown
            return 99999

        output = self.path(optimized=optimized, accuracy=accuracy)
        if len(output) == 0 and self.x != self.player_x and self.y != self.player_y:
            return 99999  # cannot build path to the creature

        return len(output)

    @property
    def notoriety(self) -> constants.Notoriety:
        """
        1 - innocent(blue)
        2 - guilded/ally(green)
        3 - attackable but not criminal(gray)
        4 - criminal(gray)
        5 - enemy(orange)
        6 - murderer(red)
        0,7 - not in use.

        Unknown = 0x00,
        Innocent = 0x01,
        Ally = 0x02,
        Gray = 0x03,
        Criminal = 0x04,
        Enemy = 0x05,
        Murderer = 0x06,
        Invulnerable = 0x07
        """
        notoriety = GetNotoriety(self._id)
        output = constants.Notoriety(notoriety)
        return output

    @property
    def innocent(self):
        return self.notoriety == constants.Notoriety.Innocent

    @property
    def ally(self):
        return self.notoriety == constants.Notoriety.Ally

    @property
    def gray(self):
        return self.notoriety == constants.Notoriety.Gray

    @property
    def criminal(self):
        return self.notoriety == constants.Notoriety.Criminal

    @property
    def enemy(self):
        return self.notoriety == constants.Notoriety.Enemy

    @property
    def murderer(self):
        return self.notoriety == constants.Notoriety.Murderer

    @property
    def invulnerable(self):
        return self.notoriety == constants.Notoriety.Invulnerable
