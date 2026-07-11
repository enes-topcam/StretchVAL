"""
Api - JS <-> Python koprusu.

Frontend 'window.pywebview.api.<metot>' ile buradaki metotlari cagirir.
Hepsi JSON'a serilestirilebilir deger dondurur. Gercek isi backend
modullerine devreder (display / valorant / profiles).
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from . import display
from . import valorant
from . import profiles
from . import prefs
from .log import log
from .constants import WINDOW_TITLE


def _bring_window_to_front(title: str) -> bool:
    """Saf Win32 ile pencereyi one getirir (pywebview nesnesine dokunmaz -> thread-guvenli)."""
    try:
        u = ctypes.windll.user32
        u.FindWindowW.restype = wintypes.HWND
        u.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        hwnd = u.FindWindowW(None, title)
        if not hwnd:
            return False
        u.ShowWindow(hwnd, 9)  # SW_RESTORE (simgeden geri getir)
        # Kisa sureligine en uste al, sonra birak -> odak lock'unu asar, kalici topmost olmaz
        u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_uint]
        SWP = 0x0001 | 0x0002 | 0x0040  # NOSIZE | NOMOVE | SHOWWINDOW
        u.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, SWP)  # HWND_TOPMOST
        u.SetWindowPos(hwnd, wintypes.HWND(-2), 0, 0, 0, 0, SWP)  # HWND_NOTOPMOST
        u.SetForegroundWindow.argtypes = [wintypes.HWND]
        u.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


class Api:
    def __init__(self):
        # Uygulama acildiginda her monitorun orijinal (native) modunu sakla ->
        # "geri al" bunu kullanir.
        self._original: dict[str, dict] = {}
        self._window = None

    def set_window(self, window):
        self._window = window

    def bring_to_front(self) -> bool:
        return _bring_window_to_front(WINDOW_TITLE)

    # ---- Monitor / cozunurluk ----
    def get_monitors(self) -> list:
        mons = display.list_monitors()
        result = [display.monitor_to_dict(m) for m in mons]
        # Ilk okumada orijinal modlari kaydet (henuz kaydedilmemis olanlari)
        for m in result:
            if m["device_name"] not in self._original:
                self._original[m["device_name"]] = dict(m["current"])
        log(f"get_monitors: {len(result)} monitor")
        return result

    def apply_resolution(self, device_name: str, width: int, height: int,
                         refresh: int | None) -> dict:
        ok, msg = display.change_resolution(
            device_name, int(width), int(height),
            int(refresh) if refresh else None
        )
        return {"ok": ok, "message": msg}

    def test_resolution(self, device_name: str, width: int, height: int,
                        refresh: int | None) -> dict:
        ok, msg = display.change_resolution(
            device_name, int(width), int(height),
            int(refresh) if refresh else None, test_only=True
        )
        return {"ok": ok, "message": msg}

    def revert(self, device_name: str) -> dict:
        orig = self._original.get(device_name)
        if not orig:
            return {"ok": False, "message": "Bu monitor icin kayitli orijinal mod yok"}
        ok, msg = display.change_resolution(
            device_name, orig["width"], orig["height"], orig["refresh"]
        )
        return {"ok": ok, "message": msg}

    def revert_all(self) -> dict:
        results = []
        for device_name, orig in self._original.items():
            ok, msg = display.change_resolution(
                device_name, orig["width"], orig["height"], orig["refresh"]
            )
            results.append({"device": device_name, "ok": ok, "message": msg})
        all_ok = all(r["ok"] for r in results) if results else False
        return {"ok": all_ok, "results": results}

    def get_originals(self) -> dict:
        return self._original

    # ---- Valorant true-stretched ini islemleri ----
    def is_game_running(self) -> bool:
        return valorant.is_game_running()

    def apply_valorant(self, width: int, height: int, puuid: str | None = None) -> dict:
        return valorant.apply_stretched(int(width), int(height), puuid or None)

    # ---- Profiller ----
    def get_profiles(self) -> dict:
        cfg = valorant.config_dir()
        lku = valorant.get_last_known_user(cfg) if cfg else None
        return {"profiles": profiles.load_profiles(), "last_known_user": lku}

    def save_profile(self, nickname: str, puuid: str) -> dict:
        # UI'dan gelen kayit = kullanici ismi acikca verdi -> named=True
        return {"ok": True, "profiles": profiles.add_profile(nickname, puuid, named=True)}

    # ---- Tercihler (son secilen cozunurluk) ----
    def get_prefs(self) -> dict:
        return prefs.load_prefs()

    def set_last_resolution(self, device: str, width: int, height: int,
                            refresh: int | None) -> dict:
        return prefs.set_last_resolution(device, width, height, refresh or 0)

    def delete_profile(self, puuid: str) -> dict:
        return {"ok": True, "profiles": profiles.delete_profile(puuid)}

    # ---- Yeni hesap akisi: Valorant baslat / kapat / aktif hesabi izle ----
    def launch_valorant(self) -> dict:
        return valorant.launch_valorant()

    def kill_valorant_game(self) -> dict:
        return valorant.kill_game()

    def kill_valorant_full(self) -> dict:
        """Oyun + Riot Client'i kapatir (temiz yeniden acilis icin)."""
        return valorant.kill_all()

    def get_current_account(self) -> dict:
        """Anlik LastKnownUser + o hesabin config'i hazir mi (yeni hesap izleme icin)."""
        cfg = valorant.config_dir()
        puuid = valorant.get_last_known_user(cfg) if cfg else None
        return {
            "puuid": puuid,
            "exists": valorant.account_exists(cfg, puuid) if (cfg and puuid) else False,
            "game_running": valorant.is_game_running(),
        }
