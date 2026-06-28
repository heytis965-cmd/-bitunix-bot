$botPath = "$env:USERPROFILE\Mimo_Projects\bitunix_bot"
$pythonPath = (Get-Command python).Source

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c chcp 65001 >nul && cd /d `"$botPath`" && `"$pythonPath`" simulator.py" -WorkingDirectory $botPath

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 365)

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Unregister-ScheduledTask -TaskName "BitunixBot" -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -TaskName "BitunixBot" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Bitunix Trading Bot auto-start"

Write-Host "Task created! Bot will start on login."
