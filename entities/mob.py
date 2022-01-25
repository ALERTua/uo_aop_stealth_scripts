from tools import constants
from entities.base_creature import Creature
from py_stealth import *

log = AddToSystemJournal


class Mob(Creature):
    def __init__(self, _id):
        super().__init__(_id)

    @property
    def mutated(self):
        return 'mutated' in self.name.lower()

    @property
    def in_aggro_range(self):
        return self.distance <= constants.AGGRO_RANGE
