"""
Valorant paketi - true stretched icin config, ini duzenleme ve surec yonetimi.

Disari acilan API (main.py / api.py bunlari 'valorant.X' olarak kullanir):
  config:   config_dir, get_last_known_user, account_files, target_files, account_exists
  process:  is_game_running, riot_client_path, launch_valorant, kill_game
  settings: apply_stretched
"""

from .config import (
    config_dir,
    get_last_known_user,
    account_files,
    target_files,
    account_exists,
)
from .process import (
    is_game_running,
    riot_client_path,
    launch_valorant,
    kill_game,
    kill_all,
)
from .settings import apply_stretched

__all__ = [
    "config_dir", "get_last_known_user", "account_files", "target_files",
    "account_exists", "is_game_running", "riot_client_path", "launch_valorant",
    "kill_game", "kill_all", "apply_stretched",
]
