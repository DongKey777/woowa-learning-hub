# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\session-start.ps1 [args...]
# bash equivalent: bin/session-start ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" session-start @args
exit $LASTEXITCODE
