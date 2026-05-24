$ErrorActionPreference = "Stop"
$py = "C:\ProgramData\miniconda3\envs\mineru\python.exe"
$script = Join-Path $PSScriptRoot "watcher.py"
& $py $script @args
