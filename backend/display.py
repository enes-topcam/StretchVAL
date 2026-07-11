"""
Win32 ekran (display) katmani.

ctypes ile user32.dll uzerinden:
  - Bagli monitorleri listeler (EnumDisplayDevices)
  - Her monitorun desteklenen tum modlarini (cozunurluk + Hz) toplar (EnumDisplaySettingsEx)
  - Mevcut modu okur (ENUM_CURRENT_SETTINGS)
  - Cozunurluk / yenileme hizini degistirir (ChangeDisplaySettingsEx)
  - Monitor konumlarini (masaustu duzeni) verir -> UI'da gorsel yerlesim icin

Admin yetkisi GEREKMEZ. Sadece Windows'ta calisir.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass, asdict
from math import gcd

user32 = ctypes.windll.user32

# ---- Sabitler (winuser.h) ----------------------------------------------------
ENUM_CURRENT_SETTINGS = -1
ENUM_REGISTRY_SETTINGS = -2

CDS_UPDATEREGISTRY = 0x00000001
CDS_TEST = 0x00000002
CDS_FULLSCREEN = 0x00000004
CDS_GLOBAL = 0x00000008
CDS_SET_PRIMARY = 0x00000010
CDS_RESET = 0x40000000
CDS_NORESET = 0x10000000

DISP_CHANGE_SUCCESSFUL = 0
DISP_CHANGE_RESTART = 1
DISP_CHANGE_FAILED = -1
DISP_CHANGE_BADMODE = -2
DISP_CHANGE_NOTUPDATED = -3
DISP_CHANGE_BADFLAGS = -4
DISP_CHANGE_BADPARAM = -5
DISP_CHANGE_BADDUALVIEW = -6

_CHANGE_RESULTS = {
    DISP_CHANGE_SUCCESSFUL: "Basarili",
    DISP_CHANGE_RESTART: "Degisiklik icin yeniden baslatma gerekiyor",
    DISP_CHANGE_FAILED: "Surucu bu modu uygulayamadi (FAILED)",
    DISP_CHANGE_BADMODE: "Bu grafik modu desteklenmiyor (BADMODE)",
    DISP_CHANGE_NOTUPDATED: "Registry'e yazilamadi (NOTUPDATED)",
    DISP_CHANGE_BADFLAGS: "Gecersiz bayrak (BADFLAGS)",
    DISP_CHANGE_BADPARAM: "Gecersiz parametre (BADPARAM)",
    DISP_CHANGE_BADDUALVIEW: "Dual-view yapilandirmasi hatasi (BADDUALVIEW)",
}

# DISPLAY_DEVICE.StateFlags
DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001
DISPLAY_DEVICE_PRIMARY_DEVICE = 0x00000004

# DEVMODE.dmFields
DM_BITSPERPEL = 0x00040000
DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000
DM_DISPLAYFREQUENCY = 0x00400000
DM_POSITION = 0x00000020


# ---- Struct'lar --------------------------------------------------------------
class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


class POINTL(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class _DUMMYSTRUCT(ctypes.Structure):
    _fields_ = [
        ("dmOrientation", wintypes.SHORT),
        ("dmPaperSize", wintypes.SHORT),
        ("dmPaperLength", wintypes.SHORT),
        ("dmPaperWidth", wintypes.SHORT),
        ("dmScale", wintypes.SHORT),
        ("dmCopies", wintypes.SHORT),
        ("dmDefaultSource", wintypes.SHORT),
        ("dmPrintQuality", wintypes.SHORT),
    ]


class _DUMMYUNION(ctypes.Union):
    _fields_ = [
        ("dummystruct", _DUMMYSTRUCT),
        ("dmPosition", POINTL),
    ]


class DEVMODEW(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("u", _DUMMYUNION),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", wintypes.WCHAR * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


# ---- Fonksiyon imzalari ------------------------------------------------------
user32.EnumDisplayDevicesW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DISPLAY_DEVICEW), wintypes.DWORD
]
user32.EnumDisplayDevicesW.restype = wintypes.BOOL

user32.EnumDisplaySettingsExW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DEVMODEW), wintypes.DWORD
]
user32.EnumDisplaySettingsExW.restype = wintypes.BOOL

user32.ChangeDisplaySettingsExW.argtypes = [
    wintypes.LPCWSTR, ctypes.POINTER(DEVMODEW), wintypes.HWND,
    wintypes.DWORD, wintypes.LPVOID
]
user32.ChangeDisplaySettingsExW.restype = wintypes.LONG


# ---- Yardimci veri tipleri ---------------------------------------------------
@dataclass
class DisplayMode:
    width: int
    height: int
    refresh: int      # Hz
    bpp: int          # bits per pixel

    @property
    def aspect(self) -> str:
        return aspect_ratio(self.width, self.height)

    def key(self) -> tuple:
        return (self.width, self.height, self.refresh)


@dataclass
class Monitor:
    device_name: str          # ornek: \\.\DISPLAY1  (API cagrilarinda kullanilir)
    friendly_name: str        # ornek: Generic PnP Monitor / monitor modeli
    adapter_name: str         # ekran karti string'i
    primary: bool
    x: int                    # masaustu konumu
    y: int
    current: DisplayMode
    modes: list               # list[DisplayMode]


def aspect_ratio(w: int, h: int) -> str:
    """1280x1024 -> '5:4', 1920x1080 -> '16:9' gibi. Bilinen oranlara yuvarlar."""
    if h == 0:
        return "?"
    ratio = w / h
    known = {
        "4:3": 4 / 3,
        "5:4": 5 / 4,
        "16:9": 16 / 9,
        "16:10": 16 / 10,
        "21:9": 21 / 9,
        "3:2": 3 / 2,
        "32:9": 32 / 9,
    }
    best, best_err = "?", 1e9
    for label, val in known.items():
        err = abs(ratio - val)
        if err < best_err:
            best, best_err = label, err
    # Bilinen orana yeterince yakin degilse indirgenmis kesir ver
    if best_err > 0.02:
        g = gcd(w, h)
        return f"{w // g}:{h // g}"
    return best


def _read_current_mode(device_name: str) -> DisplayMode | None:
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if user32.EnumDisplaySettingsExW(device_name, ENUM_CURRENT_SETTINGS, ctypes.byref(dm), 0):
        return DisplayMode(dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency, dm.dmBitsPerPel)
    return None


def _enumerate_modes(device_name: str) -> list:
    """Bir monitorun desteklenen tum modlarini toplar, tekrarları eler."""
    modes: dict[tuple, DisplayMode] = {}
    i = 0
    while True:
        dm = DEVMODEW()
        dm.dmSize = ctypes.sizeof(DEVMODEW)
        if not user32.EnumDisplaySettingsExW(device_name, i, ctypes.byref(dm), 0):
            break
        i += 1
        # Cok dusuk renk derinligini (8/16 bpp) atla, sadece 32 bpp modlar
        if dm.dmBitsPerPel and dm.dmBitsPerPel < 32:
            continue
        m = DisplayMode(dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency, dm.dmBitsPerPel)
        if m.width < 640 or m.height < 480:
            continue
        modes[m.key()] = m
    # Buyukten kucuge, sonra Hz'e gore sirala
    return sorted(modes.values(), key=lambda m: (-m.width, -m.height, -m.refresh))


def list_monitors() -> list:
    """Masaustune bagli tum monitorleri, mevcut ve desteklenen modlariyla dondurur."""
    monitors: list[Monitor] = []
    i = 0
    while True:
        adapter = DISPLAY_DEVICEW()
        adapter.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(adapter), 0):
            break
        i += 1
        if not (adapter.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP):
            continue

        device_name = adapter.DeviceName  # \\.\DISPLAYx

        # Bagli monitorun "friendly" adini al (ikinci seviye EnumDisplayDevices)
        mon = DISPLAY_DEVICEW()
        mon.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        friendly = adapter.DeviceString
        if user32.EnumDisplayDevicesW(device_name, 0, ctypes.byref(mon), 0):
            if mon.DeviceString:
                friendly = mon.DeviceString

        current = _read_current_mode(device_name)
        if current is None:
            continue

        # Konum icin DEVMODE.dmPosition (POSITION alani)
        dm = DEVMODEW()
        dm.dmSize = ctypes.sizeof(DEVMODEW)
        x = y = 0
        if user32.EnumDisplaySettingsExW(device_name, ENUM_CURRENT_SETTINGS, ctypes.byref(dm), 0):
            x, y = dm.dmPosition.x, dm.dmPosition.y

        monitors.append(Monitor(
            device_name=device_name,
            friendly_name=friendly,
            adapter_name=adapter.DeviceString,
            primary=bool(adapter.StateFlags & DISPLAY_DEVICE_PRIMARY_DEVICE),
            x=x, y=y,
            current=current,
            modes=_enumerate_modes(device_name),
        ))
    return monitors


def change_resolution(device_name: str, width: int, height: int,
                      refresh: int | None = None, test_only: bool = False) -> tuple:
    """
    Bir monitorun cozunurlugunu (ve istege bagli Hz) degistirir.
    Donen: (basari: bool, mesaj: str)
    """
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    # Once mevcut modu doldur (diger alanlar bozulmasin)
    if not user32.EnumDisplaySettingsExW(device_name, ENUM_CURRENT_SETTINGS, ctypes.byref(dm), 0):
        return False, "Mevcut ekran ayarlari okunamadi"

    dm.dmPelsWidth = width
    dm.dmPelsHeight = height
    dm.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT
    if refresh:
        dm.dmDisplayFrequency = refresh
        dm.dmFields |= DM_DISPLAYFREQUENCY

    flags = CDS_TEST if test_only else CDS_UPDATEREGISTRY
    result = user32.ChangeDisplaySettingsExW(device_name, ctypes.byref(dm), None, flags, None)
    ok = result == DISP_CHANGE_SUCCESSFUL
    msg = _CHANGE_RESULTS.get(result, f"Bilinmeyen sonuc kodu: {result}")
    return ok, msg


def monitor_to_dict(m: Monitor) -> dict:
    """UI'ya JSON olarak gonderilebilir sozluk."""
    d = asdict(m)
    d["current"]["aspect"] = m.current.aspect
    d["modes"] = [
        {**asdict(mode), "aspect": mode.aspect} for mode in m.modes
    ]
    return d


if __name__ == "__main__":
    # Hizli manuel test: monitorleri ve modlari yazdir
    mons = list_monitors()
    print(f"{len(mons)} monitor bulundu:\n")
    for mon in mons:
        star = " *(birincil)" if mon.primary else ""
        print(f"[{mon.device_name}] {mon.friendly_name}{star}")
        print(f"  konum: ({mon.x},{mon.y})")
        print(f"  mevcut: {mon.current.width}x{mon.current.height} "
              f"@{mon.current.refresh}Hz  ({mon.current.aspect})")
        # Aspect ratio'ya gore grupla ozet
        by_aspect: dict[str, set] = {}
        for md in mon.modes:
            by_aspect.setdefault(md.aspect, set()).add((md.width, md.height))
        print(f"  {len(mon.modes)} mod, oranlar:")
        for asp in sorted(by_aspect):
            reslist = sorted(by_aspect[asp], key=lambda r: -r[0])
            shown = ", ".join(f"{w}x{h}" for w, h in reslist[:6])
            print(f"    {asp:>6}: {shown}")
        print()
