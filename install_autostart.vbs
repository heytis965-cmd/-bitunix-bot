Set WshShell = CreateObject("WScript.Shell")
startup = WshShell.SpecialFolders("Startup")
botPath = WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\Mimo_Projects\bitunix_bot"
pythonPath = Replace(WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python314\python.exe", "\\", "\")

Set fso = CreateObject("Scripting.FileSystemObject")
Set f = fso.CreateTextFile(startup & "\BitunixBot.vbs", True)
f.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
f.WriteLine "WshShell.CurrentDirectory = """ & botPath & """"
f.WriteLine "WshShell.Run ""cmd /c chcp 65001 >nul && cd /d """ & botPath & """ && python simulator.py"", 0, False"
f.Close

MsgBox "Autostart installed! Bot will start on every login.", 64, "Done"
