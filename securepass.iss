; securepass.iss - Inno Setup script for SecurePass

[Setup]
AppName=SecurePass Manager
AppVersion={#APP_VERSION}
DefaultDirName={autopf}\SecurePass
DefaultGroupName=SecurePass
OutputDir=installer_output
OutputBaseFilename=SecurePassInstaller-{#APP_VERSION}
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\main.exe
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\main.dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SecurePass"; Filename: "{app}\main.exe"
Name: "{commondesktop}\SecurePass"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\main.exe"; Description: "Launch SecurePass"; Flags: nowait postinstall skipifsilent