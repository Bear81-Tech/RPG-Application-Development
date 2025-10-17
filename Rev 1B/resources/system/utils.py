# utils.py
import os
import re
import json
import random

def choose(lst):
    """Select a random item from a list, or return an empty string if the list is empty."""
    return random.choice(lst) if lst else ""

def sanitize_filename(s):
    """Remove characters from a string that are invalid for filenames."""
    return re.sub(r'[<>:"/\\|?*]', "", s).strip().replace(" ", "_")

def ensure_dir(path):
    """Make sure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def load_json(path):
    """Load a JSON file with error handling."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{path}'")
        return {}
    except Exception as e:
        print(f"Error loading JSON from '{path}': {e}")
        return {}