$ErrorActionPreference = "Stop"
$py = "C:\ProgramData\miniconda3\envs\mineru\python.exe"
$script = Join-Path $PSScriptRoot "status.py"
& $py $script @args
Write-Host ""
Read-Host "Press Enter to close"
