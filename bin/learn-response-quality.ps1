# Usage: .\bin\learn-response-quality.ps1 [args...]
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
& python "$ROOT\scripts\learning\cli_learn_response_quality.py" @args
