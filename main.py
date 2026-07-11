"""
StretchVAL - giris noktasi.

pywebview penceresini acar ve UI (ui/index.html) ile Python backend arasindaki
kopruyu (backend.api.Api) baglar. Tum uygulama mantigi backend/ ve ui/ altinda.
"""

from __future__ import annotations

import os
import webview

from backend.api import Api
from backend.paths import resource_path
from backend import constants as C


def main():
    api = Api()
    window = webview.create_window(
        title=C.WINDOW_TITLE,
        url=resource_path(os.path.join("ui", "index.html")),
        js_api=api,
        width=C.WINDOW_WIDTH,
        height=C.WINDOW_HEIGHT,
        min_size=C.WINDOW_MIN_SIZE,
        background_color=C.WINDOW_BG,
    )
    api.set_window(window)
    # WebView2 (Windows 11'de hazir) tercih edilir; yoksa mshtml'e duser.
    webview.start(gui="edgechromium", debug=False)


if __name__ == "__main__":
    main()
