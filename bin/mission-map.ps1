# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\mission-map.ps1 [args...]
# bash equivalent: bin/mission-map ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" mission-map @args
exit $LASTEXITCODE
