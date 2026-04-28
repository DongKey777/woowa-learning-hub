# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\list-repos.ps1 [args...]
# bash equivalent: bin/list-repos ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" list-repos @args
exit $LASTEXITCODE
