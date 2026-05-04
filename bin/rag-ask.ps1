# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\rag-ask.ps1 [args...]
# bash equivalent: bin/rag-ask ...
#
# Default to daemon mode + R3 production env vars (95.5% Pilot baseline).
# Opt out with $env:WOOWA_RAG_NO_DAEMON = "1".
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

if (-not $env:WOOWA_RAG_R3_ENABLED) { $env:WOOWA_RAG_R3_ENABLED = "1" }
if (-not $env:WOOWA_RAG_R3_RERANK_POLICY) { $env:WOOWA_RAG_R3_RERANK_POLICY = "always" }
if (-not $env:WOOWA_RAG_R3_FORBIDDEN_FILTER) { $env:WOOWA_RAG_R3_FORBIDDEN_FILTER = "1" }
if (-not $env:HF_HUB_OFFLINE) { $env:HF_HUB_OFFLINE = "1" }

$daemonArgs = @()
if ($env:WOOWA_RAG_NO_DAEMON -ne "1") {
    $daemonArgs += "--via-daemon"
}

& python "$ROOT\scripts\workbench\cli.py" rag-ask @daemonArgs @args
exit $LASTEXITCODE
