# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\golden.ps1 [args...]
# bash equivalent: bin/golden ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" golden @args
exit $LASTEXITCODE
