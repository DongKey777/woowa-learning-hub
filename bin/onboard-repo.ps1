# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\onboard-repo.ps1 [args...]
# bash equivalent: bin/onboard-repo ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" onboard-repo @args
exit $LASTEXITCODE
