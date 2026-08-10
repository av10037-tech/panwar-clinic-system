[Setup]
AppName=Panwar Homoeopathic Clinic Management System
AppVersion=1.3
DefaultDirName={autopf}\PanwarClinic
DefaultGroupName=Panwar Homoeopathic Clinic
OutputDir=.\InstallerOutput
OutputBaseFilename=PanwarClinic_Setup_v1.3
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\homeopathy_app.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Panwar Homoeopathic Clinic"; Filename: "{app}\homeopathy_app.exe"
Name: "{autodesktop}\Panwar Homoeopathic Clinic"; Filename: "{app}\homeopathy_app.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: checkedonce