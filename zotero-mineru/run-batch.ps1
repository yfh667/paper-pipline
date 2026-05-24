$ErrorActionPreference = "Stop"
$py = "C:\ProgramData\miniconda3\envs\mineru\python.exe"
$script = Join-Path $PSScriptRoot "batch.py"
& $py $script @args
