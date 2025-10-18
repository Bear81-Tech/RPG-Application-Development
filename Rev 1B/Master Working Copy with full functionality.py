# ================================================================
# Master Working Copy with full functionality (UPDATED MODULAR BUILD)
# Version: 2025-10-18
# Summary of this build:
#  • Core Character class moved to character_model.py
#  • Helper functions (name gen, feats, etc.) moved to character_logic.py
#  • Core execution logic remains here
# ================================================================

import os, sys, re, json, random
from typing import Dict, Any, List, Tuple

# Import the core data model and logic
from resources.system.character_model import Character
from resources.system.character_logic import get_random_name, assign_languages, _canonicalize_slot_name, FEATURE_TO_CATEGORY_MAP

# Import system utilities (assuming these are in your existing utils.py)
from resources.system.utils import choose, sanitize_filename, ensure_dir, load_json
from resources.system.output import fill_pdf, save_text
from resources.system.game_data import bab_progressions # Used for list of classes

# ------------------------------
# Load Data
# ------------------------------
names_data = load_json("resources/race/names.json")
languages_data = load_json("resources/race/language.json")
class_abilities_data = load_json("resources/class/class_abilities.json")
feats_json_data = load_json("resources/common/feats.json")
master_class_choices = load_json("resources/class/master_class_choices.json")
spells_per_day_data = load_json("resources/class/spells_per_day.json")

# ------------------------------
# Normalize feats (Kept here as it processes loaded data for the character)
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
# PDF Builder Helper (Kept here as it's part of the output pipeline)
# ------------------------------
def build_pdf_class_abilities_with_replacements(base_data: Dict[str, Any],
                                                char_class: str,
                                                replacements: Dict[int, List[str]]) -> Dict[str, Any]:
    """Applies the randomized feature replacements to the PDF data structure."""
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
            # Only replace features that are actual "slots" defined in the map
            if queue and slot_key in FEATURE_TO_CATEGORY_MAP: 
                new_entries.append({"name": queue.pop(0)})
            else:
                new_entries.append(entry)
        levels[str(lvl)] = new_entries
    return data

# ------------------------------
# Main Execution
# ------------------------------
if __name__ == "__main__":
    print("[DEBUG] Master Working Copy (UPDATED MODULAR BUILD) started.", flush=True)
    SKIP_PDF="--skip-pdf" in sys.argv; AUTO="--auto" in sys.argv
    races=list(names_data) if isinstance(names_data,dict) else ["Human"]
    classes=list(bab_progressions); aligns=["Lawful Good","Neutral Good","Chaotic Good",
                                            "Lawful Neutral","True Neutral","Chaotic Neutral",
                                            "Lawful Evil","Neutral Evil","Chaotic Evil"]

    # --- Input Handling ---
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

    # --- Character Generation ---
    print("[DEBUG] generating name…",flush=True)
    name=get_random_name(race,gender,names_data)
    print(f"[DEBUG] Name generated: {name}",flush=True)

    print("[DEBUG] building character…",flush=True)
    # Instantiate Character using the imported class and passing necessary data
    char=Character(cclass,lvl,race,gender,align,name,
                   class_abilities_data, master_class_choices, feats_flat)
    
    # Assign languages using the imported logic function
    assign_languages(char,languages_data) 

    # --- Output ---
    ensure_dir("Characters")
    fname=sanitize_filename(char.name) or "character"
    txt=os.path.join("Characters",f"{fname}.txt")
    pdf=os.path.join("Characters",f"{fname}.pdf")

    print(f"[DEBUG] writing TXT → {txt}",flush=True)
    save_text(char, txt)

    if not SKIP_PDF:
        print("[DEBUG] generating PDF…",flush=True)
        # Use the replacements calculated and stored in the character object
        _custom=build_pdf_class_abilities_with_replacements(
            class_abilities_data,char.char_class,getattr(char,"_feature_replacements",{})
        )
        fill_pdf(char,"resources/system/rev char sheet.pdf",pdf,_custom)
        print(f"[DEBUG] wrote PDF → {pdf}",flush=True)
    else:
        print("[DEBUG] --skip-pdf set; skipping PDF.",flush=True)

    print(f"\nCharacter '{name}' created!",flush=True)
    print(f"TXT: {txt}",flush=True)
    if not SKIP_PDF: print(f"PDF: {pdf}",flush=True)
