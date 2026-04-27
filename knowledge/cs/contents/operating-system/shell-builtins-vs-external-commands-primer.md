# Shell Built-ins vs External Commands Primer

> 한 줄 요약: command가 이미 실행 파일이면 `argv`로 직접 띄우면 되고, `cd`나 `export`처럼 shell 내부 상태를 바꾸는 built-in이거나 `|`, `>`, `&&` 같은 shell 문법을 쓰면 shell이 실제로 필요하다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md) 다음에 읽는 beginner bridge다. "`언제는 `subprocess.run(["ls"])`로 충분하고, 언제는 `/bin/sh -c`가 진짜 필요한가?`"를 shell syntax, built-in, external command 세 칸으로 나눠 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Runtime Shell Option Matrix](./runtime-shell-option-matrix.md)
- [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Shell Job-Control Command Bridge](./shell-job-control-command-bridge.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: operating-system-00077, shell builtins vs external commands primer, shell builtin vs external command, shell syntax vs argv, direct argv launch basics, when shell is required, subprocess shell needed or not, shell built in command, cd export source alias builtin, pipe redirection needs shell, argv vs shell syntax, sh -c when needed, external executable direct spawn, subprocess list vs shell string, beginner handoff box

## 먼저 잡는 멘탈 모델

초보자는 command를 먼저 세 칸으로 나누면 덜 헷갈린다.

| 지금 치려는 것 | 정체 | direct `argv` launch로 충분한가 |
|---|---|---|
| `grep foo file.txt`, `python app.py`, `/bin/echo hi` | 실행 파일(external command) | 보통 그렇다 |
| `cd ..`, `export DEBUG=1`, `alias ll='ls -l'` | shell built-in | 아니다. shell이 직접 해야 한다 |
| `grep foo *.log | sort > out.txt`, `cmd1 && cmd2` | shell syntax가 들어간 command line | 아니다. shell parser가 필요하다 |

핵심 문장은 이것이다.

> direct `argv` launch는 "실행 파일 하나에 인자 배열을 넘긴다"이고, shell은 "문자열을 shell 언어로 해석하거나 shell 자신의 상태를 바꾼다"다.

그래서 질문 순서는 보통 이렇다.

1. 지금 실행하려는 대상이 실제 실행 파일인가
2. 아니면 shell 내부 명령인가
3. 아니면 shell 문법을 해석해야 하는 한 줄인가

## 한눈에 보는 분기표

| 예시 | shell이 필요한 이유 | direct `argv`로 대체 가능한가 |
|---|---|---|
| `["ls", "-l", "/tmp"]` | 없음 | 가능 |
| `["echo", "$HOME"]` | 없음. literal `$HOME`를 넘길 뿐 | 가능하지만 변수 확장은 안 된다 |
| `cd /repo` | 현재 shell의 working directory를 바꿔야 함 | 불가 |
| `export PORT=8080` | 현재 shell의 environment를 바꿔야 함 | 불가 |
| `source env.sh` | 현재 shell에 스크립트 내용을 적용해야 함 | 불가 |
| `grep foo *.log` | `*.log` glob 확장 필요 | shell이 필요하거나 앱이 직접 glob을 처리해야 함 |
| `cmd1 | cmd2` | pipe 문법 해석과 두 프로세스 배선 필요 | shell 없이도 가능하지만 runtime이 pipe wiring을 직접 구현해야 함 |
| `cmd > out.txt 2>&1` | redirection 문법 해석 필요 | shell 없이도 가능하지만 runtime이 fd redirect를 직접 구현해야 함 |

여기서 중요한 포인트는 "shell이 필요하다"가 항상 "문자열 한 줄이 더 편하다"와 같은 뜻은 아니라는 점이다.
일부 shell syntax는 runtime이 직접 pipe와 redirection을 구성해서 shell 없이도 만들 수 있다.
하지만 `cd`, `export`, `source`, `alias`처럼 **shell 자신의 상태를 바꾸는 built-in**은 그 shell이 직접 실행하지 않으면 원하는 효과가 없다.

## 1. external command는 보통 direct `argv` launch로 충분하다

예를 들어:

```python
subprocess.run(["grep", "foo", "file.txt"])
```

이 경우 runtime이 필요한 일은 단순하다.

- `grep` 실행 파일을 찾고
- `argv = ["grep", "foo", "file.txt"]`를 넘기고
- child process를 실행한다

shell parser는 필요 없다.
공백이 있는 인자도 문자열 하나로 안전하게 넘길 수 있다.

```python
subprocess.run(["cat", "my file.txt"])
```

초보자가 자주 하는 오해:

- "공백이 있으니 shell이 필요하다" -> 아니다. `argv` 원소 하나면 된다.
- "`$HOME`을 쓰고 싶으니 shell이 필요하다" -> 변수 확장이 필요할 때만 그렇다. literal 값이면 필요 없다.
- "문자열로 한 번에 쓰는 편이 쉬우니 shell이 맞다" -> 쉬워 보여도 parsing boundary가 늘어난다.

즉 실행 파일 하나를 인자와 함께 띄우는 일은 보통 shell 일이 아니라 **OS process spawn + `argv` 전달 문제**다.

## 2. shell built-in은 왜 shell이 직접 해야 하나

대표 예시는 이것들이다.

- `cd`
- `export`
- `unset`
- `alias`
- `umask`
- `source` 또는 `.`
- `jobs`, `fg`, `bg`, `disown`

이 명령들은 "외부 실행 파일 하나를 띄운다"보다 **현재 shell 프로세스의 상태를 바꾼다**에 가깝다.

예를 들어 `cd`는 현재 shell의 working directory를 바꿔야 한다.

```bash
cd /tmp
pwd
```

만약 shell이 아니라 별도 child process가 `cd /tmp`를 하고 바로 끝나면, 부모 shell의 working directory는 그대로다.
그래서 `cd`는 `/usr/bin/cd` 같은 외부 명령으로 두어도 원하는 효과가 없다.

`export DEBUG=1`도 같은 종류다.

- child shell이 `export`하면 그 child의 environment만 바뀐다
- 사용자가 계속 쓰는 현재 shell의 environment는 안 바뀐다

`jobs`, `fg`, `bg`, `disown`도 shell job table을 다루므로 같은 축이다.
이 계열은 [Shell Job-Control Command Bridge](./shell-job-control-command-bridge.md)로 바로 이어진다.

## 3. shell syntax는 "실행 파일"이 아니라 "언어"다

이제 built-in이 아니라 syntax 쪽을 보자.

```bash
grep foo *.log | sort > out.txt
```

이 한 줄에서 shell이 하는 일은 많다.

- 공백 기준 토큰화
- `*.log` glob 확장
- `|`를 보고 pipe 생성
- `>`를 보고 output redirection 구성
- 각 command의 실행 순서와 fd 배선 결정

즉 `|`, `>`, `&&`, `||`, `;`, `$(...)`, `$VAR` 같은 것들은 실행 파일 이름이 아니라 **shell parser가 해석해야 하는 문법**이다.

그래서 아래 둘은 같은 뜻이 아니다.

```python
subprocess.run(["grep", "foo", "*.log"])
subprocess.run("grep foo *.log", shell=True)
```

- 첫 번째는 `grep`이 literal `*.log`를 인자로 받는다
- 두 번째는 shell이 `*.log`를 먼저 확장한 뒤 `grep`을 실행한다

## 4. shell 없이도 구현 가능한 것과 아닌 것

초보자가 헷갈리는 지점이라 따로 분리하는 편이 좋다.

| 하고 싶은 일 | shell 없이 가능한가 | 이유 |
|---|---|---|
| 실행 파일 하나를 인자와 함께 실행 | 가능 | `argv`만 넘기면 된다 |
| stdout을 파일로 redirect | 가능 | runtime이 file open + `dup2()`를 직접 하면 된다 |
| 두 프로세스를 pipe로 연결 | 가능 | runtime이 `pipe()`와 fd 배선을 직접 하면 된다 |
| 여러 command를 `&&` 의미로 조건 실행 | 가능 | 런타임 코드가 exit status를 보고 분기하면 된다 |
| `cd`로 부모 shell 디렉터리 변경 | 불가 | 현재 shell 프로세스 상태를 바꿔야 한다 |
| `export`로 부모 shell 환경 변경 | 불가 | 현재 shell의 environment를 바꿔야 한다 |
| `source env.sh`로 현재 shell에 설정 반영 | 불가 | child가 아니라 현재 shell에서 실행해야 한다 |

핵심은 이것이다.

> pipe/redirection은 shell이 "해석하고 구성해 주는 편의 문법"인 경우가 많고, `cd`/`export`/`source`는 shell 자신이 아니면 효과를 낼 수 없는 명령이다.

그래서 "shell이 필요하다"도 두 종류로 나뉜다.

- **syntax convenience** 때문에 shell을 쓰는 경우
- **shell state mutation** 때문에 shell이 반드시 필요한 경우

두 번째가 더 강한 의미의 "정말 shell이 필요함"이다.

## 5. subprocess에서 바로 적용하는 실전 규칙

| 상황 | beginner 기본값 | 이유 |
|---|---|---|
| 실행 파일 하나를 띄운다 | `["cmd", "arg1", "arg2"]` 형태 | direct `argv`가 가장 단순하다 |
| glob, pipeline, redirection이 필요하다 | 먼저 shell syntax인지, runtime 배선으로 대체 가능한지 본다 | shell parser를 추가할지 명확히 결정해야 한다 |
| `cd`, `export`, `source`를 "실행"하고 싶다 | "이 효과를 어느 shell에 남겨야 하지?"를 먼저 묻는다 | child에서 실행하면 부모 shell 상태는 안 바뀐다 |
| shell built-in과 external command가 헷갈린다 | `type <command>` 또는 `command -V <command>`로 확인한다 | shell이 builtin/alias/function/file 중 무엇으로 보는지 드러난다 |

예를 들어 Python에서 아래 두 요청은 성격이 다르다.

```python
subprocess.run(["git", "status"])
subprocess.run("cd repo && git status", shell=True)
```

첫 번째는 external command 실행이다.
두 번째는 `cd`라는 built-in과 `&&`라는 shell syntax를 같이 쓰므로 shell을 거친다.

하지만 애플리케이션 코드에서는 더 자주 이렇게 쓴다.

```python
subprocess.run(["git", "status"], cwd="repo")
```

즉 "`cd`가 필요해 보인다"가 종종 "`spawn 옵션으로 현재 작업 디렉터리를 지정하면 된다`"로 바뀔 수 있다.
이런 종류는 shell built-in을 흉내 내기보다 **runtime API가 이미 제공하는 launch option**을 먼저 찾는 편이 낫다.

## 자주 헷갈리는 포인트

- "`echo`는 built-in이니까 shell 없이는 못 쓴다" -> shell built-in `echo`가 있어도 `/bin/echo` 같은 external command가 함께 있는 경우가 많다. command마다 다르다.
- "`test`는 항상 실행 파일이다" -> shell built-in일 수도 있고 `/usr/bin/test`일 수도 있다.
- "`cd`를 subprocess로 실행했는데 왜 디렉터리가 안 바뀌지?" -> child process 안에서만 바뀌고 부모 shell은 그대로이기 때문이다.
- "`export FOO=1`을 child shell에서 실행했으니 다음 subprocess도 보겠지?" -> 그 child가 끝나면 그 environment 변화도 같이 사라진다.
- "`pipe`나 `>`를 쓰니 무조건 shell을 써야 한다" -> shell이 가장 쉬운 구현일 수는 있지만, 런타임이 직접 pipe/redirection을 구성할 수도 있다.

## 꼬리질문

> Q: shell 없이 command를 실행한다는 건 정확히 무슨 뜻인가요?
> 핵심: 문자열을 shell이 해석하지 않고, runtime이 실행 파일 하나와 `argv` 배열을 직접 넘긴다는 뜻이다.

> Q: 왜 `cd`는 external command처럼 다루면 안 되나요?
> 핵심: 효과가 child가 아니라 현재 shell 프로세스에 남아야 하기 때문이다.

> Q: 왜 `grep foo *.log`는 list argv와 shell string이 다르게 동작하나요?
> 핵심: `*.log`를 shell이 먼저 확장하느냐, 아니면 target program이 literal 문자열로 받느냐가 다르다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "Python `shell=True`, Java `ProcessBuilder`, Node `exec()`/`spawn({ shell: true })` 차이를 언어별 표로 보고 싶다면": [Runtime Shell Option Matrix](./runtime-shell-option-matrix.md)
> - "`shell=True`가 parser/process boundary를 왜 늘리는지"를 이어 보고 싶다면: [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
> - "`PIPE`, `cwd`, `close_fds` 같은 runtime 옵션을 OS 그림으로 다시 읽고 싶다면": [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
> - "`jobs`, `fg`, `bg`, `disown`가 왜 shell built-in인지"를 보고 싶다면: [Shell Job-Control Command Bridge](./shell-job-control-command-bridge.md)
> - "`spawn` 자체가 OS에서는 어떤 API 축으로 나뉘는지"를 정리하고 싶다면: [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

external command 실행은 보통 direct `argv` launch면 충분하고, shell built-in은 현재 shell 상태를 바꿔야 해서 shell이 직접 해야 하며, `|`/`>`/`&&` 같은 것은 shell 언어 문법이라 누군가 그 문법을 해석해야 한다.
