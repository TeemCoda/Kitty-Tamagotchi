"""config.py — Load and save settings to AppData/Roaming/DesktopCat/config.json."""

import json
import os
from pathlib import Path

CONFIG_DIR  = Path(os.environ.get("APPDATA", ".")) / "DesktopCat"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "costume": "orange",
    "corner":  "bottom-right",
    "scale":   4,
    "phrase_interval_minutes": 15,
    "show_hud": True,
    "mood": {
        "happiness": 80.0,
        "hunger":    20.0,
        "energy":    90.0,
    },
}


def load() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for k, v in DEFAULTS.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return DEFAULTS.copy()


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
