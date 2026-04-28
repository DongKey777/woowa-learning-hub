# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\set-profile.ps1 [args...]
# bash equivalent: bin/set-profile ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" set-profile @args
exit $LASTEXITCODE
