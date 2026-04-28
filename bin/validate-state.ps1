# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\validate-state.ps1 [args...]
# bash equivalent: bin/validate-state ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" validate-state @args
exit $LASTEXITCODE
