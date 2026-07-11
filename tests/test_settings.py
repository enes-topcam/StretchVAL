"""GameUserSettings.ini duzenleme (bolum-farkinda editor) testleri."""

from backend.valorant import settings

INI = """[/Script/ShooterGame.ShooterGameUserSettings]
bShouldLetterbox=True
bLastConfirmedShouldLetterbox=True
ResolutionSizeX=1920
ResolutionSizeY=1080
FullscreenMode=0

[ScalabilityGroups]
sg.TextureQuality=0
"""


def test_edit_updates_values_and_is_idempotent(tmp_path):
    p = tmp_path / "GameUserSettings.ini"
    p.write_text(INI, encoding="utf-8")

    desired = settings._desired(1280, 960)
    r1 = settings._edit_file(str(p), desired)
    assert r1["changed"] is True

    txt = p.read_text(encoding="utf-8")
    assert "bShouldLetterbox=False" in txt
    assert "bLastConfirmedShouldLetterbox=False" in txt
    assert "ResolutionSizeX=1280" in txt
    assert "ResolutionSizeY=960" in txt
    assert "FullscreenMode=2" in txt

    # Ayni istek tekrar -> degisiklik olmamali
    r2 = settings._edit_file(str(p), desired)
    assert r2["changed"] is False


def test_missing_key_inserted_into_shootergame_section(tmp_path):
    ini = (
        "[/Script/ShooterGame.ShooterGameUserSettings]\n"
        "bShouldLetterbox=True\n"
        "\n"
        "[/Script/Engine.GameUserSettings]\n"
        "bUseDesiredScreenHeight=False\n"
    )
    p = tmp_path / "g.ini"
    p.write_text(ini, encoding="utf-8")

    settings._edit_file(str(p), settings._desired(1280, 960))
    lines = p.read_text(encoding="utf-8").splitlines()

    i_shooter = lines.index("[/Script/ShooterGame.ShooterGameUserSettings]")
    i_engine = lines.index("[/Script/Engine.GameUserSettings]")
    fs = [i for i, l in enumerate(lines) if l.startswith("FullscreenMode=")]
    # FullscreenMode dosyanin sonuna degil, ShooterGame bolumunun icine eklenmeli
    assert fs, "FullscreenMode eklenmedi"
    assert i_shooter < fs[0] < i_engine
