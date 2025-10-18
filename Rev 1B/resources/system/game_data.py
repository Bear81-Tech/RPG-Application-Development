# game_data.py

# ---------- Core Class Data ----------

bab_progressions = {
    "Artificer": 0.75, "Barbarian": 1.0, "Bard": 0.75, "Cleric": 0.75, "Druid": 0.75,
    "Fighter": 1.0, "Gunslinger": 1.0, "Monk": 0.75, "Paladin": 1.0, "Ranger": 1.0,
    "Rogue": 0.75, "Sorcerer": 0.5, "Wizard": 0.5
}

stat_priority = {
    "Fighter": ["STR", "CON", "DEX", "WIS", "CHA", "INT"],
    "Barbarian": ["STR", "CON", "DEX", "WIS", "CHA", "INT"],
    "Paladin": ["CHA", "STR", "CON", "DEX", "WIS", "INT"],
    "Ranger": ["DEX", "CHA", "CON", "STR", "WIS", "INT"],
    "Rogue": ["DEX", "INT", "CHA", "STR", "CON", "WIS"],
    "Bard": ["CHA", "DEX", "INT", "WIS", "CON", "STR"],
    "Cleric": ["WIS", "STR", "CON", "DEX", "CHA", "INT"],
    "Druid": ["WIS", "CON", "DEX", "INT", "CHA", "STR"],
    "Monk": ["DEX", "WIS", "STR", "CON", "INT", "CHA"],
    "Wizard": ["INT", "CON", "DEX", "WIS", "CHA", "STR"],
    "Sorcerer": ["CHA", "DEX", "WIS", "CON", "INT", "STR"],
    "Artificer": ["INT", "DEX", "WIS", "CON", "CHA", "STR"],
    "Gunslinger": ["DEX", "STR", "CON", "WIS", "CHA", "INT"]
}
# --- Pathfinder 1e racial ability modifiers ---
# Notes:
#  - "ANY": +2 to one ability of the player's choice (we auto-pick the class's top stat).
#  - Duplicate keys included for hyphen/space race name variants.
#  - If a race isn’t listed, no modifiers are applied.

race_stat_mods = {
    "Human":        {"ANY": 2},
    "Half-Elf":     {"ANY": 2}, "Half Elf": {"ANY": 2},
    "Half-Orc":     {"ANY": 2}, "Half Orc": {"ANY": 2},

    "Elf":          {"DEX": 2, "INT": 2, "CON": -2},
    "Dwarf":        {"CON": 2, "WIS": 2, "CHA": -2},
    "Gnome":        {"CON": 2, "CHA": 2, "STR": -2},
    "Halfling":     {"DEX": 2, "CHA": 2, "STR": -2},

    # Common featured/ARG races (optional—keep if you use them):
    "Aasimar":      {"WIS": 2, "CHA": 2},
    "Tiefling":     {"DEX": 2, "INT": 2, "CHA": -2},

    # Add others you use here, e.g. "Orc": {"STR": 4, "INT": -2, "WIS": -2, "CHA": -2}
}

# ---------- Ability Score Arrangement ----------

def get_arranged_scores(char_class):
    """
    Returns a base ability score dictionary arranged according to class priority.
    This mirrors Pathfinder's default stat emphasis pattern.
    """
    # Default 15–16 point buy style array
    base_scores = [16, 14, 14, 12, 10, 8]

    # Pull order from stat_priority or use standard fallback
    order = stat_priority.get(char_class, ["STR", "DEX", "CON", "INT", "WIS", "CHA"])

    # Assign scores to stats in priority order
    arranged = {stat: base_scores[i] for i, stat in enumerate(order)}

    return arranged


class_base_skill_ranks = {
    "Barbarian": 4, "Bard": 6, "Cleric": 2, "Druid": 4, "Fighter": 2,
    "Monk": 4, "Paladin": 2, "Ranger": 6, "Rogue": 8,
    "Sorcerer": 2, "Wizard": 2, "Artificer": 4, "Gunslinger": 4
}

# ---------- Skills & Abilities ----------

knowledge_skills = [
    "Knowledge:Arcana", "Knowledge:Dungeoneering", "Knowledge:Engineering",
    "Knowledge:Geography", "Knowledge:History", "Knowledge:Local",
    "Knowledge:Nature", "Knowledge:Nobility", "Knowledge:Planes", "Knowledge:Religion"
]

craft_subskills = [
    "Armor", "Weapons", "Jewelry", "Glass", "Traps", "Alchemy", "Woodworking", "Pottery"
]

perform_subskills = [
    "Act", "Comedy", "Dance", "Keyboard", "Oratory", "Percussion", "String", "Wind", "Sing"
]

profession_subskills = [
    "Farming", "Merchant", "Herbalist", "Cook", "Miner", "Clerk", "Innkeeper"
]

skill_to_ability = {
    # Standard Skills
    "Acrobatics": "DEX", "Bluff": "CHA", "Climb": "STR", "Diplomacy": "CHA",
    "Disable Device": "DEX", "Escape Artist": "DEX", "Handle Animal": "CHA",
    "Heal": "WIS", "Intimidate": "CHA", "Perception": "WIS", "Ride": "DEX",
    "Stealth": "DEX", "Survival": "WIS", "Spellcraft": "INT",
    "Use Magic Device": "CHA", "Open Lock": "DEX",
    # Knowledge Skills
    "Knowledge:Arcana": "INT", "Knowledge:Dungeoneering": "INT", "Knowledge:Engineering": "INT",
    "Knowledge:Geography": "INT", "Knowledge:History": "INT", "Knowledge:Local": "INT",
    "Knowledge:Nature": "INT", "Knowledge:Nobility": "INT", "Knowledge:Planes": "INT",
    "Knowledge:Religion": "INT",
    # Craft Skills (all INT)
    "Armor": "INT", "Weapons": "INT", "Jewelry": "INT", "Glass": "INT",
    "Traps": "INT", "Alchemy": "INT", "Woodworking": "INT", "Pottery": "INT",
    # Perform Skills (all CHA)
    "Act": "CHA", "Comedy": "CHA", "Dance": "CHA", "Keyboard": "CHA", "Oratory": "CHA",
    "Percussion": "CHA", "String": "CHA", "Wind": "CHA", "Sing": "CHA",
    # Profession Skills (all WIS)
    "Farming": "WIS", "Merchant": "WIS", "Herbalist": "WIS", "Cook": "WIS",
    "Miner": "WIS", "Clerk": "WIS", "Innkeeper": "WIS"
}

# ---------- PDF Field Mappings ----------

skill_short_prefix = {
    # Standard
    "Acrobatics": "acro", "Bluff": "bluf", "Climb": "clim", "Diplomacy": "dipl",
    "Disable Device": "ddvc", "Escape Artist": "esca", "Handle Animal": "hand",
    "Heal": "heal", "Intimidate": "inti", "Perception": "perc", "Ride": "ride",
    "Stealth": "stea", "Survival": "surv", "Spellcraft": "spel",
    "Use Magic Device": "umd", "Open Lock": "oplo",
    # Knowledge
    "Knowledge:Arcana": "knarc", "Knowledge:Dungeoneering": "kndun", "Knowledge:Engineering": "kneng",
    "Knowledge:Geography": "kngeo", "Knowledge:History": "knhis", "Knowledge:Local": "knloc",
    "Knowledge:Nature": "knnat", "Knowledge:Nobility": "knnbl", "Knowledge:Planes": "knpla",
    "Knowledge:Religion": "knrel",
    # Craft
    "Armor": "crarm", "Weapons": "crwea", "Jewelry": "crjew", "Glass": "crgla",
    "Traps": "crtra", "Alchemy": "cralc", "Woodworking": "crwoo", "Pottery": "crpot",
    # Perform
    "Act": "peract", "Comedy": "percom", "Dance": "perdan", "Keyboard": "perkey",
    "Oratory": "perora", "Percussion": "perper", "String": "perstr", "Wind": "perwin", "Sing": "persin",
    # Profession
    "Farming": "profar", "Merchant": "promer", "Herbalist": "proher", "Cook": "procoo",
    "Miner": "promin", "Clerk": "procle", "Innkeeper": "proinn"
}

# ---------- Flavor & Preference Data ----------

race_perform_pref = {
    "Elf": ["Sing", "Dance"],
    "Human": ["Oratory", "Act"],
    "Dwarf": ["Act"]
}

race_profession_pref = {
    "Dwarf": ["Miner", "Blacksmith"] ,
    "Elf": ["Herbalist", "Merchant"],
    "Human": ["Merchant", "Clerk"]
}

class_perform_pref = {
    "Bard": ["Sing", "Act", "Oratory"],
    "Rogue": ["Act", "Sing"]
}

class_profession_pref = {
    "Cleric": ["Herbalist", "Teaching"],
    "Rogue": ["Merchant", "Clerk"]
}
