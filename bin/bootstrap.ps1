# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\bootstrap.ps1 [args...]
# bash equivalent: bin/bootstrap ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" bootstrap @args
exit $LASTEXITCODE
