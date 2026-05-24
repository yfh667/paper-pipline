$ErrorActionPreference = "Stop"
$py = "C:\ProgramData\miniconda3\envs\mineru\pythonw.exe"
if (-not (Test-Path $py)) { $py = "C:\ProgramData\miniconda3\envs\mineru\python.exe" }
$script = Join-Path $PSScriptRoot "export_gui.py"
& $py $script
