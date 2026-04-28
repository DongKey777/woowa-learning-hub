# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\registry-audit.ps1 [args...]
# bash equivalent: bin/registry-audit ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" registry-audit @args
exit $LASTEXITCODE
