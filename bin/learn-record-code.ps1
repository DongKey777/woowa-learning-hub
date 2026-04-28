# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\learn-record-code.ps1 [args...]
# bash equivalent: bin/learn-record-code ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" learn-record-code @args
exit $LASTEXITCODE
