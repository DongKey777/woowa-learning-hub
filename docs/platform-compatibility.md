# Platform Compatibility

`woowa-learning-hub`는 macOS / Linux / Windows 모두에서 동작한다. 다만 Windows는 **WSL2가
가장 매끄럽고**, native PowerShell도 가능하지만 약간의 제약이 있다.

## 한눈에

| 환경 | bash wrapper (`bin/*`) | PowerShell wrapper (`bin/*.ps1`) | Python 직접 호출 | 권장 |
|---|---|---|---|---|
| **macOS** | ✅ | n/a | ✅ | ✅ |
| **Linux** | ✅ | n/a | ✅ | ✅ |
| **Windows + WSL2** (Ubuntu 등) | ✅ | n/a | ✅ | ✅ |
| **Windows + Git Bash** | ✅ | ⚠️ pwsh 별도 | ✅ | 가능 |
| **Windows + PowerShell / cmd** | ❌ | ✅ **권장** | ✅ | 가능 |

모든 wrapper(`bin/*`, `bin/*.ps1`)는 같은 Python 모듈을 호출하므로 **동작 100% 동일**.
학습자는 OS별로 자기 환경에 맞는 형식을 쓰면 된다.

## 동작 원리

### Cross-platform 파일 잠금

학습자 stream과 orchestrator queue는 advisory file lock을 쓴다. 구현은
[`scripts/workbench/core/file_lock.py`](../scripts/workbench/core/file_lock.py)에 통합:

- **Unix** (macOS / Linux / WSL): `fcntl.flock`
- **Native Windows**: `fcntl` 모듈이 없어서 no-op (single-user 환경 가정)

학습자 한 명이 자기 노트북에서 단일 프로세스로 사용하는 한 race condition은 발생하지 않으니
no-op으로 충분. 진짜 multi-process 동시성이 필요한 orchestrator worker fleet (개발자 영역)을
native Windows에서 돌리려면 별도 라이브러리 (`portalocker`, `filelock`) 도입이 필요할 수
있지만, 동료 크루(학습자) 흐름엔 영향 없음.

### Entry point 종류

워크벤치 명령은 두 가지 형식으로 노출된다.

**(1) bin/ 셸 래퍼** — macOS / Linux / WSL / Git Bash에서 동작:

```bash
bin/rag-ask "Bean이 뭐야?" --module spring-core-1
bin/learn-test --module spring-core-1
bin/learn-drill offer --concept concept:spring/di
bin/learner-profile show
```

**(2) Python 직접 호출** — 모든 OS에서 동작 (native Windows 포함):

```bash
python scripts/workbench/cli.py rag-ask "Bean이 뭐야?" --module spring-core-1
python scripts/workbench/cli.py learn-test --module spring-core-1
python scripts/workbench/cli.py learn-drill offer --concept concept:spring/di
python scripts/workbench/cli.py learner-profile show
```

두 형식은 **완전히 동일한 동작**. `bin/*`은 단순 wrapper로 내부적으로 (2)와 같은 명령을
호출한다.

## Windows 환경 셋업 가이드

### 옵션 A: WSL2 (가장 매끄러움)

```powershell
# 1. WSL2 설치 (관리자 PowerShell, 한 번만)
wsl --install

# 2. Ubuntu 들어가기 (이후엔 wsl 입력하면 들어감)
wsl

# 3. Ubuntu 안에서 (macOS/Linux와 완전 동일)
sudo apt update && sudo apt install -y python3-pip git gh
gh auth login
cd ~
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
claude --dangerously-skip-permissions   # 또는 codex / gemini
# 한국어로: "이 저장소로 학습 시작하자."
```

이후 학습자 경험은 macOS/Linux와 100% 동일.

### 옵션 B: Native PowerShell

```powershell
# 1. Python / git / gh 설치 필요 (winget / chocolatey 등)
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
python -m pip install -e .
gh auth login

# 2. PowerShell ExecutionPolicy 설정 (한 번만)
#    unsigned local script 실행 허용. CurrentUser scope이라 다른 사용자에게 영향 없음.
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3. AI 세션 시작
claude --dangerously-skip-permissions   # 또는 codex / gemini
# 한국어로: "이 저장소로 학습 시작하자."
```

**명령 형식**: AI가 OS를 감지해서 자동으로 `.ps1` wrapper를 호출:

```powershell
# bash 형식 (macOS/Linux/WSL):  bin/rag-ask "Bean이 뭐야?"
# PowerShell 형식 (Native Win):  .\bin\rag-ask.ps1 "Bean이 뭐야?"
# Python 직접 (모든 OS):         python scripts/workbench/cli.py rag-ask "Bean이 뭐야?"
```

세 형식 모두 같은 Python 모듈을 호출하므로 **동작 100% 동일**. AI는 첫 명령에서 OS 감지
(`uname` 실패 또는 `$env:OS == "Windows_NT"`)해서 적절한 형식 자동 선택.

**ExecutionPolicy 보안**: `RemoteSigned`는 인터넷에서 받은 unsigned 스크립트는 거부하고
로컬 unsigned 스크립트만 허용. CurrentUser scope이라 시스템 전체에 영향 없음. 워크벤치
저장소를 신뢰한다는 전제로 안전.

### 옵션 C: Git Bash

Git for Windows에 포함된 Git Bash는 bash 환경을 제공하므로 `bin/*` 셸 스크립트도 직접 사용
가능. 다만 일부 macOS 전용 도구 (예: `du -sh`의 출력 형식)가 살짝 다를 수 있어 진단 명령은
PowerShell보다 약간 불안정할 수 있다.

## 검증

CI나 동료 환경에서 cross-platform 동작을 확인하려면:

```bash
# 정상 회귀 (현재 OS 기준)
HF_HUB_OFFLINE=1 python3 -m unittest discover -s tests/unit -p 'test_*.py'

# Windows 시뮬레이션 (fcntl import 차단)
python3 -c "
import builtins
_real = builtins.__import__
def block(name, *a, **k):
    if name == 'fcntl': raise ImportError('simulated Windows')
    return _real(name, *a, **k)
builtins.__import__ = block

import sys; sys.path.insert(0, 'scripts/workbench')
from core.file_lock import has_native_lock
assert has_native_lock() is False
from core import memory, orchestrator, orchestrator_workers
print('OK: import 성공')
"
```

## 의도 / 한계

- **Single-user 가정**: 학습자 한 명 노트북. multi-process 동시성은 orchestrator worker
  fleet (개발자 영역)에서만 발생.
- **Lock 무용 가정**: native Windows에서 학습자 흐름 (`bin/rag-ask`, `bin/coach-run`,
  `bin/learn-*`)은 단일 프로세스로 호출되니 lock no-op으로 충분.
- **Orchestrator multi-worker on native Windows는 미보장**: 동료 크루(학습자)는 안 쓰는
  영역이라 우선순위 낮음. 필요해지면 `portalocker` / `filelock` 도입 고려.
