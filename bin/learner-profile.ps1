# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\learner-profile.ps1 [args...]
# bash equivalent: bin/learner-profile ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" learner-profile @args
exit $LASTEXITCODE
