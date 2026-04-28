# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\coach-run.ps1 [args...]
# bash equivalent: bin/coach-run ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" coach-run @args
exit $LASTEXITCODE
