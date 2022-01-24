from functools import cached_property, wraps

import constants
from creature import Creature
from py_stealth import *

log = AddToSystemJournal


class Mob(Creature):
    def __init__(self, _id):
        super().__init__(_id)

    @property
    def mutated(self):
        return 'mutated' in self.name.lower()
