; StretchVAL - Inno Setup kurulum betigi
;
; Derlemek icin:
;   1) Once  python build.py  -> dist\StretchVAL.exe uretir
;   2) Inno Setup kur: https://jrsoftware.org/isdl.php
;   3) Bu dosyayi Inno Setup Compiler ile ac -> Build > Compile
;      (veya  installer\build_installer.bat  calistir)
;
; Cikti: dist\StretchVAL-Setup.exe  (GitHub Releases'e yuklenecek dosya)

#define AppName "StretchVAL"
#define AppVersion "1.0.0"
#define AppPublisher "whoop"
#define AppExe "StretchVAL.exe"

[Setup]
AppId={{9F2A7C34-5E81-4B0A-B3D6-1C7E9A0F2B48}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
; Admin gerektirmeden kullanici klasorune kurar (UAC yok)
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayName={#AppName}
OutputDir=..\dist
OutputBaseFilename=StretchVAL-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\assets\branding\stretchval-icon.ico
UninstallDisplayIcon={app}\stretchval-icon.ico

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayollar:"

[Files]
Source: "..\dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\branding\stretchval-icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\stretchval-icon.ico"
Name: "{group}\{#AppName} Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon; IconFilename: "{app}\stretchval-icon.ico"

[Run]
Filename: "{app}\{#AppExe}"; Description: "StretchVAL'ı şimdi çalıştır"; Flags: nowait postinstall skipifsilent
