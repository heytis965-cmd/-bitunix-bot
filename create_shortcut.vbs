Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
botPath = WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\Mimo_Projects\bitunix_bot"
Set f = fso.CreateTextFile(botPath & "\start.vbs", True)
f.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
f.WriteLine "WshShell.CurrentDirectory = """ & botPath & """"
f.WriteLine "WshShell.Run ""cmd /c chcp 65001 >nul && " & botPath & "\go.cmd"", 1, False"
f.Close
WshShell.Run botPath & "\start.vbs", 0, False
