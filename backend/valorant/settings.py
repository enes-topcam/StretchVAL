"""
GameUserSettings.ini duzenleme -> true stretched.

Bolum-farkinda editor: [/Script/ShooterGame.ShooterGameUserSettings] bolumundeki
anahtarlari gunceller, eksikleri o bolumun sonuna ekler. Idempotenttir; zaten
dogru olan degerlere dokunmaz. Duzenlemeden once oyunun kapali oldugunu kontrol eder.
"""

from __future__ import annotations

import re

from . import config
from . import process

# Ilgili anahtarlarin bulundugu bolum
SECTION = "[/Script/ShooterGame.ShooterGameUserSettings]"

# Cozunurlukten bagimsiz sabit anahtarlar
DESIRED_STATIC = {
    "bShouldLetterbox": "False",
    "bLastConfirmedShouldLetterbox": "False",
    "bUseVSync": "False",
    "bUseDynamicResolution": "False",
    "LastConfirmedFullscreenMode": "2",
    "PreferredFullscreenMode": "2",
    "FullscreenMode": "2",
}
# Genislik (X) / Yukseklik (Y) alan gruplari
WIDTH_KEYS = ("ResolutionSizeX", "LastUserConfirmedResolutionSizeX",
              "DesiredScreenWidth", "LastUserConfirmedDesiredScreenWidth")
HEIGHT_KEYS = ("ResolutionSizeY", "LastUserConfirmedResolutionSizeY",
               "DesiredScreenHeight", "LastUserConfirmedDesiredScreenHeight")

# Bolumun sonuna eklenirken anlamli sira
KEY_ORDER = [
    "bShouldLetterbox", "bLastConfirmedShouldLetterbox",
    "bUseVSync", "bUseDynamicResolution",
    "ResolutionSizeX", "ResolutionSizeY",
    "LastUserConfirmedResolutionSizeX", "LastUserConfirmedResolutionSizeY",
    "DesiredScreenWidth", "DesiredScreenHeight",
    "LastUserConfirmedDesiredScreenWidth", "LastUserConfirmedDesiredScreenHeight",
    "LastConfirmedFullscreenMode", "PreferredFullscreenMode", "FullscreenMode",
]


def _desired(width: int, height: int) -> dict:
    d = dict(DESIRED_STATIC)
    for k in WIDTH_KEYS:
        d[k] = str(width)
    for k in HEIGHT_KEYS:
        d[k] = str(height)
    return d


def _key_of(line: str) -> str | None:
    m = re.match(r"\s*([A-Za-z0-9_]+)\s*=", line)
    return m.group(1) if m else None


def _edit_file(path: str, desired: dict) -> dict:
    """
    Bir GameUserSettings.ini dosyasini bolum-farkinda duzenler.
    Donen: {"changed": bool, "changed_keys": [...]}
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(newline)

    # ShooterGame bolumunun sinirlarini bul
    start = None
    for i, line in enumerate(lines):
        if line.strip() == SECTION:
            start = i
            break

    changed_keys: list[str] = []
    remaining = dict(desired)  # henuz yazilmamis anahtarlar

    if start is None:
        # Bolum yoksa dosyanin sonuna komple ekle
        block = [SECTION] + [f"{k}={desired[k]}" for k in KEY_ORDER if k in desired]
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.extend(block)
        changed_keys = list(desired.keys())
    else:
        # Bolumun sonu: sonraki [..] baslik veya dosya sonu
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].lstrip().startswith("["):
                end = j
                break

        # Mevcut satirlari guncelle
        for j in range(start + 1, end):
            key = _key_of(lines[j])
            if key and key in remaining:
                new_val = remaining.pop(key)
                cur_val = lines[j].split("=", 1)[1].strip()
                if cur_val != new_val:
                    lines[j] = f"{key}={new_val}"
                    changed_keys.append(key)

        # Eksik anahtarlari bolumun sonundaki bos satirdan once ekle
        if remaining:
            insert_at = end
            while insert_at - 1 > start and lines[insert_at - 1].strip() == "":
                insert_at -= 1
            add = [f"{k}={remaining[k]}" for k in KEY_ORDER if k in remaining]
            add += [f"{k}={v}" for k, v in remaining.items() if k not in KEY_ORDER]
            lines[insert_at:insert_at] = add
            changed_keys.extend(k for k in remaining)

    if not changed_keys:
        return {"changed": False, "changed_keys": []}

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(newline.join(lines))

    return {"changed": True, "changed_keys": changed_keys}


def apply_stretched(width: int, height: int, puuid: str | None = None) -> dict:
    """
    Stretched ayarlarini GameUserSettings.ini dosyalarina yazar.

    puuid verilirse: SADECE o hesabin klasorune yazar (profil modu).
    puuid None ise:  genel sablon + son giris yapilan hesap (varsayilan).

    Donen ozet: {ok, code?, message?, changed, count, puuid, files:[...]}
    """
    cfg = config.config_dir()
    if not cfg:
        return {"ok": False, "code": "no_config",
                "message": "VALORANT config klasörü bulunamadı (Valorant kurulu mu?)"}

    if process.is_game_running():
        return {"ok": False, "code": "game_running",
                "message": "Valorant açık. Önce oyunu tamamen kapat."}

    if puuid:
        files = config.account_files(cfg, puuid)
    else:
        files, puuid = config.target_files(cfg)
    if not files:
        return {"ok": False, "code": "no_files",
                "message": "Düzenlenecek GameUserSettings.ini bulunamadı."}

    desired = _desired(int(width), int(height))
    results = []
    any_changed = False
    for f in files:
        try:
            r = _edit_file(f, desired)
            results.append({"file": f, **r})
            any_changed = any_changed or r["changed"]
        except Exception as e:
            results.append({"file": f, "changed": False, "error": str(e)})

    return {
        "ok": True,
        "changed": any_changed,
        "count": len(files),
        "puuid": puuid,
        "files": results,
    }
