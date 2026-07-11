"""Profil deposu (kaydet/guncelle/sil + named bayragi) testleri.

APPDATA'yi gecici klasore yonlendirip gercek veriye dokunmadan test eder.
"""

import importlib


def _fresh_profiles(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from backend import profiles
    importlib.reload(profiles)  # data_dir env'i cagri aninda okur, yine de temiz baslayalim
    return profiles


def test_add_update_delete(tmp_path, monkeypatch):
    profiles = _fresh_profiles(tmp_path, monkeypatch)

    assert profiles.load_profiles() == []

    profiles.add_profile("Ana Hesap", "puuid-1", named=True)
    ps = profiles.load_profiles()
    assert len(ps) == 1
    assert ps[0]["nickname"] == "Ana Hesap"
    assert ps[0]["named"] is True

    # Ayni puuid -> guncelle (named=False)
    profiles.add_profile("kisa-ad", "puuid-1", named=False)
    ps = profiles.load_profiles()
    assert len(ps) == 1
    assert ps[0]["named"] is False

    profiles.delete_profile("puuid-1")
    assert profiles.load_profiles() == []
