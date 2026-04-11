[Setup]
AppName=ClearSkyRFI
AppVersion=0.0.1
DefaultDirName={pf}\ClearSkyRFI
DefaultGroupName=ClearSkyRFI
OutputDir=installer
OutputBaseFilename=ClearSkyRFI-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\ClearSkyRFI.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "vendor\ffmpeg\*"; DestDir: "{app}\ffmpeg"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\ClearSkyRFI"; Filename: "{app}\ClearSkyRFI.exe"
Name: "{commondesktop}\ClearSkyRFI"; Filename: "{app}\ClearSkyRFI.exe"

[Run]
Filename: "{app}\ClearSkyRFI.exe"; Description: "Launch ClearSkyRFI"; Flags: nowait postinstall skipifsilent