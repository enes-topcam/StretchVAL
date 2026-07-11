"""
Valorant surec yonetimi: oyunu baslat / kapat / calisiyor mu.

Not: Sadece OYUN surecini (VALORANT-Win64-Shipping.exe) yonetiriz.
RiotClientServices'i oldurmuyoruz ki oturum kalsin ve yeniden acilis hizli olsun.
"""

from __future__ import annotations

import os
import json
import subprocess

from ..log import log

CREATE_NO_WINDOW = 0x08000000    # subprocess konsol penceresi acmasin
DETACHED_PROCESS = 0x00000008    # baslattigimiz oyun bize bagli kalmasin

GAME_PROCS = ["VALORANT-Win64-Shipping.exe", "VALORANT.exe"]
# Riot Client surecleri (temiz "soguk" yeniden acilis icin hepsini kapatiriz)
RIOT_PROCS = ["RiotClientServices.exe", "RiotClientUx.exe",
              "RiotClientUxRender.exe", "RiotClientCrashHandler.exe"]


def is_game_running() -> bool:
    """Sadece OYUN sureci acik mi? ini'yi cikista o geri yazar.
    Riot Client'in acik olmasi sorun degil (oyun baslarken config'i okur)."""
    try:
        for name in GAME_PROCS:
            out = subprocess.run(
                ["tasklist", "/fi", f"imagename eq {name}", "/nh"],
                capture_output=True, text=True, creationflags=CREATE_NO_WINDOW,
            )
            if name.lower() in (out.stdout or "").lower():
                return True
    except Exception:
        pass
    return False


def riot_client_path() -> str | None:
    """RiotClientServices.exe yolunu resmi kayittan (RiotClientInstalls.json) cozer."""
    candidates: list[str] = []
    pd = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    reg = os.path.join(pd, "Riot Games", "RiotClientInstalls.json")
    if os.path.isfile(reg):
        try:
            with open(reg, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key in ("rc_live", "rc_default"):
                v = data.get(key)
                if v:
                    candidates.append(v)
        except Exception:
            pass
    candidates.append(r"C:\Riot Games\Riot Client\RiotClientServices.exe")
    for c in candidates:
        c = c.replace("/", os.sep)
        if os.path.isfile(c):
            return c
    return None


def launch_valorant() -> dict:
    """Valorant'i Riot Client uzerinden baslatir (RiotClientServices --launch-product).
    Riot Client'i once kapattigimiz icin bu soguk baslatma yapar."""
    rc = riot_client_path()
    if not rc:
        log("launch_valorant: RiotClientServices bulunamadi")
        return {"ok": False, "message": "RiotClientServices.exe bulunamadı"}
    try:
        subprocess.Popen(
            [rc, "--launch-product=valorant", "--launch-patchline=live"],
            creationflags=DETACHED_PROCESS, close_fds=True,
        )
        log(f"launch_valorant: RiotClientServices -> {rc}")
        return {"ok": True, "method": "RiotClientServices"}
    except Exception as e:
        log(f"launch_valorant: HATA -> {e}")
        return {"ok": False, "message": str(e)}


def _taskkill(names: list) -> list:
    killed = []
    for name in names:
        try:
            r = subprocess.run(
                ["taskkill", "/F", "/IM", name],
                capture_output=True, text=True, creationflags=CREATE_NO_WINDOW,
            )
            if r.returncode == 0:
                killed.append(name)
        except Exception:
            pass
    return killed


def kill_game() -> dict:
    """Sadece OYUN surecini kapatir (RiotClient acik/oturum kalir)."""
    killed = _taskkill(GAME_PROCS)
    log(f"kill_game: kapatilanlar={killed}")
    return {"ok": True, "killed": killed}


def kill_all() -> dict:
    """Oyun + Riot Client'i kapatir -> sonraki acilis temiz (soguk) baslar,
    boylece Riot 'oyun hala calisiyor' sanip launch'i yok saymaz."""
    game = _taskkill(GAME_PROCS)
    riot = _taskkill(RIOT_PROCS)
    log(f"kill_all: game={game} riot={riot}")
    return {"ok": True, "game": game, "riot": riot}
