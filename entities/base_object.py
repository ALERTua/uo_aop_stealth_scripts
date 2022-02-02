from tools import constants
import py_stealth as stealth
from tools.tools import log


class Object:
    def __init__(self, _id, type_id=None, color=None, name=None, path_distance=99999, x=None, y=None, z=None,
                 fixed_coords=False, _direct=True):
        assert _direct is False, "Please use .instantiate classmethod"
        self._id = _id
        self._type_id = type_id
        self._color = color
        self._name = name
        self._path_distance = path_distance
        self._x = x
        self._y = y
        self._z = z
        self.fixed_coords = fixed_coords

    def __eq__(self, other):
        try:
            output = (type(self) == type(other)) and (self.id_ == other.id_)
            return output
        except:
            return False

    def __str__(self):
        return f"[{self.__class__.__name__}]({hex(self._id)}){self.name}"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def instantiate(cls, obj, *args, **kwargs):
        if isinstance(obj, (cls, *cls.__subclasses__())):
            return obj

        if isinstance(obj, Object):  # todo: not perfect
            return cls(obj._id, _direct=False, *args, **kwargs)

        return cls(obj, _direct=False, *args, **kwargs)

    @property
    def id_(self):
        return self._id

    @property
    def type_id(self):
        if self._type_id is None:
            self._type_id = stealth.GetType(self._id)
            if self._type_id == 0:
                self._type_id = None
        return self._type_id

    @property
    def color(self):
        if self._color is None:
            self._color = stealth.GetColor(self._id)
        return self._color

    @color.setter
    def color(self, value):
        self._color = value

    @property
    def parent(self):
        parent = stealth.GetParent(self.id_)
        if parent:
            from entities.container import Container  # avoid cyclic import
            return Container.instantiate(parent)

    @property
    def exists(self):
        return stealth.IsObjectExists(self._id) and self.type_id

    def _get_name(self):
        output = stealth.GetName(self._id)
        return output or ''

    @property
    def name(self):
        if not self._name:
            self._name = self._get_name() or ''
        return self._name

    @property
    def x(self):
        if self.fixed_coords:
            return self._x

        return stealth.GetX(self._id)

    @property
    def y(self):
        if self.fixed_coords:
            return self._y

        return stealth.GetY(self._id)

    @property
    def z(self):
        if self.fixed_coords:
            return self._z

        return stealth.GetZ(self._id)

    @property
    def xy(self):
        return self.x, self.y

    @property
    def coords(self):
        return self.x, self.y, self.z, stealth.WorldNum()

    @property
    def _player_id(self):
        return stealth.Self()

    @property
    def player_x(self):
        return stealth.GetX(self._player_id)

    @property
    def player_y(self):
        return stealth.GetY(self._player_id)

    @property
    def distance(self):
        if self.coords == (0, 0, 0, 0):  # creature coords unknown
            return 99999

        return stealth.Dist(self.player_x, self.player_y, self.x, self.y)

    def path(self, optimized=True, accuracy=0):
        output = stealth.GetPathArray(self.x, self.y, optimized, accuracy)
        return output

    def path_distance(self, optimized=True, accuracy=0):
        if not self.exists:
            return -1  # todo: consider this

        if self.exists and self.coords == (0, 0, 0, 0):  # creature coords unknown
            return 99999

        output = self.path(optimized=optimized, accuracy=accuracy)
        if self.exists and len(output) == 0 and self.x != self.player_x and self.y != self.player_y:
            return 99999  # cannot build path to the creature

        self._path_distance = len(output)
        return self._path_distance

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
        notoriety = stealth.GetNotoriety(self._id)
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

    def hide(self):
        return stealth.ClientHide(self.id_)  # never gets the result and hangs forever
