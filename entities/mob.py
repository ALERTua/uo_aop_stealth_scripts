from .base_creature import Creature
from tools import constants
from py_stealth import *

log = AddToSystemJournal


class Mob(Creature):
    def __init__(self, _id, path_distance=99999):
        super().__init__(_id)
        self._path_distance = path_distance

    @property
    def mutated(self):
        return 'mutated' in self.name.lower()

    @property
    def in_aggro_range(self):
        return self.distance <= constants.AGGRO_RANGE
