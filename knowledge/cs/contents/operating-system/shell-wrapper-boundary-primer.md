---
schema_version: 3
title: shell=True Shell Wrapper Boundary Primer
concept_id: operating-system/shell-wrapper-boundary-primer
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 73
review_feedback_tags:
- shell-wrapper-boundary
- shell-true-shell
- wrapper
- sh-c-boundary
aliases:
- shell=True shell wrapper
- sh -c boundary
- shell script wrapper
- command string shell parsing
- shell quoting security fd leak
- parent shell app process tree
intents:
- definition
- troubleshooting
linked_paths:
- contents/operating-system/popen-runtime-wrapper-mapping.md
- contents/operating-system/runtime-shell-option-matrix.md
- contents/operating-system/shell-redirection-order-primer.md
- contents/operating-system/subprocess-fd-hygiene-basics.md
- contents/operating-system/o-cloexec-fd-inheritance-exec-leaks.md
expected_queries:
- shell=True나 sh -c를 쓰면 target program을 직접 띄우는 것과 무엇이 달라?
- shell wrapper가 quoting, security, fd leak 이야기를 함께 부르는 이유는?
- parent -> shell -> app process tree에서 signal과 fd는 어떻게 보이나?
- command string이 shell 문법으로 다시 해석된다는 뜻은?
contextual_chunk_prefix: |
  이 문서는 shell=True, sh -c, shell script wrapper가 target program을 직접 띄우지 않고 shell을
  한 겹 더 거치게 하므로 command string parsing, quoting, redirection, fd visibility,
  signal delivery가 달라진다는 beginner primer다.
---
# `shell=True` / Shell Wrapper Boundary Primer

> 한 줄 요약: `shell=True`, `sh -c`, shell script wrapper는 target program을 직접 띄우지 않고 shell을 한 번 더 거치게 만든다. 그래서 command string은 shell 문법으로 다시 해석되고, 열린 fd도 먼저 shell에 보인다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md) 다음에 읽는 beginner bridge다. "`shell=True`가 왜 quoting, security, fd leak 이야기를 한꺼번에 부르지?"를 한 장에서 묶어 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Runtime Shell Option Matrix](./runtime-shell-option-matrix.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Wrapper `exec` Handoff Timeline](./wrapper-exec-handoff-timeline.md)
- [Shell Redirection Order Primer](./shell-redirection-order-primer.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Session vs Process Group Primer](./session-vs-process-group-primer.md)
- [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
- [입력값 검증 기초](../security/input-validation-basics.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: shell wrapper boundary primer, shell=true mental model, python subprocess shell true, sh -c extra process, shell quoting boundary, fd inheritance shell wrapper, pipe eof shell wrapper, shell true eof delay, shell wrapper fd leak illusion, shell command wrapper 뭐예요, quoting 처음 배우는데, direct spawn vs shell wrapper, shell wrapper boundary primer basics, shell wrapper boundary primer beginner, shell wrapper boundary primer intro

## 먼저 잡는 멘탈 모델

같은 "외부 명령 실행"처럼 보여도 머릿속 그림은 둘로 나뉜다.

```text
direct spawn
  parent -> target program

shell wrapper
  parent -> shell -> target program
```

`subprocess.run(["grep", "foo", "file.txt"])`는 보통 target의 `argv`를 직접 넘기는 쪽이고, `subprocess.run("grep foo file.txt", shell=True)`나 `sh -c "..."`는 shell wrapper를 거치는 쪽이다.

초보자용으로는 이 문장 하나가 핵심이다.

> shell wrapper는 "실행 대상 앞에 shell이라는 parser/process를 한 겹 더 두는 것"이다.

일부 단순한 경우 shell이 마지막에 `exec`로 자기 자신을 교체할 수도 있지만, beginner mental model은 "shell이 먼저 명령 문자열을 읽고 나서 다음 프로그램을 고른다"로 두는 편이 안전하다.

## 한눈에 보기

| 항목 | direct spawn | shell wrapper |
|---|---|---|
| parent가 직접 넘기는 것 | 이미 나뉜 `argv` 배열 | 한 줄 command string |
| 중간 parser | 없다 | shell이 공백, 따옴표, `*`, `$VAR`, `|`, `>`를 다시 해석한다 |
| process tree 감각 | `parent -> app` | 보통 `parent -> shell -> app` |
| fd를 먼저 보는 주체 | target program | shell이 먼저 보고, 그다음 shell이 띄운 program이 본다 |
| beginner 기본값 | 일반 명령 실행에 적합 | shell 문법이 정말 필요할 때만 선택 |

즉 `shell=True`는 단순한 문법 설탕이 아니라, **parsing boundary와 process boundary를 같이 하나 더 추가하는 선택**이다.

## 왜 shell wrapper가 한 겹 더 생기나

shell wrapper가 필요한 대표 이유는 shell 문법 자체를 쓰고 싶을 때다.

- pipeline: `cmd1 | cmd2`
- redirection: `cmd > out.txt 2>&1`
- glob: `*.log`
- shell built-in: `cd`, `export`, `test`

이런 문법이 필요하면 누군가는 shell parser를 실행해야 한다. 그래서 runtime은 보통 `/bin/sh -c "..."` 같은 형태로 shell을 먼저 띄운다.
여기서 `cmd > out.txt 2>&1`와 `cmd 2>&1 > out.txt`가 왜 다른지는 shell이 redirection을 왼쪽부터 적용하기 때문이다. 이 순서 자체는 [Shell Redirection Order Primer](./shell-redirection-order-primer.md)에서 따로 짧게 본다.

```python
subprocess.run(["ls", "*.log"])
subprocess.run("ls *.log", shell=True)
```

위 두 줄은 같은 뜻이 아니다.

- 첫 번째는 target program이 literal `*.log`를 인자로 받는다
- 두 번째는 shell이 먼저 `*.log`를 확장한 뒤 target을 실행한다

즉 "문자열 한 줄로 편하게 실행"은 사실상 "shell language로 다시 한 번 해석"을 뜻한다.

## quoting boundary를 따로 봐야 하는 이유

shell wrapper가 끼면 **데이터와 문법의 경계**가 바뀐다.

| 내가 원한 것 | direct spawn | shell wrapper |
|---|---|---|
| 공백이 있는 파일명 `my file.txt` | `["cat", "my file.txt"]`처럼 그대로 전달 | shell에서 따옴표나 escape를 정확히 맞춰야 한다 |
| literal `*.log` | target이 그대로 `*.log`를 본다 | shell이 glob을 확장할 수 있다 |
| literal `$HOME` | target이 그대로 `$HOME`를 본다 | shell이 변수 치환을 할 수 있다 |

예를 들어:

```python
subprocess.run(["cat", "my file.txt"])
subprocess.run("cat my file.txt", shell=True)
subprocess.run("cat 'my file.txt'", shell=True)
```

여기서 두 번째 줄은 shell이 공백으로 단어를 나누기 때문에 `my`와 `file.txt`를 다른 인자로 볼 수 있다. 세 번째 줄처럼 shell quoting을 따로 맞춰야 비슷한 결과가 나온다.

그래서 user input이나 파일명을 command string에 그냥 이어 붙이면, 원래는 "데이터"였어야 할 값이 shell 문법처럼 읽힐 수 있다. 이 감각은 [입력값 검증 기초](../security/input-validation-basics.md)에서 보는 "구조와 값을 분리하라"는 원칙과 닮아 있다.

## fd inheritance를 beginner-safe하게 보면

fd 관점에서도 shell wrapper는 한 겹 더 생긴다.

```text
parent opens pipe/socket/fd
  -> shell wrapper starts
  -> shell sees inherited fd first
  -> shell launches app/helper
```

`close_fds`나 `CLOEXEC` 정책이 약하면 target program만이 아니라 shell도 그 fd를 볼 수 있고, shell이 띄운 다음 helper까지 이어받을 수 있다. 그래서 shell wrapper에서는 fd leak 범위가 더 넓어지기 쉽다.

초보자에게 필요한 기본 규칙은 네 가지다.

- 일반 명령 실행은 가능하면 `argv` 리스트로 직접 띄운다
- `close_fds` 기본값과 `CLOEXEC` 습관을 유지한다
- 꼭 넘길 fd만 `pass_fds` 같은 방식으로 예외 처리한다
- shell script wrapper가 단순 hand-off 역할이면 마지막을 `exec real-app "$@"` 형태로 끝내 extra holder를 줄인다

pipe EOF가 늦게 오면 app만 보지 말고 shell/wrapper도 같이 봐야 한다. wrapper가 아직 살아 있거나, wrapper가 띄운 다른 child가 write end를 계속 들고 있을 수 있기 때문이다. 더 자세한 기본 규칙은 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)에서 이어서 보면 된다.
여기서 왜 `exec real-app "$@"`가 extra PID, signal hop, fd holder를 줄이는지는 [Wrapper `exec` Handoff Timeline](./wrapper-exec-handoff-timeline.md)에서 timeline으로 따로 떼어 설명한다.

## 작은 예시로 보는 EOF 지연과 fd 상속 착시

같은 hang라도 direct spawn과 shell wrapper는 "누가 아직 pipe write end를 들고 있나"가 다르게 보일 수 있다.

| 실행 모양 | 겉으로 보이는 대상 | 실제 holder 후보 | 초보자 착시 |
|---|---|---|---|
| `Popen(["cat"], stdin=PIPE)` | `cat` 하나 | parent, `cat` | "`cat`만 보면 되겠지" |
| `Popen("cat", shell=True, stdin=PIPE)` | `cat`을 실행한 것처럼 보임 | parent, shell, shell이 띄운 helper | "`cat`이 안 끝나네` -> 실제로는 wrapper 쪽이 write end를 쥘 수 있다" |

예를 들어 batch형 child를 shell 없이 띄우면 그림이 단순하다.

```python
p = subprocess.Popen(["sort"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
p.stdin.write("b\na\n")
# p.stdin.close()를 안 하면 sort는 EOF를 못 보고 계속 read()할 수 있다.
```

여기에 shell을 끼우면 멘탈 모델이 한 단계 늘어난다.

```python
p = subprocess.Popen("sort", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
p.stdin.write("b\na\n")
# parent가 안 닫았거나 wrapper 쪽 프로세스가 write end를 들고 있으면
# 겉보기에는 sort가 느린 것 같아도 실제 원인은 EOF 미전달일 수 있다.
```

핵심은 "`shell=True`라서 무조건 느리다"가 아니다. shell이 끼면 **EOF를 늦출 수 있는 holder 후보가 하나 더 생긴다**는 뜻이다.

fd 상속도 비슷한 착시를 만든다. 예를 들어 parent가 우연히 열어 둔 admin socket이나 temp fd가 있고 close policy가 약하면, 초보자는 "target app이 그 fd를 직접 물고 갔다"고 생각하기 쉽다. 하지만 실제로는 `parent -> shell -> app` 경로에서 shell도 먼저 그 fd를 상속받았고, shell이 띄운 다른 helper가 계속 들고 있을 수도 있다.

그래서 shell wrapper가 끼는 순간 점검 순서는 보통 이렇게 잡는 편이 안전하다.

- target app만 보지 말고 shell/wrapper PID도 같이 본다
- EOF가 안 오면 "누가 write end를 아직 들고 있나"를 먼저 묻는다
- fd leak가 의심되면 "target에 바로 갔나?"보다 "shell 단계에서도 한 번 퍼졌나?"를 먼저 의심한다

## 흔한 오해와 함정

- "`shell=True`는 공백 있는 파일명 때문에 필요하다" -> 보통 아니다. 공백은 `argv` 배열 원소 하나로 넘기면 된다.
- "문자열 안의 따옴표가 target program까지 그대로 간다" -> shell mode에서는 따옴표가 shell parser를 위한 경우가 많고, 최종 `argv`에서는 사라질 수 있다.
- "`shell=True`는 security 문제만 만든다" -> security뿐 아니라 process tree, fd inheritance, EOF timing, signal 경로까지 바꾼다.
- "출력이 늦게 보이면 무조건 shell 탓이다" -> buffering이나 PTY/pipe 차이일 수도 있다. [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md), [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)와 분리해서 보는 편이 안전하다.

## 실무에서 쓰는 모습

| 목표 | beginner 기본값 | 이유 |
|---|---|---|
| 프로그램 하나를 인자와 함께 실행 | direct spawn (`argv` 리스트) | shell parser와 extra process를 건너뛴다 |
| pipeline, redirection, glob이 정말 필요함 | shell wrapper를 의도적으로 사용 | 이 경우는 shell language를 쓰겠다는 뜻이다 |
| wrapper script가 환경 설정만 하고 앱으로 넘김 | 마지막에 `exec app "$@"` | PID/fd/signal 경로를 덜 꼬이게 한다 |
| user input이 명령 일부로 들어감 | 가능한 한 shell string을 피함 | 데이터가 shell 문법으로 승격되는 것을 막는다 |

즉 shell wrapper는 "항상 금지"가 아니라, **shell 문법을 살 가치가 있을 때만 의식적으로 쓰는 도구**로 보는 편이 맞다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "Python `shell=True`, Java `ProcessBuilder`, Node `exec()`/`spawn({ shell: true })`를 한 표로 다시 맞춰 보고 싶다면": [Runtime Shell Option Matrix](./runtime-shell-option-matrix.md)
> - "`PIPE`, `close_fds`, `pass_fds`가 실제 fd 작업으로 어떻게 번역되는지"를 다시 보고 싶다면: [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
> - "wrapper 마지막의 `exec app \"$@\"`가 왜 PID/signal/fd를 덜 꼬이게 하지?"를 바로 잇고 싶다면: [Wrapper `exec` Handoff Timeline](./wrapper-exec-handoff-timeline.md)
> - "`shell wrapper 때문에 EOF가 늦는가, fd leak인가"를 먼저 분기하고 싶다면: [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - "`Ctrl-C`, foreground job, shell bookkeeping"까지 이어 보고 싶다면: [Session vs Process Group Primer](./session-vs-process-group-primer.md)
> - 운영체제 입문 primer 묶음으로 돌아가려면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

`shell=True`나 shell wrapper는 "command string을 shell이 한 번 더 해석하고, 열린 fd도 먼저 shell에 보이게 하는 extra boundary"다. 일반 명령 실행은 direct spawn을 기본값으로 두고, shell 문법이 필요할 때만 의도적으로 올리는 편이 안전하다.
