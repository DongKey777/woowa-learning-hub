# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\my-pr.ps1 [args...]
# bash equivalent: bin/my-pr ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" my-pr @args
exit $LASTEXITCODE
