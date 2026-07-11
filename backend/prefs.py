"""
Kullanici tercihleri -> %APPDATA%/StretchVAL/prefs.json
Simdilik: en son secilen cozunurluk (uygulama tekrar acilinca otomatik secilsin).
"""

from __future__ import annotations

import os
import json

from .paths import data_dir


def _path() -> str:
    return os.path.join(data_dir(), "prefs.json")


def load_prefs() -> dict:
    p = _path()
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_prefs(prefs: dict) -> dict:
    cur = load_prefs()
    cur.update(prefs or {})
    try:
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return cur


def set_last_resolution(device: str, width: int, height: int, refresh: int) -> dict:
    return save_prefs({"last_resolution": {
        "device": device, "width": int(width), "height": int(height),
        "refresh": int(refresh) if refresh else None,
    }})
