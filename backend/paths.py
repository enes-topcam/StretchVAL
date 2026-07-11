"""Ortak yol yardimcilari (tek kaynak) - kaynak/paketlenmis fark etmez."""

from __future__ import annotations

import os
import sys

from .constants import APP_NAME


def _project_root() -> str:
    # backend/paths.py -> bir ust klasor = proje koku
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(rel: str) -> str:
    """UI gibi paket-ici dosyalar. PyInstaller'da _MEIPASS, kaynakta proje koku."""
    base = getattr(sys, "_MEIPASS", _project_root())
    return os.path.join(base, rel)


def data_dir() -> str:
    """Kullanici verisi (profiller/tercihler/log) -> %APPDATA%/<APP_NAME> (olustur)."""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d
