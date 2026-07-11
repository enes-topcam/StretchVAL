"""
Valorant config yollari ve hesap kesfi.

%LOCALAPPDATA%\\VALORANT\\Saved\\Config yapisi:
  - WindowsClient\\RiotLocalMachine.ini   -> LastKnownUser (son giris yapilan PUUID)
  - WindowsClient\\GameUserSettings.ini    -> genel sablon
  - <PUUID>-<bolge>\\WindowsClient\\GameUserSettings.ini -> hesaba ozel
"""

from __future__ import annotations

import os
import re
import glob


def config_dir() -> str | None:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    p = os.path.join(local, "VALORANT", "Saved", "Config")
    return p if os.path.isdir(p) else None


def get_last_known_user(cfg: str) -> str | None:
    """RiotLocalMachine.ini -> [UserInfo] LastKnownUser=<puuid>"""
    rlm = os.path.join(cfg, "WindowsClient", "RiotLocalMachine.ini")
    if not os.path.isfile(rlm):
        return None
    with open(rlm, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = re.match(r"\s*LastKnownUser\s*=\s*(\S+)", line)
            if m:
                return m.group(1).strip()
    return None


def account_files(cfg: str, puuid: str) -> list:
    """Belirli bir PUUID'nin hesap dosyalari (klasor bolge sonekli olabilir: <puuid>-eu)."""
    files: list[str] = []
    for d in glob.glob(os.path.join(cfg, puuid + "*")):
        f = os.path.join(d, "WindowsClient", "GameUserSettings.ini")
        if os.path.isfile(f) and f not in files:
            files.append(f)
    return files


def target_files(cfg: str) -> tuple:
    """
    Varsayilan mod hedefleri: (genel sablon) + (son giris yapilan hesabin dosyalari).
    Donen: (files, last_known_user_puuid)
    """
    files: list[str] = []
    general = os.path.join(cfg, "WindowsClient", "GameUserSettings.ini")
    if os.path.isfile(general):
        files.append(general)

    puuid = get_last_known_user(cfg)
    if puuid:
        for f in account_files(cfg, puuid):
            if f not in files:
                files.append(f)
    return files, puuid


def account_exists(cfg: str, puuid: str) -> bool:
    """Bu PUUID'nin duzenlenebilir GameUserSettings.ini'si var mi?"""
    return bool(cfg and puuid and account_files(cfg, puuid))
