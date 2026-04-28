# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\assess-learner-state.ps1 [args...]
# bash equivalent: bin/assess-learner-state ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" assess-learner-state @args
exit $LASTEXITCODE
