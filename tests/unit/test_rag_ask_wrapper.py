from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rag_ask_no_daemon_opt_out_handles_empty_daemon_args():
    env = {
        **os.environ,
        "WOOWA_RAG_NO_DAEMON": "1",
    }

    result = subprocess.run(
        [str(ROOT / "bin" / "rag-ask"), "Gradle 설정 어떻게 해?"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["decision"]["tier"] == 0
    assert payload["decision"]["reason"] == "tool/build question, no CS domain"
