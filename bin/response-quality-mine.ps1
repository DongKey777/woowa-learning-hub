# Usage: .\bin\response-quality-mine.ps1 [args...]
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
& python "$ROOT\scripts\learning\cli_response_quality_mine.py" @args
