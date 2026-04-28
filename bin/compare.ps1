# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\compare.ps1 [args...]
# bash equivalent: bin/compare ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" compare @args
exit $LASTEXITCODE
