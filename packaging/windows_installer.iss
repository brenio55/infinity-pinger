[Setup]
AppName=InfinityPinger
AppVersion=0.3.0
AppPublisher=Orkestrae
DefaultDirName={autopf}\InfinityPinger
DefaultGroupName=InfinityPinger
UninstallDisplayIcon={app}\InfinityPinger.exe
Compression=lzma2
SolidCompression=yes
; O output vai para a pasta 'releases' na raiz
OutputDir=..\releases
OutputBaseFilename=InfinityPinger_Setup_v0.3.0_Win

[Tasks]
Name: "desktopicon"; Description: "Criar icone na Area de Trabalho"; GroupDescription: "Atalhos Adicionais:"

[Files]
; Copia a pasta gerada pelo PyInstaller (que estara em build/dist/InfinityPinger)
Source: "dist\InfinityPinger\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\InfinityPinger"; Filename: "{app}\InfinityPinger.exe"
Name: "{group}\Desinstalar InfinityPinger"; Filename: "{uninstallexe}"
Name: "{autodesktop}\InfinityPinger"; Filename: "{app}\InfinityPinger.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\InfinityPinger.exe"; Description: "Abrir o InfinityPinger agora"; Flags: nowait postinstall skipifsilent
