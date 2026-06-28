$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Bitunix Bot.lnk")
$Shortcut.TargetPath = "python.exe"
$Shortcut.Arguments = "-u C:\Users\Леонид\Mimo_Projects\bitunix_bot\simulator.py"
$Shortcut.WorkingDirectory = "C:\Users\Леонид\Mimo_Projects\bitunix_bot"
$Shortcut.Description = "Bitunix Trading Bot Simulator"
$Shortcut.Save()
echo "Desktop shortcut created"
