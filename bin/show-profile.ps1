# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\show-profile.ps1 [args...]
# bash equivalent: bin/show-profile ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" show-profile @args
exit $LASTEXITCODE
