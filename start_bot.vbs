Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd.exe /c chcp 65001 >nul && pythonw.exe -u ""C:\Users\Леонид\Mimo_Projects\bitunix_bot\simulator.py""", 0, False