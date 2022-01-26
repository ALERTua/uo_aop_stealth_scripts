# MISCS
from enum import Enum

AGGRO_RANGE = 15
ENGAGE_MAX_DISTANCE = 25
USE_GROUND_RANGE = 3

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

# COLORS
COLOR_INGOT_IRON = 0x0961
COLOR_ORE_IRON = 0x0000
COLOR_LOGS_S = 0x0000
COLOR_LOGS = [
    COLOR_LOGS_S,
    0x04C2,
    0x0455,
    0x01CB,
    0x052D,
    0x0482,
    0x0676,
    0x084D,
    0x0750,
    0x0289,
    0x0253,
    0x0590,
    0x0322,
    0x0400,
    0x02C3,
    0x06B7,
    0x0347,
    0x01BF,
]

# COORDS
COORDS_MINOC_HEALER = (2572, 585)
COORDS_MINOC_BANK = (2512, 556)

# TYPE IDS
TYPE_ID_CORPSE = 0x2006
TYPE_ID_HIDE = 0x1078
TYPE_ID_FEATHERS = 0x1BD1

# WEAPONS
TYPE_ID_KRYSS = 0x1400
TYPE_ID_KATANA = 0x13FF
TYPE_ID_HATCHET = 0x0F43
TYPE_ID_SHIELD_KITE = 0x1B74
TYPE_ID_SHIELD_BRONZE = 0x1B72
TYPE_ID_MACE = 0x0F5C
TYPE_ID_CUTLASS = 0x1440
TYPE_ID_BATTLE_AXE = 0x0F47
TYPE_ID_HALBERT = 0x143E
TYPE_ID_CROSSBOW = 0x0F4F

TYPE_IDS_WEAPONS = [
    TYPE_ID_KRYSS,
    TYPE_ID_KATANA,
    TYPE_ID_MACE,
    TYPE_ID_CUTLASS,
    TYPE_ID_BATTLE_AXE,
    TYPE_ID_HALBERT,
    # TYPE_ID_HATCHET,
]
TYPE_IDS_CORPSE_CUT_TOOLS = [  # todo: fill up
    TYPE_ID_HATCHET,
    TYPE_ID_BATTLE_AXE,
    TYPE_ID_CUTLASS,
    TYPE_ID_KATANA,
    TYPE_ID_KRYSS,
    TYPE_ID_HALBERT,
]

# ARMOR
TYPE_ID_CHAIN_COLF = 0x13BB
TYPE_ID_PLATE_GORGET = 0x1413
TYPE_ID_PLATEMAIL = 0x1416

TYPE_IDS_ARMOR_PLATE = [
    TYPE_ID_PLATE_GORGET,
    TYPE_ID_PLATEMAIL,
]
TYPE_IDS_ARMOR_CHAIN = [
    TYPE_ID_CHAIN_COLF,
]
TYPE_IDS_ARMOR = [
    *TYPE_IDS_ARMOR_CHAIN,
    *TYPE_IDS_ARMOR_PLATE,
]

# TILES
TYPE_ID_TILE_FISHING = [
    0x179A,
    0x179B,
    0x179C,
    0x1797,
    0x1799,
]

# FISH
TYPE_ID_FISH = [
    0x09CE,
    0x09CD,
    0x09CC,
]
TYPE_IDS_FISH_TRASH = [
    0x1AE1,
    0x1AE2,
    0x1AE4,
    0x1EA3,
    0x1EA5,
    0x0F7A,  # painting
    0x0FC8,
    0x0FC4,
    TYPE_ID_SHIELD_BRONZE,
]
TYPE_ID_BANDAGE = 0x0E21
TYPE_ID_ORE = 0x19B9
TYPE_ID_INGOT = 0x1BF2
TYPE_ID_LOGS = 0x1BE0
TYPE_ID_FORGE = 0x0FB1
TYPE_ID_FOOD_FISHSTEAKS = 0x097B

TYPE_ID_TOOL_FISHING_POLE = 3519
TYPE_ID_TOOL_PICKAXE = 0x0E85
TYPE_IDS_TOOL = [
    TYPE_ID_TOOL_FISHING_POLE,
    TYPE_ID_TOOL_PICKAXE,
]

# REAGENTS
TYPE_ID_REAGENT_SA = 0x0F8C
TYPE_ID_REAGENT_BP = 0x0F7A
TYPE_ID_REAGENT_GI = 0x0F85
TYPE_ID_REAGENT_BM = 0x0F7B
TYPE_ID_REAGENT_SS = 0x0F8D
TYPE_ID_REAGENT_NS = 0x0F88
TYPE_ID_REAGENT_GA = 0x0F84
TYPE_ID_REAGENT_MR = 0x0F86
TYPE_IDS_REAGENT = [
    TYPE_ID_REAGENT_SA,
    TYPE_ID_REAGENT_BP,
    TYPE_ID_REAGENT_GI,
    TYPE_ID_REAGENT_BM,
    TYPE_ID_REAGENT_SS,
    TYPE_ID_REAGENT_NS,
    TYPE_ID_REAGENT_GA,
    TYPE_ID_REAGENT_MR,
]

TYPE_ID_GOLD = 0x0EED
TYPE_ID_VIAL_OF_BLOOD = 0x0F7D
TYPE_ID_EYE_OF_NEWT = 0x0F87
TYPE_ID_TREASURE_MAP = 0x14EB
TYPE_ID_EMPTY_MAP = 0x14ED
TYPE_ID_BIG_CHEST_1 = 0x0E40
TYPE_ID_BIG_CHEST_3 = 0x0E43

TYPE_ID_ARROWS = 0x0F3F

TYPE_IDS_LOOT = [
    TYPE_ID_GOLD,
    TYPE_ID_FEATHERS,
    TYPE_ID_ARROWS,
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

TYPE_IDS_MINING_LOOT = [
    *TYPE_IDS_LOOT,
    TYPE_ID_INGOT,
    TYPE_ID_ORE,
    TYPE_ID_BANDAGE,
    TYPE_ID_TOOL_PICKAXE,
    TYPE_ID_HIDE,
]

TYPE_IDS_LJ_LOOT = [
    *TYPE_IDS_LOOT,
    # TYPE_ID_BANDAGE,
    # TYPE_ID_HATCHET,
    TYPE_ID_LOGS,
    TYPE_ID_HIDE,
]


# MOBS
TYPE_ID_POISON_ELEM = 0x000D
TYPE_ID_MOB_REAPER = 0x002F
TYPE_ID_MOB_ETIN = 0x0012
TYPE_ID_MOB_SWAMP_TENTACLE = 0x0008
TYPE_ID_MOB_FOREST_SPIDER = 0x001C
TYPE_ID_GIANT_SERPENT = 0x0015
TYPE_ID_SEA_SERPENT = 0x0096
TYPE_ID_MONGBAT = 0x0027
TYPE_ID_HARPY = 0x001E
TYPE_ID_OGRE = 0x0001
TYPE_ID_BLOOD_ELEM = 0x0010

TYPE_IDS_MOB_AGGRESSIVE = [
    TYPE_ID_MOB_REAPER,
    TYPE_ID_MOB_ETIN,
    TYPE_ID_MOB_SWAMP_TENTACLE,
    TYPE_ID_MOB_FOREST_SPIDER,
    TYPE_ID_GIANT_SERPENT,
    TYPE_ID_MONGBAT,
    TYPE_ID_HARPY,
    TYPE_ID_OGRE,
    TYPE_ID_BLOOD_ELEM,
    TYPE_ID_SEA_SERPENT,
    TYPE_ID_POISON_ELEM,
]
TYPE_IDS_MOB_MELEE = [
    TYPE_ID_MOB_SWAMP_TENTACLE,
    TYPE_ID_MOB_FOREST_SPIDER,
    TYPE_ID_GIANT_SERPENT,
    TYPE_ID_MONGBAT,
    TYPE_ID_HARPY,
    TYPE_ID_OGRE,
    TYPE_ID_BLOOD_ELEM,
]
TYPE_IDS_MOB_RANGED = [
    TYPE_ID_MOB_REAPER,
    TYPE_ID_MOB_ETIN,
    TYPE_ID_BLOOD_ELEM,
    TYPE_ID_SEA_SERPENT,
    TYPE_ID_POISON_ELEM,
]

TYPE_ID_EAGLE = 0x0005
TYPE_ID_GREY_WOLF = 0x00E1
TYPE_ID_PANTHER = 0x00D6
TYPE_ID_RABBIT = 0x00CD
TYPE_ID_BLACK_BEAR = 0x00D3
TYPE_ID_WOODPECKER = 0x0006
TYPE_ID_GREAT_HART = 0x00EA
TYPE_ID_HORSE = 0x00E4
TYPE_ID_BLUE_BIRD = 0x0006

TYPE_IDS_CRITTER = [
    TYPE_ID_EAGLE,
    TYPE_ID_GREY_WOLF,
    TYPE_ID_PANTHER,
    TYPE_ID_RABBIT,
    TYPE_ID_BLACK_BEAR,
    TYPE_ID_WOODPECKER,
    TYPE_ID_GREAT_HART,
    TYPE_ID_HORSE,
    TYPE_ID_BLUE_BIRD,
]

# FOOD
TYPE_ID_RAW_RIBS = 0x09F1
TYPE_ID_RAW_LEG_OF_LAMB = 0x1609
TYPE_ID_RAW_BIRD = 0x09B9

TYPE_IDS_RAW_FOOD = [
    TYPE_ID_RAW_RIBS,
    TYPE_ID_RAW_LEG_OF_LAMB,
    TYPE_ID_RAW_BIRD,
]

ITEM_IDS_TRASH = [
    *TYPE_IDS_RAW_FOOD,
    TYPE_ID_MACE,
]


class Notoriety(Enum):
    Unknown = 0x00
    Innocent = 0x01
    Ally = 0x02
    Gray = 0x03
    Criminal = 0x04
    Enemy = 0x05
    Murderer = 0x06
    Invulnerable = 0x07
