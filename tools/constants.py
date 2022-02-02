from enum import Enum, unique
# noinspection PyUnresolvedReferences
from .constants_armor import *
# noinspection PyUnresolvedReferences
from .constants_colors import *
# noinspection PyUnresolvedReferences
from .constants_creatures import *
# noinspection PyUnresolvedReferences
from .constants_food import *
# noinspection PyUnresolvedReferences
from .constants_gems import *
# noinspection PyUnresolvedReferences
from .constants_reagents import *
# noinspection PyUnresolvedReferences
from .constants_scrolls import *
# noinspection PyUnresolvedReferences
from .constants_weapons import *
from . import tools


@unique
class Notoriety(Enum):
    Unknown = 0x00
    Innocent = 0x01
    Ally = 0x02
    Gray = 0x03
    Criminal = 0x04
    Enemy = 0x05
    Murderer = 0x06
    Invulnerable = 0x07
    Player = 65


# RANGES
AGGRO_RANGE = 15
ENGAGE_MAX_DISTANCE = 25
USE_GROUND_RANGE = 3
MAX_PICK_UP_DISTANCE = 3

# COOLDOWNS
SKILL_COOLDOWN = 3000 + tools.server_ping_average()
DRAG_COOLDOWN = 250 + tools.server_ping_average()
USE_COOLDOWN = 3000 + tools.server_ping_average()
MINING_COOLDOWN = USE_COOLDOWN
BANDAGE_COOLDOWN = 8000 + tools.server_ping_average()
LOOT_COOLDOWN = DRAG_COOLDOWN

# WEIGHTS
WEIGHT_ORE = 12
WEIGHT_LOGS = 2
WEIGHT_INGOT = 1

# COORDS
COORDS_MINOC_HEALER = (2572, 585)
COORDS_MINOC_BANK = (2512, 556)

# TYPE IDS
TYPE_ID_CORPSE = 0x2006
TYPE_ID_HIDE = 0x1078
TYPE_ID_FEATHERS = 0x1BD1
TYPE_ID_RUNE = 0x1F14

# FISHING
TYPE_ID_TILE_FISHING = [
    0x179A,
    0x179B,
    0x179C,
    0x1797,
    0x1799,
]

TYPE_ID_FISH = [
    0x09CE,
    0x09CD,
    0x09CC,
]

# CRAFT
TYPE_ID_BANDAGE = 0x0E21
TYPE_ID_ORE = 0x19B9
TYPE_ID_INGOT = 0x1BF2
TYPE_ID_LOGS = 0x1BE0
TYPE_ID_FORGE = 0x0FB1


# TOOLS
TYPE_ID_TOOL_FISHING_POLE = 3519
TYPE_ID_TOOL_PICKAXE = 0x0E85
TYPE_IDS_TOOL = [
    TYPE_ID_TOOL_FISHING_POLE,
    TYPE_ID_TOOL_PICKAXE,
]


# TREASURES
TYPE_ID_GOLD = 0x0EED
TYPE_ID_TREASURE_MAP = 0x14EB
TYPE_ID_EMPTY_MAP = 0x14ED
TYPE_ID_BIG_CHEST_1 = 0x0E40
TYPE_ID_BIG_CHEST_3 = 0x0E43


# AMMO
TYPE_ID_ARROWS = 0x0F3F
TYPE_ID_BOLTS = 0x1BFB


# LOOT
TYPE_IDS_LOOT = [
    TYPE_ID_GOLD,
    TYPE_ID_FEATHERS,
    TYPE_ID_ARROWS,
    TYPE_ID_BOLTS,
    TYPE_ID_VIAL_OF_BLOOD,
    TYPE_ID_EYE_OF_NEWT,
    TYPE_ID_TREASURE_MAP,
    TYPE_ID_BIG_CHEST_1,
    TYPE_ID_BIG_CHEST_3,
    TYPE_ID_EMPTY_MAP,
    *TYPE_IDS_WEAPONS,
    *TYPE_IDS_ARMOR,
    *TYPE_IDS_REAGENT,
]

ITEM_IDS_TRASH = [
    *TYPE_ID_GEMS,
    *TYPE_IDS_RAW_FOOD,
]


if __name__ == '__main__':
    pass
