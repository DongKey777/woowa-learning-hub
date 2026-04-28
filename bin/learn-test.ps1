# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\learn-test.ps1 [args...]
# bash equivalent: bin/learn-test ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" learn-test @args
exit $LASTEXITCODE
