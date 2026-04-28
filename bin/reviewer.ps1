# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\reviewer.ps1 [args...]
# bash equivalent: bin/reviewer ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" reviewer @args
exit $LASTEXITCODE
