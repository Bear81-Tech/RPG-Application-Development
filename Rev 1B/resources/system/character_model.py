# character_model.py
import random
import re
from typing import Dict, Any, List, Tuple

# Note: In a real system, game_data would be imported/passed in or placed here.
# Assuming game_data is in 'resources/system/' relative to the project root.
from .game_data import bab_progressions, stat_priority, class_base_skill_ranks, skill_to_ability, craft_subskills, perform_subskills, profession_subskills

# =========================================================================================
# FIX APPLIED HERE: CONSOLIDATED ALL IMPORTS FROM character_logic TO THE TOP OF THE FILE
# This resolves the ModuleNotFoundError that occurred when the function was called.
# =========================================================================================
from .character_logic import (
    _is_class_skill_name, 
    choose_subskills_for_character, 
    pick_character_feats,
    get_random_ranger_style, 
    _canonicalize_slot_name, 
    option_prereq_ok, 
    FEATURE_TO_CATEGORY_MAP
)
# =========================================================================================

class Character:
    """The core character model containing attributes and calculation logic."""

    def __init__(self, char_class, level, race, gender, alignment, name, 
                 class_abilities_data, master_class_choices, feats_flat):
        
        print(f"[DEBUG] Building character: {char_class} L{level} {race} {gender}", flush=True)
        self.char_class, self.level, self.race, self.gender, self.alignment, self.name = \
            char_class, level, race, gender, alignment, name
        
        # Skill preparation
        self.class_skills_list = class_abilities_data.get(self.char_class, {}).get("features", {}).get("class_skills", [])
        self._class_skills_norm = self._normalize_class_skill_list(self.class_skills_list)
        self.chosen_subskills = choose_subskills_for_character(char_class, race)
        
        # Core Calculations
        self.abilityScores = self._make_ability_scores()
        self.hitPoints = self._calculate_hit_points()
        self.bab, self.iterative_attacks = self._compute_bab_and_iterations()
        self.skillRanks = self._assign_skill_ranks()
        self.skillBonuses = self._compute_skill_bonuses()

        # Features and Feats
        lines, replacements = self._resolve_class_features_with_options(
            self.char_class, self.level, class_abilities_data, master_class_choices
        )
        self.features_and_abilities = lines
        self._feature_replacements = replacements
        
        # Ranger style storage
        if hasattr(self._resolve_class_features_with_options, "_ranger_style_choice"):
            self.combat_style = self._resolve_class_features_with_options._ranger_style_choice[1]
        else:
            self.combat_style = None
        if self.char_class == "Ranger":
            print(f"[DEBUG] Ranger combat style selected: {self.combat_style}", flush=True)
        
        # Feat selection
        self.feats = pick_character_feats(self.level, self.race, feats_flat)

    # --- Utility Methods (Normalized Skill List Fix) ---
    def _normalize_class_skill_list(self, raw: List[str]) -> set:
        """
        Helper for __init__ to normalize class skill names for membership checking.
        Fixes: Handles 'raw' as a list of strings by iterating over it.
        """
        if not raw:
            return set()
            
        normalized_skills = set()
        
        for skill_name in raw:
            if not isinstance(skill_name, str):
                continue

            # Apply normalization steps to the single skill name (string)
            s = skill_name.lower().strip().replace("’", "'").replace("knowledge(", "knowledge:").replace(")", "")
            s = s.replace("knowledge (", "knowledge:")
            s = re.sub(r"\s+", "", s)
            
            # Add the final normalized string to the set
            normalized_skills.add(s)

        return normalized_skills

    # --- Core Calculations (Internal) ---
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
        # Max 1 is PF1e rule to ensure at least 1 rank/level
        ranks_per=max(1,base+mod+(1 if self.race=="Human" else 0)) 
        total=ranks_per*self.level
        ranks={s:0 for s in skill_to_ability}
        # Class skill check uses logic imported from character_logic
        pri=[s for s in ranks if _is_class_skill_name(s,self._class_skills_norm)] 
        pool=pri*2+list(ranks)
        while total>0 and pool:
            s=random.choice(pool);ranks[s]+=1;total-=1
        return ranks

    def _compute_skill_bonuses(self):
        out={}
        for s,r in self.skillRanks.items():
            a=skill_to_ability.get(s,"INT");mod=self.abilityScores[a]["mod"]
            # Class skill check uses logic imported from character_logic
            cls=3 if r>0 and _is_class_skill_name(s,self._class_skills_norm) else 0 
            out[s]={"ranks":r,"ability_mod":mod,"class_skill_bonus":cls,"total":r+mod+cls}
        return out

    # --- Feature Resolver (Updated) ---
    def _resolve_class_features_with_options(self, char_class: str, level: int,
                                        abilities: Dict[str, Any],
                                        master_choices: Dict[str, Any]) -> Tuple[List[str], Dict[int, List[str]]]:
        """Core logic for resolving class features, making random choices, and handling Ranger style."""
        # The import below was REMOVED as part of the fix. All required functions
        # (get_random_ranger_style, _canonicalize_slot_name, etc.) are now imported at the top.
        
        lines, replacements = [], {}
        cls_block = (abilities or {}).get(char_class, {})
        levels = cls_block.get("levels", {})
        chosen_by_category: Dict[str, set] = {}

        for L in range(1, level + 1):
            for feat in levels.get(str(L), []):
                base_name = feat.get("name") if isinstance(feat, dict) else feat
                base_name = base_name or "Unknown Feature"
                slot_key = _canonicalize_slot_name(base_name) # Function imported from character_logic at top
                category = FEATURE_TO_CATEGORY_MAP.get(slot_key) # Variable imported from character_logic at top

                # --- Special case: Ranger combat style ---
                if char_class.lower() == "ranger" and "combat style" in slot_key:
                    # Use a function attribute to store the choice persistently
                    if not hasattr(self._resolve_class_features_with_options, "_ranger_style_choice"):
                        style_key, style_label = get_random_ranger_style() # Function imported from character_logic at top
                        self._resolve_class_features_with_options._ranger_style_choice = (style_key, style_label)
                    else:
                        style_key, style_label = self._resolve_class_features_with_options._ranger_style_choice
                    category = style_key
                    if L == 2:
                        lines.append(f"Lvl 2: Combat Style – {style_label}")
                        replacements.setdefault(L, []).append(f"Combat Style – {style_label}")

                if category and master_choices.get(category):
                    pool = master_choices[category]
                    pool_ok = [opt for opt in pool if option_prereq_ok(opt, char_class, L)] # Function imported from character_logic at top
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
