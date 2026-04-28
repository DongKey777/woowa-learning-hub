# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\rag-ask.ps1 [args...]
# bash equivalent: bin/rag-ask ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" rag-ask @args
exit $LASTEXITCODE
