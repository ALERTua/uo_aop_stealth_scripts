from tools import constants, tools
import py_stealth as stealth
from tools.tools import log


class Object:
    cache = {}

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

    def __hash__(self):
        return self._id

    def __eq__(self, other):
        try:
            return self.id_ == other.id_
        except:
            return False

    def __str__(self):
        return f"[{self.__class__.__name__}]({self.type_id}:{hex(self._id)}){self.name}"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def _get_cached(cls, id_, omit_cache=False, *args, **kwargs):
        if not omit_cache and id_ in cls.cache.keys() and cls.cache[id_].__class__ == cls:
            output = cls.cache[id_]
            # log.debug(f"Returning cached {output}")
        else:
            output = cls.__new__(cls)
            output.__init__(id_, _direct=False, *args, **kwargs)
            cls.cache[id_] = output
            # log.debug(f"Creating {output}")
        return output

    @classmethod
    def instantiate(cls, obj, omit_cache=False, force_class=False, *args, **kwargs):
        if isinstance(obj, (cls, *cls.__subclasses__())):
            return obj

        cls_ = cls
        id_ = obj
        if isinstance(obj, Object):
            id_ = obj.id_
        type_id = stealth.GetType(id_)
        if type_id and not force_class:
            if type_id in constants.TYPE_IDS_CONTAINER or stealth.IsContainer(id_):
                from entities.container import Container
                cls_ = Container
            elif type_id in constants.TYPE_IDS_WEAPONS:
                from entities.base_weapon import Weapon
                cls_ = Weapon
            elif type_id in constants.TYPE_IDS_CREATURE:
                from entities.base_creature import Creature
                cls_ = Creature

        return cls_._get_cached(id_, omit_cache=omit_cache, *args, **kwargs)

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
        return all((stealth.IsObjectExists(self._id), self.type_id))

    def _get_name(self):
        output = stealth.GetName(self._id)
        return output or ''

    def _get_click_info(self):
        journal_start = stealth.HighJournal() + 1
        stealth.ClickOnObject(self._id)
        journal = tools.journal(start_index=journal_start)
        journal_filtered = [i for i in journal if 'You see: ' in i.text]
        for i in journal_filtered:
            i.text = i.text.replace('You see: ', '')
        return journal_filtered

    @property
    def name(self):
        if self._name is None:
            self._name = self._get_name()
            if not self._name and self._id not in (0, stealth.RhandLayer(), stealth.LhandLayer()):
                # clickonobject doesn't work on id 0
                stealth.ClickOnObject(self._id)
                self._name = self._get_name()
            if self.name.startswith('[') and self.name.endswith(']'):
                self._name = " ".join([i.text for i in self._get_click_info()])
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def short_name(self):
        return self.name_short

    @property
    def name_short(self):
        name = self.name
        if not name:
            return self._id

        short_name = name.split(':')[0].strip()
        short_name = short_name.lstrip('a').strip()
        short_name = short_name.split('made by')[0].strip()
        if short_name.endswith('s'):
            pre_s_character = short_name[-2]
            if tools.is_latin(pre_s_character):
                if pre_s_character == 's':  # two 's' at the end
                    short_name = short_name[:-1]
                else:  # one 's' at the end
                    pass
            else:  # russian letter before the last 's'
                short_name = short_name[:-1]
        return short_name

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
    def xyz(self):
        return self.x, self.y, self.z

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

        output = stealth.Dist(self.player_x, self.player_y, self.x, self.y)
        return output

    def path(self, optimized=True, accuracy=0):
        output = stealth.GetPathArray(self.x, self.y, optimized, accuracy)
        return output

    def path_distance(self, optimized=True, accuracy=0):
        if not self.exists:
            return -1  # todo: consider this

        if self.exists and self.coords == (0, 0, 0, 0):  # creature coords unknown
            return 99999

        output = self.path(optimized=optimized, accuracy=accuracy)
        if self.exists and len(output) == 0 and (self.x != self.player_x or self.y != self.player_y):
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

    @property
    def quantity(self):
        return stealth.GetQuantity(self.id_)
