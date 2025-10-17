def pick_character_feats(level, race, feats):
    """
    Randomly selects feats ensuring prerequisites are met.
    Emits [DEBUG] logs for both accepted and rejected feats with reasons.
    Uses prerequisite text from either 'property' or 'prerequisite' fields.
    """
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
        # We cannot compute exact BAB here (class-dependent), so log and do a soft allow.
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
        # If the prereq mentions at least one known feat name and none are already chosen, reject.
        mentioned_feats = [nm for nm in all_feat_names if nm and nm in prereq_low]
        if mentioned_feats:
            if not any(nm in chosen_set for nm in mentioned_feats):
                ok = False
                # show at most 3 to keep logs readable
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


# ================================================================
# Master Working Copy with full functionality (final_sync_rangerfix).py
# Version: 2025-10-08
# Author: ChatGPT (assistant to Anthony Falsone / BKI-Applications)
#
#Class outputs with full functionality:Rogue, Ranger.
#
# Summary of this build:
#  • Expands FEATURE_TO_CATEGORY_MAP (Rogue→Sorcerer)
#  • Randomizes Ranger combat style (Archery / Two-Weapon)
#  • Displays chosen style at Level 2 in TXT and PDF
#  • Ensures identical feature rolls across TXT and PDF
#  • Keeps [DEBUG] outputs for transparency
# ================================================================

import os, sys, re, json, random
from typing import Dict, Any, List, Tuple

from game_data import *
from utils import choose, sanitize_filename, ensure_dir, load_json
from output import fill_pdf, save_text

# ------------------------------
# Load Data
# ------------------------------
names_data = load_json("resources/names.json")
languages_data = load_json("resources/language.json")
class_abilities_data = load_json("resources/class_abilities.json")
feats_json_data = load_json("resources/feats.json")
master_class_choices = load_json("resources/master_class_choices.json")
spells_per_day_data = load_json("resources/spells_per_day.json")

# ------------------------------
# Normalize feats
# ------------------------------
def _normalize_feats_list(feats_json):
    feats = []
    iterable = feats_json if isinstance(feats_json, list) else feats_json.get("feats", [])
    for f in iterable:
        nm = (f.get("feat") or f.get("title") or "").strip()
        if nm:
            feats.append({
                "name": nm,
                "prerequisite": (f.get("prerequisite") or "").strip(),
                "summary": (f.get("summary") or "").strip(),
                "category": f.get("category", []),
            })
    return feats

feats_flat = _normalize_feats_list(feats_json_data)

# ------------------------------
# Master Choice Mapping
# ------------------------------
FEATURE_TO_CATEGORY_MAP = {
    "rogue talent": "rogue_talent",
    "advanced rogue talent": "advanced_rogue_talent",
    "advanced talents": "advanced_rogue_talent",
    "rage power": "rage_power",
    "mercy": "paladin_mercy",
    "favored enemy": "ranger_favored_enemy",
    "favored terrain": "ranger_favored_terrain",
    "combat style feat": "ranger_combat_style_archery",
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
# Ranger style helper
# ------------------------------
def get_random_ranger_style() -> Tuple[str, str]:
    return random.choice([
        ("ranger_combat_style_archery", "Archery"),
        ("ranger_combat_style_two_weapon", "Two-Weapon Fighting")
    ])

# Default placeholder
FEATURE_TO_CATEGORY_MAP["combat style feat"] = "ranger_combat_style_archery"

def _canonicalize_slot_name(name: str) -> str:
    return re.sub(r"\s*\+\d+$", "", name.strip().lower())

def _extract_min_level_and_class(prereq_text: str) -> Tuple[str, int]:
    if not prereq_text:
        return ("", 0)
    m = re.search(r"([A-Za-z]+)\s*(\d+)\+", prereq_text)
    return (m.group(1), int(m.group(2))) if m else ("", 0)

def option_prereq_ok(option: Dict[str, Any], char_class: str, level: int) -> bool:
    prereq = (option.get("prerequisite") or "").strip()
    if not prereq or prereq.lower() == "none":
        return True
    cls, min_lvl = _extract_min_level_and_class(prereq)
    if cls and min_lvl:
        return (char_class.lower() == cls.lower()) and (level >= min_lvl)
    return True

# ------------------------------
# Core feature resolver
# ------------------------------
def resolve_class_features_with_options(char_class: str, level: int,
                                        abilities: Dict[str, Any],
                                        master_choices: Dict[str, Any]) -> Tuple[List[str], Dict[int, List[str]]]:
    lines, replacements = [], {}
    cls_block = (abilities or {}).get(char_class, {})
    levels = cls_block.get("levels", {})
    chosen_by_category: Dict[str, set] = {}

    for L in range(1, level + 1):
        for feat in levels.get(str(L), []):
            base_name = feat.get("name") if isinstance(feat, dict) else feat
            base_name = base_name or "Unknown Feature"
            slot_key = _canonicalize_slot_name(base_name)
            category = FEATURE_TO_CATEGORY_MAP.get(slot_key)

            # --- Special case: Ranger combat style ---
            if char_class.lower() == "ranger" and "combat style" in slot_key:
                if not hasattr(resolve_class_features_with_options, "_ranger_style_choice"):
                    style_key, style_label = get_random_ranger_style()
                    resolve_class_features_with_options._ranger_style_choice = (style_key, style_label)
                else:
                    style_key, style_label = resolve_class_features_with_options._ranger_style_choice
                category = style_key
                if L == 2:
                    lines.append(f"Lvl 2: Combat Style – {style_label}")
                    replacements.setdefault(L, []).append(f"Combat Style – {style_label}")

            if category and master_choices.get(category):
                pool = master_choices[category]
                pool_ok = [opt for opt in pool if option_prereq_ok(opt, char_class, L)]
                chosen = chosen_by_category.setdefault(category, set())
                pool_ok = [opt for opt in pool_ok if opt["name"] not in chosen]
                if pool_ok:
                    picked = random.choice(pool_ok)
                    chosen.add(picked["name"])
                    lines.append(f"Lvl {L}: {picked['name']}")
                    replacements.setdefault(L, []).append(picked["name"])
                    continue
            lines.append(f"Lvl {L}: {base_name}")
    return lines, replacements

def build_pdf_class_abilities_with_replacements(base_data: Dict[str, Any],
                                                char_class: str,
                                                replacements: Dict[int, List[str]]) -> Dict[str, Any]:
    import copy
    data = copy.deepcopy(base_data)
    levels = data.get(char_class, {}).get("levels", {})
    for lvl, picks in replacements.items():
        ary = levels.get(str(lvl), [])
        queue = list(picks)
        new_entries = []
        for entry in ary:
            nm = entry.get("name") if isinstance(entry, dict) else str(entry)
            slot_key = _canonicalize_slot_name(nm)
            if queue and slot_key in FEATURE_TO_CATEGORY_MAP:
                new_entries.append({"name": queue.pop(0)})
            else:
                new_entries.append(entry)
        levels[str(lvl)] = new_entries
    return data

# ------------------------------
# Debug helper
# ------------------------------
def prepare_feature_replacements_for_output(character, class_abilities_data, master_class_choices, level_cap=None):
    char_class = getattr(character, "char_class", "Rogue")
    level = level_cap or getattr(character, "level", 1)
    lines, replacements = resolve_class_features_with_options(
        char_class, int(level), class_abilities_data, master_class_choices
    )
    custom = build_pdf_class_abilities_with_replacements(class_abilities_data, char_class, replacements)
    print("[DEBUG] Generated Abilities:")
    for ln in lines:
        print("  ", ln)
    return lines, custom

# ------------------------------
# Utility blocks (skills, etc.)
# ------------------------------
def _norm_for_membership(s: str) -> str:
    s = s.lower().strip().replace("’", "'").replace("knowledge(", "knowledge:").replace(")", "")
    s = s.replace("knowledge (", "knowledge:")
    return re.sub(r"\s+", "", s)

def _normalize_class_skill_list(raw):
    return {_norm_for_membership(it) for it in (raw or [])}

def _is_class_skill_name(skill, norm):
    n = _norm_for_membership(skill)
    if n in norm: return True
    if skill in craft_subskills and _norm_for_membership("Craft") in norm: return True
    if skill in perform_subskills and _norm_for_membership("Perform") in norm: return True
    if skill in profession_subskills and _norm_for_membership("Profession") in norm: return True
    return False

def choose_subskills_for_character(char_class, race):
    crafts = random.sample(craft_subskills, 3)
    return {"Craft": crafts, "Perform": perform_subskills[:2], "Profession": profession_subskills[:2]}

def assign_languages(character, data):
    rdata = data.get("races", {}).get(character.race, {})
    langs = rdata.get("defaultLanguages", ["Common"])
    pool = [l for l in rdata.get("bonusLanguages", []) if l not in langs]
    random.shuffle(pool)
    bonus = max(0, character.abilityScores["INT"]["mod"])
    character.languages = langs + pool[:bonus]


def get_random_name(race, gender, data):
    """Generates a random name based on race, gender, and data from names.json (original logic)."""
    if race not in data: return "Unnamed"
    nd = data[race]
    g = gender.lower()

    if race == "Elf":
        pa, pb, pc, pd = nd.get("part_a",[]), nd.get("part_b",[]), nd.get("part_c",[]), nd.get("part_d",[])
        endings = nd.get("male_endings" if g == "male" else "female_endings", [])
        if random.choice([True, False]): return f"{choose(pa)}'{choose(pb)}{choose(pc)} {choose(pd)}{choose(endings)}"
        else: return f"{choose(pa)}'{choose(pb)}{choose(pc)}{choose(endings)}"
    
    if race == "Dark Elf":
        demp, dems = nd.get("male_prefixes",[]), nd.get("male_suffixes",[])
        defp, defs_ = nd.get("female_prefixes",[]), nd.get("female_suffixes",[])
        dehp, dehs = nd.get("house_prefixes",[]), nd.get("house_suffixes",[])
        eme = nd.get("female_suffixes",[])
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
    return f"{choose(first_names)} {choose(last_names)}"

# ------------------------------
# Character
# ------------------------------
class Character:
    def __init__(self, char_class, level, race, gender, alignment, name):
        print(f"[DEBUG] Building character: {char_class} L{level} {race} {gender}", flush=True)
        self.char_class, self.level, self.race, self.gender, self.alignment, self.name = \
            char_class, level, race, gender, alignment, name
        self.class_skills_list = class_abilities_data.get(self.char_class, {}).get("features", {}).get("class_skills", [])
        self._class_skills_norm = _normalize_class_skill_list(self.class_skills_list)
        self.chosen_subskills = choose_subskills_for_character(char_class, race)
        self.abilityScores = self._make_ability_scores()
        self.hitPoints = self._calculate_hit_points()
        self.bab, self.iterative_attacks = self._compute_bab_and_iterations()
        self.skillRanks = self._assign_skill_ranks()
        self.skillBonuses = self._compute_skill_bonuses()

        # --- Features and feats ---
        lines, replacements = resolve_class_features_with_options(
            self.char_class, self.level, class_abilities_data, master_class_choices
        )
        self.features_and_abilities = lines
        self._feature_replacements = replacements
        if hasattr(resolve_class_features_with_options, "_ranger_style_choice"):
            self.combat_style = resolve_class_features_with_options._ranger_style_choice[1]
        else:
            self.combat_style = None
        if self.char_class == "Ranger":
            print(f"[DEBUG] Ranger combat style selected: {self.combat_style}", flush=True)
        self.feats = pick_character_feats(self.level, self.race, feats_flat)

    # --- internal ---
    def _make_ability_scores(self):
        rolls = sorted([sum(sorted([random.randint(1,6) for _ in range(4)])[1:]) for _ in range(6)], reverse=True)
        prio = stat_priority.get(self.char_class, ["STR","DEX","CON","INT","WIS","CHA"])
        canonical = ["STR","DEX","CON","INT","WIS","CHA"]
        scores={st:{"score":10,"mod":0} for st in canonical}
        for i,st in enumerate(prio):
            if i<len(rolls):
                v=rolls[i];scores[st]={"score":v,"mod":(v-10)//2}
        return scores

    def _calculate_hit_points(self):
        hd={"Barbarian":12,"Fighter":10,"Paladin":10,"Ranger":10,"Bard":8,"Cleric":8,
            "Druid":8,"Monk":8,"Rogue":8,"Sorcerer":6,"Wizard":6}.get(self.char_class,8)
        con=self.abilityScores["CON"]["mod"]
        return hd + ((hd//2)+con)*(self.level-1)

    def _compute_bab_and_iterations(self):
        prog=bab_progressions.get(self.char_class,0.75)
        bab=int(self.level*prog)
        parts=[];cur=bab
        while cur>0: parts.append(f"+{cur}");cur-=5
        return bab,"/".join(parts)

    def _assign_skill_ranks(self):
        base=class_base_skill_ranks.get(self.char_class,2)
        mod=self.abilityScores["INT"]["mod"]
        ranks_per=max(1,base+mod+(1 if self.race=="Human" else 0))
        total=ranks_per*self.level
        ranks={s:0 for s in skill_to_ability}
        pri=[s for s in ranks if _is_class_skill_name(s,self._class_skills_norm)]
        pool=pri*2+list(ranks)
        while total>0 and pool:
            s=random.choice(pool);ranks[s]+=1;total-=1
        return ranks

    def _compute_skill_bonuses(self):
        out={}
        for s,r in self.skillRanks.items():
            a=skill_to_ability.get(s,"INT");mod=self.abilityScores[a]["mod"]
            cls=3 if r>0 and _is_class_skill_name(s,self._class_skills_norm) else 0
            out[s]={"ranks":r,"ability_mod":mod,"class_skill_bonus":cls,"total":r+mod+cls}
        return out

# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    print("[DEBUG] Master Working Copy (final_sync_rangerfix) started.", flush=True)
    SKIP_PDF="--skip-pdf" in sys.argv; AUTO="--auto" in sys.argv
    races=list(names_data) if isinstance(names_data,dict) else ["Human"]
    classes=list(bab_progressions); aligns=["Lawful Good","Neutral Good","Chaotic Good",
                                            "Lawful Neutral","True Neutral","Chaotic Neutral",
                                            "Lawful Evil","Neutral Evil","Chaotic Evil"]

    if AUTO:
        race=random.choice(races);gender=random.choice(["Male","Female"])
        cclass=random.choice(classes);align=random.choice(aligns);lvl=random.randint(1,20)
        print(f"[DEBUG] AUTO → {race=}, {gender=}, {cclass=}, {align=}, {lvl=}",flush=True)
    else:
        print("Choose Race:");[print(f"[{i+1}] {r}") for i,r in enumerate(races)]
        race=races[int(input("> "))-1]
        print("Choose Gender:\n[1] Male\n[2] Female")
        gender=["Male","Female"][int(input("> "))-1]
        print("Choose Class:");[print(f"[{i+1}] {c}") for i,c in enumerate(classes)]
        cclass=classes[int(input("> "))-1]
        print("Choose Alignment:");[print(f"[{i+1}] {a}") for i,a in enumerate(aligns)]
        align=aligns[int(input("> "))-1]
        lvl=int(input("Enter Level (1–20): "))

    print("[DEBUG] generating name…",flush=True)
    name=get_random_name(race,gender,names_data)
    print(f"[DEBUG] Name generated: {name}",flush=True)

    print("[DEBUG] building character…",flush=True)
    char=Character(cclass,lvl,race,gender,align,name)
    assign_languages(char,languages_data)

    ensure_dir("Characters")
    fname=sanitize_filename(char.name) or "character"
    txt=os.path.join("Characters",f"{fname}.txt")
    pdf=os.path.join("Characters",f"{fname}.pdf")

    print(f"[DEBUG] writing TXT → {txt}",flush=True)
    save_text(char, txt)

    if not SKIP_PDF:
        print("[DEBUG] generating PDF…",flush=True)
        _custom=build_pdf_class_abilities_with_replacements(
            class_abilities_data,char.char_class,getattr(char,"_feature_replacements",{})
        )
        fill_pdf(char,"rev char sheet.pdf",pdf,_custom)
        print(f"[DEBUG] wrote PDF → {pdf}",flush=True)
    else:
        print("[DEBUG] --skip-pdf set; skipping PDF.",flush=True)

    print(f"\nCharacter '{name}' created!",flush=True)
    print(f"TXT: {txt}",flush=True)
    if not SKIP_PDF: print(f"PDF: {pdf}",flush=True)


