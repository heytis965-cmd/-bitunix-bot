$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Bitunix Bot Dashboard.url")
$Shortcut.TargetPath = "http://localhost:5000"
$Shortcut.Save()
Write-Output "Shortcut created"
