# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\archive-status.ps1 [args...]
# bash equivalent: bin/archive-status ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" archive-status @args
exit $LASTEXITCODE
