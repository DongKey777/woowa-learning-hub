# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\compose-response.ps1 [args...]
# bash equivalent: bin/compose-response ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" compose-response @args
exit $LASTEXITCODE
