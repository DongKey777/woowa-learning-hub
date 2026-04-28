# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\doctor.ps1 [args...]
# bash equivalent: bin/doctor ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" doctor @args
exit $LASTEXITCODE
