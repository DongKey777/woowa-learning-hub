# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\cs-index-build.ps1 [args...]
# bash equivalent: bin/cs-index-build ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\learning\cli_cs_index_build.py"  @args
exit $LASTEXITCODE
