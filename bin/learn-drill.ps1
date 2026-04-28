# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\learn-drill.ps1 [args...]
# bash equivalent: bin/learn-drill ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" learn-drill @args
exit $LASTEXITCODE
