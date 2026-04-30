# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\cs-index-build.ps1 [args...]
# bash equivalent: bin/cs-index-build ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
if ($env:PYTHON) {
    $PY = $env:PYTHON
} elseif (Test-Path "$ROOT\.venv\Scripts\python.exe") {
    $PY = "$ROOT\.venv\Scripts\python.exe"
} elseif (Test-Path "$ROOT\.venv\bin\python") {
    $PY = "$ROOT\.venv\bin\python"
} else {
    $PY = "python"
}
& $PY "$ROOT\scripts\learning\cli_cs_index_build.py"  @args
exit $LASTEXITCODE
