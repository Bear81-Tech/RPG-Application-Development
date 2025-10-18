# character_logic.py
import re
import random
from typing import Dict, Any, List, Tuple

# Importing game data that is required by the logic functions
from resources.system.game_data import craft_subskills, perform_subskills, profession_subskills

# ------------------------------
# Master Choice Mapping (Moved from main file)
# ------------------------------
FEATURE_TO_CATEGORY_MAP = {
    "rogue talent": "rogue_talent",
    "advanced rogue talent": "advanced_rogue_talent",
    "advanced talents": "advanced_rogue_talent",
    "rage power": "rage_power",
    "mercy": "paladin_mercy",
    "favored enemy": "ranger_favored_enemy",
    "favored terrain": "ranger_favored_terrain",
    "combat style feat": "ranger_combat_style_archery", # Default, will be overwritten by random choice
    "bonus combat feat": "fighter_combat_feat",
    "ki power": "monk_ki_power",
    "bonus feat": "monk_bonus_feat",
    "style strike": "monk_style_strike",
    "arcane school power": "wizard_arcane_school_power",
    "bonus feat (wizard)": "wizard_bonus_feat",
    "arcane discovery": "wizard_arcane_discovery",
    "bloodline power": "sorcerer_bloodline_power",
    "bloodline feat": "sorcerer_bloodline_feat",
}

# ------------------------------
# Feature Resolver Utilities (Moved from main file/should be in utils.py)
# ------------------------------
def get_random_ranger_style() -> Tuple[str, str]:
    """Randomly selects a Ranger combat style for the feature resolver."""
    return random.choice([
        ("ranger_combat_style_archery", "Archery"),
        ("ranger_combat_style_two_weapon", "Two-Weapon Fighting")
    ])

def _canonicalize_slot_name(name: str) -> str:
    """Standardizes a feature name for map lookup."""
    return re.sub(r"\s*\+\d+$", "", name.strip().lower())

def _extract_min_level_and_class(prereq_text: str) -> Tuple[str, int]:
    """Extracts minimum class/level from a prerequisite string."""
    if not prereq_text:
        return ("", 0)
    m = re.search(r"([A-Za-z]+)\s*(\d+)\+", prereq_text)
    return (m.group(1), int(m.group(2))) if m else ("", 0)

def option_prereq_ok(option: Dict[str, Any], char_class: str, level: int) -> bool:
    """Checks if a feature option meets class/level prerequisites."""
    prereq = (option.get("prerequisite") or "").strip()
    if not prereq or prereq.lower() == "none":
        return True
    cls, min_lvl = _extract_min_level_and_class(prereq)
    if cls and min_lvl:
        return (char_class.lower() == cls.lower()) and (level >= min_lvl)
    return True


# ------------------------------
# Skill Logic (Moved from main file's utility block)
# ------------------------------
def _norm_for_membership(s: str) -> str:
    """Normalizes a skill name for set membership checking."""
    s = s.lower().strip().replace("’", "'").replace("knowledge(", "knowledge:").replace(")", "")
    s = s.replace("knowledge (", "knowledge:")
    return re.sub(r"\s+", "", s)

def _is_class_skill_name(skill, norm_class_skills: set) -> bool:
    """Checks if a skill is a class skill, including subskills."""
    n = _norm_for_membership(skill)
    if n in norm_class_skills: return True
    if skill in craft_subskills and _norm_for_membership("Craft") in norm_class_skills: return True
    if skill in perform_subskills and _norm_for_membership("Perform") in norm_class_skills: return True
    if skill in profession_subskills and _norm_for_membership("Profession") in norm_class_skills: return True
    return False

def choose_subskills_for_character(char_class: str, race: str) -> Dict[str, List[str]]:
    """Randomly selects subskills for skills that require specialization (Craft, Perform, Profession)."""
    crafts = random.sample(craft_subskills, 3)
    return {"Craft": crafts, "Perform": perform_subskills[:2], "Profession": profession_subskills[:2]}


# ------------------------------
# Character Metadata Logic (Moved from main file's utility block)
# ------------------------------
def get_random_name(race: str, gender: str, data: Dict[str, Any]) -> str:
    """Generates a random name based on race, gender, and data from names.json."""
    # ... (Keep the full implementation of get_random_name here)
    if race not in data: return "Unnamed"
    nd = data[race]
    g = gender.lower()

    if race == "Elf":
        pa, pb, pc, pd = nd.get("part_a",[]), nd.get("part_b",[]), nd.get("part_c",[]), nd.get("part_d",[])
        endings = nd.get("male_endings" if g == "male" else "female_endings", [])
        def choose(lst): return random.choice(lst) if lst else "" # local choose to avoid global import
        if random.choice([True, False]): return f"{choose(pa)}'{choose(pb)}{choose(pc)} {choose(pd)}{choose(endings)}"
        else: return f"{choose(pa)}'{choose(pb)}{choose(pc)}{choose(endings)}"
    
    # ... (rest of the logic for Dark Elf and generic names)
    if race == "Dark Elf":
        demp, dems = nd.get("male_prefixes",[]), nd.get("male_suffixes",[])
        defp, defs_ = nd.get("female_prefixes",[]), nd.get("female_suffixes",[])
        dehp, dehs = nd.get("house_prefixes",[]), nd.get("house_suffixes",[])
        eme = nd.get("female_suffixes",[])
        def choose(lst): return random.choice(lst) if lst else ""
        if g == "male":
            v = random.randint(1, 3)
            if v == 1: return f"{choose(demp)}'{choose(dems)} {choose(dehp)}'{choose(dehs)}"
            elif v == 2: return f"{choose(demp)}'{choose(dems)}'{choose(dems)}{choose(eme)} {choose(dehp)}'{choose(dehs)}"
            else: return f"{choose(demp)}'{choose(dems)}{choose(eme)}"
        else:
            v = random.randint(1, 2)
            if v == 1: return f"{choose(defp)}'{choose(defs_)} {choose(dehp)}'{choose(dehs)}"
            else: return f"{choose(defp)}'{choose(defs_)}{choose(eme)} {choose(dehp)}'{choose(dehs)}"

    first_names = nd.get(f"{g}_first", nd.get("male_first", []))
    last_names = nd.get("last", nd.get("clans", []))
    def choose(lst): return random.choice(lst) if lst else ""
    return f"{choose(first_names)} {choose(last_names)}"

def assign_languages(character, data):
    """Assigns starting and bonus languages to the character."""
    rdata = data.get("races", {}).get(character.race, {})
    langs = rdata.get("defaultLanguages", ["Common"])
    pool = [l for l in rdata.get("bonusLanguages", []) if l not in langs]
    random.shuffle(pool)
    bonus = max(0, character.abilityScores["INT"]["mod"])
    character.languages = langs + pool[:bonus]


# ------------------------------
# Feat Selection Logic (Moved from main file)
# ------------------------------
def pick_character_feats(level: int, race: str, feats: List[Dict[str, Any]]) -> List[str]:
    """Randomly selects feats ensuring prerequisites are met (as best as possible with available data)."""
    # ... (Keep the full implementation of pick_character_feats here)
    import re, random
    # how many feats to pick (PF1e baseline + human bonus)
    num_feats = (level // 2) + 1 + (1 if str(race).lower() == 'human' else 0)

    # cache all feat names to detect dependencies
    all_feat_names = set()
    for f in feats:
        nm = (f.get('title') or f.get('name') or '').strip().lower()
        if nm:
            all_feat_names.add(nm)

    chosen = []
    chosen_set = set()

    def prereq_met(feat):
        reasons = []
        ok = True

        # normalize text
        prereq = (feat.get('property') or feat.get('prerequisite') or '').strip()
        prereq_low = prereq.lower()

        if not prereq or prereq_low in ('none', ''):
            reasons.append('no prerequisites')
            return True, reasons

        # --- Character level requirement (e.g., "character level 10th", "level 10", "lvl 10") ---
        m = re.search(r'(?:character\s+level|level|lvl)\s*(\d+)', prereq_low)
        if m:
            need = int(m.group(1))
            if level < need:
                ok = False
                reasons.append(f'needs level {need}')

        # --- Base Attack Bonus requirement (heuristic): "base attack bonus +X" ---
        if re.search(r'base\s+attack\s+bonus\s*[+−-]?\s*(\d+)', prereq_low):
            reasons.append('BAB prereq present (not enforced here)')

        # --- Race restriction (common PF1e races) ---
        race_terms = ['human','elf','dwarf','halfling','gnome','half-orc','half-elf','aasimar','tiefling','orc','catfolk','tengu','ratfolk','ifrit','sylph','undine','fetchling','dhampir']
        mentioned = [r for r in race_terms if r in prereq_low]
        if mentioned:
            if str(race).lower() not in prereq_low:
                ok = False
                reasons.append(f'race restricted ({", ".join(mentioned)})')

        # --- Ability score prereqs (e.g., "Dex 13", "STR 15") — not enforced here ---
        if re.search(r'\b(str|dex|con|int|wis|cha)\s*(\d+)', prereq_low):
            reasons.append('ability prereq present (not enforced here)')

        # --- Feat dependency (very rough heuristic) ---
        mentioned_feats = [nm for nm in all_feat_names if nm and nm in prereq_low]
        if mentioned_feats:
            if not any(nm in chosen_set for nm in mentioned_feats):
                ok = False
                reasons.append('missing required feat(s): ' + ', '.join(mentioned_feats[:3]))

        return ok, reasons if reasons else ['prereq text found']

    # Try to pick until we have enough feats or we run out
    pool = feats.copy()
    random.shuffle(pool)
    attempts = 0
    MAX_ATTEMPTS = len(pool) * 3 if pool else 0

    for feat in pool:
        if len(chosen) >= num_feats:
            break
        attempts += 1
        ok, reasons = prereq_met(feat)
        ftitle = feat.get('title') or feat.get('name') or 'Unknown'
        if ok:
            chosen.append(ftitle)
            chosen_set.add(ftitle.strip().lower())
            print(f"[DEBUG] Feat ACCEPTED → {ftitle} | reasons: {', '.join(reasons)}", flush=True)
        else:
            print(f"[DEBUG] Feat REJECTED → {ftitle} | reasons: {', '.join(reasons)}", flush=True)
        if attempts >= MAX_ATTEMPTS and len(chosen) < num_feats:
            print(f"[DEBUG] Stopping early after {attempts} attempts; picked {len(chosen)}/{num_feats} feats.", flush=True)
            break

    return chosen
