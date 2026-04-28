# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\repo-readiness.ps1 [args...]
# bash equivalent: bin/repo-readiness ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" repo-readiness @args
exit $LASTEXITCODE
