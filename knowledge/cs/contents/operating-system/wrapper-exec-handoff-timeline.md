---
schema_version: 3
title: Wrapper exec Handoff Timeline
concept_id: operating-system/wrapper-exec-handoff-timeline
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 73
review_feedback_tags:
- wrapper-exec-handoff
- timeline
- exec-app
- shell-wrapper-final
aliases:
- wrapper exec handoff
- exec app "$@"
- shell wrapper final exec
- PID signal fd handoff
- wrapper child vs replacement
- container entrypoint exec
intents:
- definition
- troubleshooting
linked_paths:
- contents/operating-system/shell-wrapper-boundary-primer.md
- contents/operating-system/container-pid-1-sigterm-zombie-reaping-basics.md
- contents/operating-system/process-spawn-api-comparison.md
- contents/operating-system/o-cloexec-fd-inheritance-exec-leaks.md
- contents/operating-system/signals-process-supervision.md
expected_queries:
- shell wrapper 마지막에 exec app \"$@\"를 쓰면 PID, signal, fd tracking이 왜 단순해져?
- wrapper가 child를 하나 더 들고 있는 구조와 wrapper 자신이 app으로 교체되는 구조는 어떻게 달라?
- container entrypoint script에서 마지막 exec가 중요한 이유는?
- exec handoff timeline으로 shell wrapper process tree를 설명해줘
contextual_chunk_prefix: |
  이 문서는 shell wrapper가 마지막에 exec app "$@"를 쓰면 wrapper가 child를 하나 더 들고 있는
  구조가 아니라 wrapper process image가 app으로 교체되어 PID, signal, fd 추적이 단순해지는
  timeline을 설명한다.
---
# Wrapper `exec` Handoff Timeline

> 한 줄 요약: shell wrapper가 마지막에 `exec app "$@"`를 쓰면 "wrapper가 child를 하나 더 들고 있는 구조"가 아니라 "wrapper 자신이 app으로 교체되는 구조"가 되어 PID, signal, fd 추적이 훨씬 단순해진다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)와 [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md) 사이를 잇는 beginner bridge다. "wrapper script는 왜 마지막에 꼭 `exec`로 넘기라고 하지?"를 timeline 하나로 설명한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
- [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [signals, process supervision](./signals-process-supervision.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: operating-system-00076, wrapper exec handoff timeline, exec app "$@" primer, shell wrapper exec handoff, entrypoint exec handoff, container entrypoint exec why, shell script exec app, exec replaces shell, extra pid wrapper, pid signal fd confusion, shell wrapper pid confusion, shell wrapper signal forwarding, shell wrapper fd holder, container entrypoint pid 1 exec, beginner exec handoff

## 먼저 잡는 멘탈 모델

wrapper script에서 마지막 한 줄은 보통 둘 중 하나다.

```sh
# case 1: child를 하나 더 만든다
app "$@"

# case 2: wrapper 자신을 app으로 교체한다
exec app "$@"
```

둘 다 "결국 app이 실행된다"는 점은 같아 보여서 초보자가 차이를 놓치기 쉽다.
하지만 운영체제 관점에서는 process tree가 다르다.

```text
without exec
  parent -> wrapper -> app

with exec
  parent -> app
  (wrapper PID가 app으로 바뀜)
```

초보자용으로는 이 문장 하나가 핵심이다.

> `exec app "$@"`는 "wrapper가 app을 실행한다"가 아니라 "wrapper 자리에 app이 들어온다"에 가깝다.

## 한눈에 보기

| 비교 항목 | `app "$@"` | `exec app "$@"` |
|---|---|---|
| 추가 PID | wrapper와 app이 둘 다 남는다 | wrapper PID가 app으로 바뀌어 extra PID가 없다 |
| signal first stop | 보통 wrapper가 먼저 받는다 | app이 바로 받는다 |
| child reaping 책임 | wrapper가 forwarding/reaping을 고민해야 한다 | app이 직접 받거나, 별도 init를 둘지 명확해진다 |
| pipe/socket fd holder | wrapper와 app이 동시에 들고 있을 수 있다 | wrapper가 사라져 extra holder 하나가 줄어든다 |
| container PID 1 해석 | shell이 PID 1로 남기 쉽다 | app이 PID 1이 되기 쉽다 |
| beginner 기본값 | 특별한 이유 없으면 피한다 | 단순 handoff wrapper의 기본값으로 안전하다 |

## timeline으로 보면 왜 다른가

### 1. `exec` 없이 넘길 때

```sh
#!/bin/sh
setup_env
app "$@"
```

timeline은 보통 이렇게 읽는다.

```text
wrapper starts
  -> wrapper does setup
  -> wrapper forks/spawns app
  -> app runs as wrapper child
  -> signal often reaches wrapper first
  -> wrapper may need to forward signal
  -> wrapper may keep inherited fd open until it exits
  -> wrapper waits or exits separately
```

이 구조에서 초보자가 자주 만나는 혼동은 세 가지다.

- `ps`를 보면 PID가 둘이라서 "누가 진짜 본체지?"가 흐려진다
- `SIGTERM`이 wrapper에만 먼저 들어와 app 종료가 늦어질 수 있다
- wrapper가 pipe write end나 listener fd를 잠깐 더 들고 있어 EOF나 close timing이 꼬일 수 있다

### 2. `exec`로 넘길 때

```sh
#!/bin/sh
setup_env
exec app "$@"
```

timeline은 더 짧다.

```text
wrapper starts
  -> wrapper does setup
  -> exec app "$@"
  -> same PID now runs app
  -> parent/container now sees app directly
```

핵심은 `exec()`가 새 child를 만드는 호출이 아니라는 점이다.

- wrapper PID가 그대로 app PID가 된다
- wrapper shell code는 여기서 끝난다
- wrapper가 들고 있던 불필요한 "중간 관리 책임"도 같이 사라진다

즉 handoff만 필요했던 wrapper라면 `exec`가 process tree를 목적에 더 가깝게 만든다.

## PID confusion이 줄어드는 이유

초보자가 wrapper script를 디버깅할 때 제일 먼저 막히는 질문은 이것이다.

- 왜 `ps`에 shell과 app이 둘 다 보이지?
- 누가 parent고 누가 signal을 받지?
- container에서 왜 PID 1이 app이 아니라 `sh`지?

`exec` 없이 실행하면 이런 그림이 흔하다.

```text
PID 1  sh /entrypoint.sh
PID 7  app --serve
```

`exec`로 넘기면 이렇게 단순해진다.

```text
PID 1  app --serve
```

그래서 beginner 관점에서는 "`exec`가 성능 최적화"라기보다 "**관찰 화면과 실제 책임 주체를 맞춘다**"로 이해하는 편이 쉽다.

## signal confusion이 줄어드는 이유

`SIGTERM`, `SIGINT`, `Ctrl-C`, container stop 같은 이벤트는 "누가 먼저 받는가"가 중요하다.

`exec` 없이 wrapper가 남아 있으면:

- wrapper가 먼저 signal을 받는다
- wrapper가 app에 다시 보내야 할 수 있다
- wrapper가 `wait` 중이거나 trap 로직이 어설프면 app 종료가 어긋날 수 있다

`exec`로 넘기면:

- app이 그 PID에서 바로 signal을 받는다
- signal forwarding이라는 중간 단계가 줄어든다
- container entrypoint에서는 PID 1 해석도 더 직접적이 된다

즉 "`exec`를 쓰면 signal이 더 강해진다"가 아니라, **signal path가 짧아진다**고 보는 편이 정확하다.

## fd confusion이 줄어드는 이유

wrapper가 살아 있다는 것은 열린 fd를 잡고 있는 프로세스가 하나 더 있다는 뜻이기도 하다.

예를 들어 parent가 pipe를 열고 wrapper를 띄웠다고 해 보자.

```text
parent
  -> wrapper inherits pipe write end
  -> wrapper spawns app
  -> app also inherits pipe write end
```

이제 app이 끝나도 wrapper가 아직 write end를 들고 있으면 reader는 EOF를 못 볼 수 있다.

`exec app "$@"`로 바꾸면:

```text
parent
  -> wrapper inherits pipe write end
  -> exec replaces wrapper with app
  -> extra holder process does not remain
```

물론 `exec`만으로 모든 fd leak가 해결되지는 않는다.

- `CLOEXEC`가 꺼져 있으면 원치 않는 fd가 app까지 갈 수 있다
- wrapper가 `exec` 전에 별도 helper를 띄웠다면 그 helper가 fd를 계속 들고 있을 수 있다

그래도 **"쓸모없는 shell 프로세스가 fd를 더 들고 있는 문제"**는 줄일 수 있다.
그래서 단순 handoff wrapper라면 `exec`가 beginner-safe 기본값이다.

## container entrypoint에서 특히 자주 나오는 이유

컨테이너에서는 "누가 PID 1인가"가 종료 흐름을 크게 바꾼다.

```Dockerfile
# shell form
CMD python app.py

# exec form
CMD ["python", "app.py"]
```

shell form이나 shell entrypoint가 남아 있으면 PID 1이 shell이 될 수 있다.
반대로 entrypoint script 마지막을 `exec "$@"` 또는 `exec app "$@"`로 끝내면 app이 PID 1이 되기 쉽다.

이 차이 때문에 다음 증상이 자주 갈린다.

- `docker stop`이 왔는데 app이 TERM을 바로 못 받는다
- PID 1 shell이 자식 회수 책임까지 떠안는다
- 종료는 됐는데 zombie나 delayed shutdown 해석이 어려워진다

그래서 container 문맥에서는 "`exec`를 쓰면 shell 한 겹을 치운다"라는 감각이 특히 중요하다.

## 언제 `exec`를 바로 쓰면 좋은가

| 상황 | beginner 기본값 | 이유 |
|---|---|---|
| wrapper가 env 설정 후 앱 하나로 넘기기만 함 | 마지막에 `exec app "$@"` | extra PID, signal hop, fd holder를 줄인다 |
| entrypoint script가 인자 전처리 후 최종 명령 하나 실행 | 마지막에 `exec "$@"` | container PID 1을 target command에 넘기기 쉽다 |
| shell이 app 종료 뒤 cleanup을 계속 해야 함 | 무조건 `exec`하지 말고 cleanup 설계를 먼저 명확히 함 | wrapper가 남아야 하는 이유가 실제로 있기 때문이다 |

핵심은 "`exec`가 무조건 정답"이 아니라, **wrapper의 역할이 단순 handoff인지**를 먼저 보는 것이다.

## 자주 하는 오해

- "`exec`는 child를 더 효율적으로 만드는 것이다" -> 아니다. 새 child를 만드는 게 아니라 현재 프로세스를 교체한다.
- "`exec`를 쓰면 fd가 자동으로 전부 닫힌다" -> 아니다. `CLOEXEC`가 아닌 fd는 새 프로그램에도 남을 수 있다.
- "`exec`를 쓰면 signal 문제는 100% 끝난다" -> 아니다. app 자체가 signal을 잘 처리해야 한다.
- "entrypoint script에서는 그냥 shell이 남아 있어도 비슷하다" -> 단순 handoff라면 PID 1, signal, wait 책임이 분산돼 초보자에게 훨씬 헷갈려진다.

## 꼬리질문

> Q: `exec app "$@"`를 쓰면 왜 `ps`에서 shell이 안 보이나요?
> 핵심: shell이 child를 만든 게 아니라 자기 자신이 app으로 교체됐기 때문이다.

> Q: `exec`만 쓰면 zombie 문제가 자동으로 사라지나요?
> 핵심: 아니다. app이 다시 child를 만들면 그 child의 종료 처리 책임은 여전히 남는다.

> Q: wrapper에서 `trap`이나 cleanup을 하고 싶은데도 `exec`를 써야 하나요?
> 핵심: handoff 뒤에도 wrapper가 살아 있어야 할 명확한 일이 있으면 별도 설계를 해야 한다. 단순 전달만 한다면 `exec`가 더 안전하다.

## 여기까지 이해했으면 다음 문서

> **Beginner handoff box**
>
> - shell이 한 겹 더 생기는 기본 그림부터 다시 잡고 싶다면: [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
> - container PID 1, `SIGTERM`, zombie 회수까지 잇고 싶다면: [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
> - `CLOEXEC`, EOF 지연, leaked fd 쪽을 더 분리해 보고 싶다면: [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - `exec()`가 "새 프로세스 생성"이 아니라 "현재 프로세스 교체"라는 점을 다시 고정하고 싶다면: [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)

## 한 줄 정리

wrapper script나 container entrypoint가 단순히 앱으로 넘기는 역할이라면 `exec app "$@"`는 extra PID 하나를 없애고, 그만큼 signal 경로와 fd holder를 줄여서 shutdown과 EOF 해석을 beginner-friendly하게 만든다.
