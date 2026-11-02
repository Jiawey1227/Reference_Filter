[Setup]
AppId={{6FA5C427-D528-47AB-9305-EA7508C5FCA1}
AppName=Author Scope Screening
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\AuthorScopeScreening
DefaultGroupName=Author Scope Screening
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=AuthorScopeScreening-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
[Files]
Source: "..\dist\AuthorScopeScreening\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Author Scope Screening"; Filename: "{app}\AuthorScopeScreening.exe"
Name: "{autodesktop}\Author Scope Screening"; Filename: "{app}\AuthorScopeScreening.exe"
[Run]
Filename: "{app}\AuthorScopeScreening.exe"; Description: "Open Author Scope Screening"; Flags: nowait postinstall skipifsilent
