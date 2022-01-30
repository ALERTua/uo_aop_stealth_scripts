from enum import Enum, unique
from .constants_weapons import *
from .constants_armor import *
from .constants_gems import *
from .constants_reagents import *
from .constants_food import *
from .constants_scrolls import *
from .constants_colors import *
from .constants_creatures import *


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


@unique
class LineColor(Enum):
    GREY = 946
    INNOCENT = 90
    RED = 38
    SPEECH = 690
    YELLOW = 55
    WHITE = 1153


class JournalLine:
    def __init__(self, journal_id):
        self.journal_id = journal_id
        self.text = Journal(self.journal_id)
        self.color = LineTextColor()
        try:
            self.color = LineColor(self.color)
        except:
            pass
        self.author = LineName()
        self.time = LineTime()
        # self.msg_type = LineMsgType()
        # self.count = LineCount()
        # self.line_id = LineID()
        # self.type = LineType()
        # self.font = LineTextFont()


# RANGES
AGGRO_RANGE = 15
ENGAGE_MAX_DISTANCE = 25
USE_GROUND_RANGE = 3
MAX_PICK_UP_DISTANCE = 3

# COOLDOWNS
SKILL_COOLDOWN = 3100
DRAG_COOLDOWN = 260
USE_COOLDOWN = 3250
MINING_COOLDOWN = 4200
BANDAGE_COOLDOWN = 8000
LOOT_COOLDOWN = 650

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
