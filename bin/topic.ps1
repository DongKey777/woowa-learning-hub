# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\topic.ps1 [args...]
# bash equivalent: bin/topic ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" topic @args
exit $LASTEXITCODE
