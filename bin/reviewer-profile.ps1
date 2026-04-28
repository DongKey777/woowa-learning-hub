# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\reviewer-profile.ps1 [args...]
# bash equivalent: bin/reviewer-profile ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" reviewer-profile @args
exit $LASTEXITCODE
