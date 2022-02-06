# ARMOR
TYPE_ID_HELMET = 0x140A
TYPE_ID_NOSE_HELM = 0x140E
TYPE_ID_CLOSE_HELM = 0x1408

# BONE
TYPE_ID_BONE_GLOVES = 0x1450
TYPE_ID_BONE_ARMS = 0x144E
TYPE_ID_BONE_CHEST = 0x144F
TYPE_ID_BONE_LEGS = 0x1452
TYPE_ID_BONE_HELM = 0x1451

TYPE_IDS_ARMOR_BONE = [
    TYPE_ID_BONE_GLOVES,
    TYPE_ID_BONE_ARMS,
    TYPE_ID_BONE_CHEST,
    TYPE_ID_BONE_LEGS,
    TYPE_ID_BONE_HELM,
]


# PLATE
TYPE_ID_PLATE_GORGET = 0x1413
TYPE_ID_PLATEMAIL = 0x1416
TYPE_ID_PLATE_GLOVES = 0x1414
TYPE_ID_PLATE_SLEEVES = 0x1410
TYPE_ID_PLATE_LEGGINGS = 0x141A
TYPE_ID_PLATE_HELM = 0x1412

TYPE_IDS_ARMOR_PLATE = [
    TYPE_ID_PLATE_GORGET,
    TYPE_ID_PLATEMAIL,
    TYPE_ID_PLATE_GLOVES,
    TYPE_ID_PLATE_SLEEVES,
    TYPE_ID_PLATE_LEGGINGS,
    TYPE_ID_PLATE_HELM,
]


# CHAIN
TYPE_ID_CHAIN_COLF = 0x13BB
TYPE_ID_CHAIN_TUNIC = 0x13C4
TYPE_ID_CHAIN_LEGGINGS = 0x13C3


TYPE_IDS_ARMOR_CHAIN = [
    TYPE_ID_CHAIN_COLF,
    TYPE_ID_CHAIN_TUNIC,
    TYPE_ID_CHAIN_LEGGINGS,
]


# LEATHER
TYPE_ID_ARMOR_LEATHER_BUSTIER = 0x1C0A
TYPE_ID_ARMOR_LEATHER_SKIRT = 0x1C08

TYPE_ID_ARMOR_LEATHER = [
    TYPE_ID_ARMOR_LEATHER_BUSTIER,
    TYPE_ID_ARMOR_LEATHER_SKIRT,
]
TYPE_IDS_ARMOR = [
    TYPE_ID_HELMET,
    TYPE_ID_NOSE_HELM,
    TYPE_ID_CLOSE_HELM,
    *TYPE_IDS_ARMOR_CHAIN,
    *TYPE_IDS_ARMOR_PLATE,
    *TYPE_IDS_ARMOR_BONE,
]