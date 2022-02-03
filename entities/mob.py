from .base_creature import Creature
from tools import constants
from tools.tools import log


class Mob(Creature):
    def __init__(self, _id, **kwargs):
        super().__init__(_id, **kwargs)

    @property
    def mutated(self):
        return 'mutated' in self.name.lower()

    @property
    def in_aggro_range(self):
        return self.distance <= constants.AGGRO_RANGE
