# output.py
# SPECIAL ABILITIES for PDF now writes:
#   SA 1 → "Weapons: …"
#   SA 2 → "Armor: …"
#   SA 3 → "Shields: …" (if any)
# …then class features up to level, 2 per field starting at the next slot.
# FEATS = names only (3 per line); overflow to SPECIAL ABILITIES 16–21.
# Class-skill checkboxes robust; +3 class bonus safety net; subskills filled; initiative via feats.

import os, json, re
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject, BooleanObject, DictionaryObject
from game_data import *  # skill_short_prefix, skill_to_ability, subskill lists, etc.

# ============================================================
#                  FEATS INDEX (RE)MERGE
# ============================================================

def _feat_paths():
    here = os.path.dirname(__file__)
    candidates_simple = [
        os.path.join(os.getcwd(), "feats.json"),
        os.path.join(os.getcwd(), "resources", "feats.json"),
        os.path.join(here, "feats.json"),
        os.path.join(here, "resources", "feats.json"),
    ]
    candidates_complex = [
        os.path.join(os.getcwd(), "feats.bak.json"),
        os.path.join(os.getcwd(), "resources", "feats.bak.json"),
        os.path.join(here, "feats.bak.json"),
        os.path.join(here, "resources", "feats.bak.json"),
    ]
    return candidates_simple, candidates_complex

def _load_json_if_exists(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _minimize_to_bonus(text: str) -> str:
    if not text:
        return ""
    m = re.search(r'([+-]\s*\d+%?)', text)
    if not m:
        return ""
    start = m.start()
    period = text.find(".", start)
    snippet = text[start:] if period == -1 else text[start:period]
    return snippet.strip()

def _extract_second_text_after_second_rule(contents):
    rule_count = 0
    texts_after = []
    for item in contents:
        if isinstance(item, str) and item.strip().lower() == "rule":
            rule_count += 1
            continue
        if rule_count >= 2 and isinstance(item, str) and item.lower().startswith("text |"):
            parts = item.split("|", 1)
            payload = parts[1].strip() if len(parts) > 1 else ""
            texts_after.append(payload)
    return texts_after[1].strip() if len(texts_after) >= 2 else ""

def _build_index_from_complex_obj(data_obj):
    feat_index = {}
    feats_list = []
    if isinstance(data_obj, dict) and isinstance(data_obj.get("feats"), list):
        feats_list = data_obj["feats"]
    elif isinstance(data_obj, list):
        feats_list = data_obj
    else:
        return feat_index

    for feat in feats_list:
        try:
            name = (feat.get("title") or feat.get("feat") or "").strip()
            if not name:
                continue
            prereq = ""
            contents = feat.get("contents", [])
            if isinstance(contents, list):
                for item in contents:
                    if isinstance(item, str) and item.lower().startswith("property | prerequisites |"):
                        parts = item.split("|")
                        if len(parts) >= 3:
                            prereq = parts[2].strip()
                        break
                mechanics_text = _extract_second_text_after_second_rule(contents)
            else:
                mechanics_text = ""
            summary = _minimize_to_bonus(mechanics_text)
            feat_index[name.lower()] = {
                "feat": name,
                "prerequisite": prereq,
                "summary": summary
            }
        except Exception:
            continue
    return feat_index

def _try_save_simplified_index_to(path, feat_index):
    try:
        out = [{"feat": v["feat"], "prerequisite": v["prerequisite"], "summary": v["summary"]}
               for v in sorted(feat_index.values(), key=lambda x: x["feat"].lower())]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Re-merged feats written to: {path} ({len(out)} feats)")
    except Exception as e:
        print(f"[DEBUG] Could not write simplified feats.json: {e}")

def load_or_build_feat_index():
    candidates_simple, candidates_complex = _feat_paths()
    for p in candidates_simple:
        data = _load_json_if_exists(p)
        if isinstance(data, list) and data and isinstance(data[0], dict) and "feat" in data[0]:
            idx = {}
            for it in data:
                name = str(it.get("feat", "")).strip()
                if not name:
                    continue
                idx[name.lower()] = {
                    "feat": name,
                    "prerequisite": str(it.get("prerequisite", "")).strip(),
                    "summary": str(it.get("summary", "")).strip(),
                }
            print(f"[DEBUG] Using simplified feats.json: {p} ({len(idx)} feats)")
            return idx
    for p in candidates_simple:
        data = _load_json_if_exists(p)
        if isinstance(data, dict) and "feats" in data:
            idx = _build_index_from_complex_obj(data)
            if idx:
                _try_save_simplified_index_to(p, idx)
                print(f"[DEBUG] Built feat index from book-ish feats.json: {p} ({len(idx)} feats)")
                return idx
    for p in candidates_complex:
        data = _load_json_if_exists(p)
        if data:
            idx = _build_index_from_complex_obj(data)
            if idx:
                target = candidates_simple[0]
                _try_save_simplified_index_to(target, idx)
                print(f"[DEBUG] Built feat index from feats.bak.json: {p} ({len(idx)} feats)")
                return idx
    print("[DEBUG] No feats file found; initiative misc from feats will be 0 unless hard-coded.")
    return {}

# ============================================================
#            CLASS ABILITIES / PROFICIENCIES HELPERS
# ============================================================

def _load_features_from_disk(char_class):
    candidates = [
        os.path.join(os.getcwd(), "class_abilities.json"),
        os.path.join(os.getcwd(), "resources", "class_abilities.json"),
        os.path.join(os.path.dirname(__file__), "class_abilities.json"),
        os.path.join(os.path.dirname(__file__), "resources", "class_abilities.json"),
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get(char_class), dict):
                feats = data[char_class].get("features") or {}
                return feats
        except Exception:
            pass
    return {}

def extract_proficiencies_for_pdf(char_class, class_skills_data):
    feats = {}
    if isinstance(class_skills_data, dict):
        cd = class_skills_data.get(char_class) or {}
        feats = cd.get("features") or {}
    elif isinstance(class_skills_data, list):
        for entry in class_skills_data:
            if isinstance(entry, dict) and isinstance(entry.get(char_class), dict):
                feats = entry[char_class].get("features") or {}
                break
    if not feats:
        feats = _load_features_from_disk(char_class)
    prof = feats.get("proficiencies") or {}
    weapons = prof.get("weapons") or []
    armor = prof.get("armor") or []
    shields = prof.get("shields") or []
    return weapons, armor, shields

def _try_extract_levels_from_param(char_class, class_skills_data):
    if isinstance(class_skills_data, dict):
        cd = class_skills_data.get(char_class)
        if isinstance(cd, dict):
            for k, v in cd.items():
                if isinstance(k, str) and k.lower() == "levels" and isinstance(v, dict):
                    return v
    if isinstance(class_skills_data, list):
        for entry in class_skills_data:
            if isinstance(entry, dict) and char_class in entry and isinstance(entry[char_class], dict):
                cd = entry[char_class]
                for k, v in cd.items():
                    if isinstance(k, str) and k.lower() == "levels" and isinstance(v, dict):
                        return v
    return None

def _load_levels_from_disk(char_class):
    candidates = [
        os.path.join(os.getcwd(), "class_abilities.json"),
        os.path.join(os.getcwd(), "resources", "class_abilities.json"),
        os.path.join(os.path.dirname(__file__), "class_abilities.json"),
        os.path.join(os.path.dirname(__file__), "resources", "class_abilities.json"),
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cd = data.get(char_class)
                if isinstance(cd, dict):
                    lev = cd.get("levels") or cd.get("Levels")
                    if isinstance(lev, dict):
                        print(f"[DEBUG] Loaded 'levels' for {char_class} from {path}")
                        return lev
        except Exception:
            pass
    print(f"[DEBUG] Could not find 'levels' for {char_class} on disk.")
    return {}

def extract_levels_for_pdf(char_class, class_skills_data):
    lev = _try_extract_levels_from_param(char_class, class_skills_data)
    if isinstance(lev, dict):
        return lev
    return _load_levels_from_disk(char_class)

def _clean_name_only(s):
    if not s:
        return ""
    s = str(s).strip()
    s = s.split("—")[0].split("-")[0].split(":")[0].strip()
    return s

def _load_class_skills_from_disk(char_class):
    candidates = [
        os.path.join(os.getcwd(), "class_abilities.json"),
        os.path.join(os.getcwd(), "resources", "class_abilities.json"),
        os.path.join(os.path.dirname(__file__), "class_abilities.json"),
        os.path.join(os.path.dirname(__file__), "resources", "class_abilities.json"),
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cd = data.get(char_class)
                if isinstance(cd, dict):
                    feats = cd.get("features") or cd.get("Features") or {}
                    if isinstance(feats, dict):
                        cls = feats.get("class_skills")
                        if isinstance(cls, list):
                            print(f"[DEBUG] Loaded class_skills for {char_class} from {path}")
                            return set(cls)
        except Exception:
            pass
    print(f"[DEBUG] Could not find class_skills for {char_class} on disk.")
    return set()

def extract_class_skills_for_pdf(char_class, class_skills_data):
    if isinstance(class_skills_data, dict):
        cd = class_skills_data.get(char_class)
        if isinstance(cd, dict):
            feats = cd.get("features") or cd.get("Features")
            if isinstance(feats, dict):
                cls = feats.get("class_skills")
                if isinstance(cls, list):
                    return set(cls)
    if isinstance(class_skills_data, list):
        for entry in class_skills_data:
            if isinstance(entry, dict) and char_class in entry and isinstance(entry[char_class], dict):
                feats = entry[char_class].get("features") or entry[char_class].get("Features")
                if isinstance(feats, dict):
                    cls = feats.get("class_skills")
                    if isinstance(cls, list):
                        return set(cls)
    return _load_class_skills_from_disk(char_class)

# ============================================================
#               CHECKBOX NAME RESOLUTION
# ============================================================

def _norm(s):
    s = s.lower().strip()
    s = s.replace("’", "'")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

PDF_SKILL_ALIASES = {
    "disable device": ["Open Lock"],
    "sleight of hand": ["Slight of Hand"],  # common template misspelling
}

def _collect_pdf_field_names(writer):
    field_map = {}
    for page in writer.pages:
        if "/Annots" in page:
            for annot in page["/Annots"]:
                obj = annot.get_object()
                if obj.get("/Subtype") == "/Widget" and obj.get("/T"):
                    key = obj.get("/T").strip("()")
                    field_map[_norm(key)] = key
    return field_map

def _resolve_checkbox_field(skill_name, pdf_fields_norm_map):
    candidates = [skill_name]
    aliases = PDF_SKILL_ALIASES.get(skill_name.lower())
    if aliases:
        candidates.extend(aliases)
    for cand in candidates:
        key = pdf_fields_norm_map.get(_norm(cand))
        if key:
            return key
    return None

def _set_checkbox_checked(obj):
    on_state = NameObject("/Yes")
    try:
        ap = obj.get("/AP")
        if ap and "/N" in ap:
            normal = ap["/N"]
            states = list(normal.keys()) if hasattr(normal, "keys") else []
            for s in states:
                try:
                    if str(s) != "/Off":
                        on_state = s
                        break
                except Exception:
                    continue
    except Exception:
        pass
    obj.update({NameObject("/V"): on_state, NameObject("/AS"): on_state})

# ============================================================
#                 INITIATIVE (DEX + FEATS)
# ============================================================

INITIATIVE_FEAT_STATIC = {
    "improved initiative": 4,
}

def _parse_initiative_bonus_from_summary(summary: str) -> int:
    if not summary:
        return 0
    bonus = 0
    text = summary.lower()
    for m in re.finditer(r'([+-]?\d+)\s*(?:\w+\s*){0,4}initiative', text):
        try:
            bonus += int(m.group(1))
        except Exception:
            continue
    return bonus

def compute_initiative_parts(character, feat_index):
    dex_mod = int(character.abilityScores.get("DEX", {}).get("mod", 0))
    misc = 0
    for feat in getattr(character, "feats", []):
        if isinstance(feat, dict):
            name = str(feat.get("feat", feat.get("name", ""))).strip()
        else:
            name = str(feat).strip()
        lname = name.lower()
        if feat_index and lname in feat_index:
            summary = feat_index[lname].get("summary", "")
            misc += _parse_initiative_bonus_from_summary(summary)
            continue
        if lname in INITIATIVE_FEAT_STATIC:
            misc += INITIATIVE_FEAT_STATIC[lname]
    total = dex_mod + misc
    return total, dex_mod, misc

# ============================================================
#                        PDF FILL
# ============================================================

def prepare_languages_for_pdf(languages_list):
    """Formats languages into three lines for the PDF layout."""
    lines = ["", "", ""]
    line_char_limit = 76
    current_line = 0
    for lang in languages_list:
        if len(lines[current_line]) + len(lang) + 2 <= line_char_limit:
            if lines[current_line]:
                lines[current_line] += ", "
            lines[current_line] += lang
        else:
            current_line += 1
            if current_line < len(lines):
                lines[current_line] = lang
            else:
                lines[2] += ", " + lang
    return {"Language_1": lines[0], "Language_2": lines[1], "Language_3": lines[2]}

def fill_pdf(character, template_pdf, out_pdf, class_skills_data):
    """Fills the Pathfinder character sheet PDF with character data."""
    try:
        print(f"[DEBUG] fill_pdf(template='{template_pdf}', out='{out_pdf}')", flush=True)

        # Be tolerant of quirky/flagged PDFs
        reader = PdfReader(template_pdf, strict=False)
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
                print("[DEBUG] Template was encrypted; attempted blank decrypt.", flush=True)
            except Exception as _e_dec:
                print(f"[DEBUG] Decrypt attempt failed (may be fine): {_e_dec}", flush=True)

        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)

        # Map of available PDF field names (normalized)
        pdf_fields_norm_map = _collect_pdf_field_names(writer)
        print(f"[DEBUG] Found {len(pdf_fields_norm_map)} PDF fields (normalized).")

        # --- BASIC INFO ---
        field_map = {
            "1": character.name,
            "2": f"{character.char_class} {character.level}",
            "Race": character.race,
            "Alignment": character.alignment,
            "Gender": character.gender,
            "bab": character.iterative_attacks,
            "BaseAttack": str(character.bab),
            "hit points": str(character.hitPoints),
        }
        field_map.update(prepare_languages_for_pdf(character.languages))

        # --- ABILITY SCORES ---
        for st in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
            field_map[st.lower()] = str(character.abilityScores[st]["score"])
            field_map[st[0].lower() + "mod"] = f"{character.abilityScores[st]['mod']:+}"
        field_map["chamod"] = f"{character.abilityScores['CHA']['mod']:+}"

        # --- INITIATIVE (Total, Dex mod, Misc from feats via re-merged feat index) ---
        feat_index = load_or_build_feat_index()
        init_total, init_mod, init_misc = compute_initiative_parts(character, feat_index)
        field_map["INITIATIVE"] = f"{init_total:+}"
        field_map["initiative mod"] = f"{init_mod:+}"
        field_map["initiative misc"] = f"{init_misc:+}"

        # --- SPECIAL ABILITIES LINES: clear all first ---
        for i in range(1, 22):
            field_map[f"SPECIAL ABILITIES {i}"] = ""

        # --- PROFICIENCIES: each on its own field (as requested) ---
        weapons, armor, shields = extract_proficiencies_for_pdf(character.char_class, class_skills_data)
        sa_slot = 1
        if weapons:
            field_map[f"SPECIAL ABILITIES {sa_slot}"] = f"Weapons: {', '.join(weapons)}"
            sa_slot += 1
        if armor:
            field_map[f"SPECIAL ABILITIES {sa_slot}"] = f"Armor: {', '.join(armor)}"
            sa_slot += 1
        if shields:
            field_map[f"SPECIAL ABILITIES {sa_slot}"] = f"Shields: {', '.join(shields)}"
            sa_slot += 1

        # --- CLASS FEATURES up to level (names only), 2 per field, starting after prof slots ---
        feature_lines = []
        levels = extract_levels_for_pdf(character.char_class, class_skills_data)
        max_lvl = int(getattr(character, "level", 1) or 1)
        if isinstance(levels, dict):
            for lvl_str, feats in sorted(levels.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 999):
                try:
                    lvl = int(lvl_str)
                except Exception:
                    continue
                if lvl > max_lvl:
                    break
                if isinstance(feats, list):
                    for feat_entry in feats:
                        if isinstance(feat_entry, dict):
                            nm = _clean_name_only(feat_entry.get("name", ""))
                        else:
                            nm = _clean_name_only(feat_entry)
                        if nm:
                            feature_lines.append(f"Lvl {lvl_str}: {nm}")

        print(f"\n[DEBUG] Extracted {len(feature_lines)} class ability lines for {character.char_class} (starting at SA slot {sa_slot}).")
        for ln in feature_lines[:10]:
            print("  ", ln)
        if len(feature_lines) > 10:
            print("  ...")

        grouped_features = []
        for i in range(0, len(feature_lines), 2):
            grouped_features.append(", ".join(feature_lines[i:i + 2]))

        for offset, text in enumerate(grouped_features, start=0):
            slot = sa_slot + offset
            if slot <= 21:
                field_map[f"SPECIAL ABILITIES {slot}"] = text

        # --- FEATS (names only, 3 per line); overflow to SPECIAL ABILITIES 16–21 if empty ---
        clean_feats = []
        for f in character.feats:
            if isinstance(f, dict):
                nm = f.get("feat", f.get("name", ""))
                nm = str(nm).strip()
                if nm:
                    clean_feats.append(nm)
            elif isinstance(f, str):
                nm = f.split("(")[0].strip()
                if nm:
                    clean_feats.append(nm)

        grouped_feats = []
        for i in range(0, len(clean_feats), 3):
            grouped_feats.append(", ".join(clean_feats[i:i + 3]))

        for i, line_text in enumerate(grouped_feats[:12]):
            field_map[f"FEATS {i + 1}"] = line_text

        overflow_feats = grouped_feats[12:18]
        for idx, feat_string in enumerate(overflow_feats, start=16):
            if idx <= 21:
                key = f"SPECIAL ABILITIES {idx}"
                if not field_map.get(key):  # only fill if still empty
                    field_map[key] = f"(Feat) {feat_string}"

        # === CLASS-SKILL CHECKBOXES & SKILL VALUES ===

        cls_sk = extract_class_skills_for_pdf(character.char_class, class_skills_data)
        cls_sk_norm = set()
        for s in cls_sk:
            if s.lower().startswith("knowledge "):
                s = s.replace(" (", ":").replace(")", "")
            cls_sk_norm.add(re.sub(r"[^a-z0-9]+", "", s.lower()))

        def _pdf_is_class_skill(skill_name: str) -> bool:
            def _n(s: str) -> str:
                s = s.lower().strip()
                s = s.replace("knowledge (", "knowledge:").replace(")", "")
                return re.sub(r"[^a-z0-9]+", "", s)
            n = _n(skill_name)
            if n in cls_sk_norm:
                return True
            if skill_name in craft_subskills and _n("Craft") in cls_sk_norm:
                return True
            if skill_name in perform_subskills and _n("Perform") in cls_sk_norm:
                return True
            if skill_name in profession_subskills and _n("Profession") in cls_sk_norm:
                return True
            return False

        def get_skill_info(skill_name):
            info = character.skillBonuses.get(skill_name, {})
            ranks = int(info.get("ranks", 0))
            mod = int(info.get("ability_mod", 0))
            clsb = int(info.get("class_skill_bonus", 0))
            if ranks > 0 and clsb == 0 and _pdf_is_class_skill(skill_name):
                clsb = 3
            total = ranks + mod + clsb
            return {"ranks": ranks, "mod": mod, "class": clsb, "total": total}

        # Subskills
        subs = getattr(character, "chosen_subskills", {})
        if not subs or not any(subs.values()):
            subs = {"Craft": [], "Perform": [], "Profession": []}
            for sk in character.skillBonuses:
                if sk in craft_subskills and len(subs["Craft"]) < 3:
                    subs["Craft"].append(sk)
                elif sk in perform_subskills and len(subs["Perform"]) < 2:
                    subs["Perform"].append(sk)
                elif sk in profession_subskills and len(subs["Profession"]) < 2:
                    subs["Profession"].append(sk)

        for i, sub in enumerate(subs.get("Craft", [])[:3], start=1):
            data = get_skill_info(sub)
            field_map[f"craft{i}_name"] = sub
            field_map[f"craft{i}_mod"] = f"{data['mod']:+}"
            field_map[f"craft{i}_rank"] = str(data["ranks"])
            field_map[f"craft{i}_class"] = str(data["class"])
            field_map[f"craft{i}_tot"] = str(data["total"])

        for i, sub in enumerate(subs.get("Perform", [])[:2], start=1):
            data = get_skill_info(sub)
            field_map[f"perform{i}_name"] = sub
            field_map[f"perform{i}_mod"] = f"{data['mod']:+}"
            field_map[f"perform{i}_rank"] = str(data["ranks"])
            field_map[f"perform{i}_class"] = str(data["class"])
            field_map[f"perform{i}_tot"] = str(data["total"])

        for i, sub in enumerate(subs.get("Profession", [])[:2], start=1):
            data = get_skill_info(sub)
            field_map[f"profession{i}_name"] = sub
            field_map[f"profession{i}_mod"] = f"{data['mod']:+}"
            field_map[f"profession{i}_rank"] = str(data["ranks"])
            field_map[f"profession{i}_class"] = str(data["class"])
            field_map[f"profession{i}_tot"] = str(data["total"])

        # Standard skills
        for sk in character.skillBonuses.keys():
            if sk in craft_subskills or sk in perform_subskills or sk in profession_subskills:
                continue
            short = skill_short_prefix.get(sk)
            if not short:
                continue
            data = get_skill_info(sk)
            field_map[f"{short}tot"] = str(data["total"])
            field_map[f"{short}rank"] = str(data["ranks"])
            abil = skill_to_ability.get(sk, "INT").lower()
            field_map[f"{short}{abil}"] = f"{data['mod']:+}"
            field_map[f"{short}class"] = f"{data['class']:+}"

        # --- CHECKBOXES ---
        checkbox_map = {}
        unmatched = []
        for skill_name in cls_sk:
            if skill_name in ("Craft", "Perform", "Profession"):
                continue
            resolved = _resolve_checkbox_field(skill_name, pdf_fields_norm_map)
            if resolved:
                checkbox_map[resolved] = True
            else:
                unmatched.append(skill_name)

        def mark_if_exists(name):
            nkey = _norm(name)
            real = pdf_fields_norm_map.get(nkey)
            if real:
                checkbox_map[real] = True

        if "Craft" in cls_sk:
            for box in ("Craft_1", "Craft_2", "Craft_3"):
                mark_if_exists(box)
        if "Perform" in cls_sk:
            for box in ("Perform", "Perform_2"):
                mark_if_exists(box)
        if "Profession" in cls_sk:
            for box in ("Profession", "Profession_2"):
                mark_if_exists(box)

        if unmatched:
            print("[DEBUG] Could not resolve PDF checkbox fields for:", unmatched)

        # --- WRITE TO PDF ---
        for page in writer.pages:
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    obj = annot.get_object()
                    if obj.get("/Subtype") == "/Widget" and obj.get("/T"):
                        key = obj.get("/T").strip("()")
                        obj.update({NameObject("/DA"): TextStringObject("/Helv 0 Tf 0 g")})
                        if key in field_map:
                            val = TextStringObject(str(field_map[key]))
                            obj.update({NameObject("/V"): val, NameObject("/DV"): val})
                        elif key in checkbox_map and checkbox_map[key]:
                            _set_checkbox_checked(obj)

        if "/AcroForm" not in writer._root_object:
            writer._root_object.update({NameObject("/AcroForm"): DictionaryObject()})
        writer._root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})

        try:
            with open(out_pdf, "wb") as f:
                writer.write(f)
            print(f"[DEBUG] Wrote PDF → {out_pdf}", flush=True)
        except PermissionError:
            print("!!! PDF ERROR: Permission denied writing output. "
                  "Close the PDF if it’s open in a viewer and try again.", flush=True)
        except FileNotFoundError:
            print("!!! PDF ERROR: Output path not found. Check folder permissions/exists.", flush=True)

    except FileNotFoundError:
        print(f"!!! PDF ERROR: Template file not found at '{template_pdf}'")
    except Exception as e:
        print(f"!!! AN UNEXPECTED PDF ERROR OCCURRED: {e}")

# ============================================================
#                         TXT EXPORT
# ============================================================

def save_text(character, txt_path):
    """Generates text export of all stats."""
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Name: {character.name}\n")
            f.write(f"Class & Level: {character.char_class} {character.level}\n")
            f.write(f"Race: {character.race}\nGender: {character.gender}\nAlignment: {character.alignment}\n")
            f.write(f"HP: {character.hitPoints}\nBAB: {character.bab} ({character.iterative_attacks})\n\n")

            f.write("Ability Scores:\n")
            for st in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
                s = character.abilityScores[st]
                f.write(f"  {st}: {s['score']} ({s['mod']:+})\n")

            feat_index = load_or_build_feat_index()
            itot, imod, imisc = compute_initiative_parts(character, feat_index)
            f.write(f"\nInitiative: {itot:+} (Dex {imod:+}, Misc {imisc:+})\n")

            f.write("\nLanguages: " + ", ".join(character.languages) + "\n")

            f.write("\nFeatures & Abilities:\n")
            for item in character.features_and_abilities:
                f.write(f"  {item}\n")

            f.write("\nFeats:\n")
            for item in character.feats:
                f.write(f"  {item}\n")

            f.write("\nSkills:\n")
            chosen_crafts = set(character.chosen_subskills.get("Craft", []))
            chosen_performs = set(character.chosen_subskills.get("Perform", []))
            chosen_professions = set(character.chosen_subskills.get("Profession", []))

            standard_skills, craft_skills, perform_skills, profession_skills = [], [], [], []
            for sk, info in sorted(character.skillBonuses.items()):
                if sk in craft_subskills:
                    if sk in chosen_crafts:
                        craft_skills.append((sk, info))
                    continue
                if sk in perform_subskills:
                    if sk in chosen_performs:
                        perform_skills.append((sk, info))
                    continue
                if sk in profession_subskills:
                    if sk in chosen_professions:
                        profession_skills.append((sk, info))
                    continue
                standard_skills.append((sk, info))

            def _fmt(info):
                return f"Total {info['total']:+} (Ranks:{info['ranks']}, Mod:{info['ability_mod']:+}, Class:{info['class_skill_bonus']})"

            for sk, info in standard_skills:
                f.write(f"  {sk}: {_fmt(info)}\n")

            if craft_skills:
                f.write("\n  -- Craft Skills --\n")
                for sk, info in craft_skills:
                    f.write(f"    {sk}: {_fmt(info)}\n")

            if perform_skills:
                f.write("\n  -- Perform Skills --\n")
                for sk, info in perform_skills:
                    f.write(f"    {sk}: {_fmt(info)}\n")

            if profession_skills:
                f.write("\n  -- Profession Skills --\n")
                for sk, info in profession_skills:
                    f.write(f"    {sk}: {_fmt(info)}\n")

    except Exception as e:
        print(f"!!! AN UNEXPECTED TXT ERROR OCCURRED: {e}")
