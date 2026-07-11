"""
Kayitli Valorant hesap profilleri.

Her profil: {"nickname": "...", "puuid": "<puuid>", "named": true/false}
%APPDATA%\\StretchVAL\\profiles.json icinde saklanir.

Amaç: farkli hesaplara stretched uygulayabilmek. Kullanici bir profil secip
Uygula derse, LastKnownUser yerine o profilin PUUID klasorune yazariz.
"""

from __future__ import annotations

import os
import json

from .paths import data_dir


def profiles_path() -> str:
    return os.path.join(data_dir(), "profiles.json")


def load_profiles() -> list:
    p = profiles_path()
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            out = []
            for x in data:
                if isinstance(x, dict) and x.get("puuid"):
                    x.setdefault("named", True)  # eski kayitlar isimlendirilmis sayilir
                    out.append(x)
            return out
    except Exception:
        pass
    return []


def save_profiles(profiles: list) -> None:
    with open(profiles_path(), "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def add_profile(nickname: str, puuid: str, named: bool = True) -> list:
    """Ayni PUUID varsa takma adini gunceller, yoksa ekler.
    named=True -> kullanici ismi acikca verdi (artik isim popup'i cikmaz)."""
    nickname = (nickname or "").strip() or puuid
    profiles = load_profiles()
    for pr in profiles:
        if pr.get("puuid") == puuid:
            pr["nickname"] = nickname
            pr["named"] = bool(named)
            save_profiles(profiles)
            return profiles
    profiles.append({"nickname": nickname, "puuid": puuid, "named": bool(named)})
    save_profiles(profiles)
    return profiles


def delete_profile(puuid: str) -> list:
    profiles = [p for p in load_profiles() if p.get("puuid") != puuid]
    save_profiles(profiles)
    return profiles
