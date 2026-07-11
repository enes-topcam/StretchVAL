"""Basit dosya logu -> %APPDATA%/StretchVAL/app.log (tani icin)."""

from __future__ import annotations

import os
import datetime

from .paths import data_dir


def _path() -> str:
    return os.path.join(data_dir(), "app.log")


def log(msg: str) -> None:
    try:
        with open(_path(), "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n")
    except Exception:
        pass
