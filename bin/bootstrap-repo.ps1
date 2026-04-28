# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\bootstrap-repo.ps1 [args...]
# bash equivalent: bin/bootstrap-repo ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" bootstrap-repo @args
exit $LASTEXITCODE
