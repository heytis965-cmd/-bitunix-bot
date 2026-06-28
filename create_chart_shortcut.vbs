Set WshShell = CreateObject("WScript.Shell")
desktop = WshShell.SpecialFolders("Desktop")
botPath = WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\Mimo_Projects\bitunix_bot"

Set shortcut = WshShell.CreateShortcut(desktop & "\Trade Charts.lnk")
shortcut.TargetPath = "cmd.exe"
shortcut.Arguments = "/c chcp 65001 >nul && cd /d """ & botPath & """ && python simulator.py"
shortcut.WorkingDirectory = botPath
shortcut.IconLocation = "shell32.dll,13"
shortcut.Description = "Bitunix Bot + Dashboard"
shortcut.Save
