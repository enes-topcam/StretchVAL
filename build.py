"""
Tek dosyalik .exe uretir (PyInstaller ile).

Kullanim:
    pip install pyinstaller
    python build.py

Cikti:  dist/StretchVAL.exe
"""

import os
import sys
import shutil
import subprocess

APP_NAME = "StretchVAL"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller kurulu degil. Once:  pip install pyinstaller")
        sys.exit(1)

    # Eski ciktilari temizle
    for d in ("build", "dist"):
        p = os.path.join(HERE, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
    spec = os.path.join(HERE, f"{APP_NAME}.spec")
    if os.path.exists(spec):
        os.remove(spec)

    # Windows'ta --add-data ayraci ';'
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",                      # konsol penceresi acma
        "--name", APP_NAME,
        "--add-data", "ui;ui",             # HTML/CSS/JS arayuzu gomule
        "--add-data", "assets;assets",     # marka gorselleri (logo/ikon)
        "--collect-all", "webview",        # WebView2 loader DLL'leri + hook'lar
        "--collect-all", "clr_loader",     # pythonnet runtime
        "--hidden-import", "clr",
        "--icon", os.path.join("assets", "branding", "stretchval-icon.ico"),
        "main.py",
    ]
    print("Calistiriliyor:\n  " + " ".join(args) + "\n")
    result = subprocess.run(args, cwd=HERE)
    if result.returncode == 0:
        out = os.path.join(HERE, "dist", f"{APP_NAME}.exe")
        print(f"\nTamamlandi -> {out}")
    else:
        print("\nBuild basarisiz oldu.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
