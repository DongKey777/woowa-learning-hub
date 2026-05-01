# Usage: .\bin\rag-daemon.ps1 start|status|stop
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PY = if ($env:PYTHON) { $env:PYTHON } else { "python" }
& $PY "$ROOT\scripts\workbench\cli.py" rag-daemon @args
