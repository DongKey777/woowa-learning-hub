# `Killed`, `OOMKilled`, `memory.events`를 한 장면으로 읽는 입문 메모

> 한 줄 요약: 앱 로그의 `Killed`, Kubernetes의 `OOMKilled`, cgroup의 `memory.events`는 "메모리 한도에 부딪혀 커널이 프로세스를 정리했다"는 같은 사건을 서로 다른 높이에서 보여 주는 표지판이다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [메모리 관리 기초](./memory-management-basics.md) 다음에 읽는 beginner bridge다. 메모리 문제를 처음 볼 때 `Killed`와 `OOMKilled`를 따로 외우지 않고 같은 멘탈 모델로 묶게 돕는다.

**난이도: 🟢 Beginner**

관련 문서:

- [메모리 관리 기초](./memory-management-basics.md)
- [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
- [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
- [signals, process supervision](./signals-process-supervision.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: killed oomkilled memory.events beginner, killed vs oomkilled, app log killed meaning, kubernetes oomkilled meaning, memory.events oom_kill beginner, cgroup memory events primer, oom beginner mental model, oom 표기 해석, killed 로그 의미, oomkilled 뜻, memory.events 읽는 법 입문, 메모리 한도 초과 멘탈 모델, cgroup oom beginner bridge, normal exit vs killed, signal stop vs oom kill

## 먼저 잡는 멘탈 모델

- 같은 교통사고를 CCTV, 교통 앱, 경찰 기록이 각자 다르게 적는다고 생각하면 된다.
- `Killed`는 애플리케이션 쪽에서 본 짧은 결과다.
- `OOMKilled`는 Kubernetes가 붙여 준 "왜 죽었는지" 라벨이다.
- `memory.events`는 cgroup이 남긴 커널 쪽 카운터다.

즉, 이름은 달라도 초보자 관점에서 먼저 잡아야 할 그림은 하나다.

> "프로세스가 메모리 한도에 부딪혔고, 커널이 살리기보다 종료를 선택했다."

## 한눈에 보기

| 어디서 보나 | 흔한 표기 | 초보자 1차 해석 |
| --- | --- | --- |
| 앱/쉘 로그 | `Killed` | 프로세스가 외부에서 종료됐다. 메모리 OOM일 가능성을 먼저 의심한다. |
| Kubernetes 상태 | `OOMKilled` | 컨테이너 메모리 한도 쪽 OOM으로 죽었다는 운영 플랫폼의 요약이다. |
| cgroup 파일 | `memory.events`의 `oom`, `oom_kill` 증가 | 메모리 한도 압박과 실제 kill 이벤트가 커널 기록에 남았다. |

초보자에게 중요한 포인트는 "셋 중 하나만 봐도 다른 둘을 연결해서 떠올릴 수 있어야 한다"는 점이다.

## `Killed`가 다 같은 종료는 아니다

처음에는 종료를 세 갈래로만 나눠 생각하면 된다.

| 종료 장면 | 보통 누가 끝내나 | 초보자에게 보이는 흔한 단서 | `memory.events` |
| --- | --- | --- | --- |
| 정상 종료 | 프로그램 자신 | `Exited`, 종료 코드 `0` 또는 앱이 정한 에러 코드 | 보통 변화 없음 |
| 일반 signal 종료 | 사용자, supervisor, runtime | `Terminated`, `SIGTERM`, 때로는 종료 코드 `143`/`137` | 보통 변화 없음 |
| OOM 계열 종료 | 커널이 메모리 한도 압박에서 희생 프로세스를 정리 | 앱 로그 `Killed`, 플랫폼 이유 `OOMKilled`, 종료 코드 `137`가 함께 보일 수 있음 | `oom_kill` 증가 가능 |

핵심은 이것이다.

- `Killed`나 종료 코드 `137`만으로는 "무조건 OOM"이라고 단정하지 않는다.
- OOM 쪽은 `OOMKilled`, `memory.events`의 `oom_kill`, 메모리 한도 문맥이 같이 붙을 때 더 강해진다.
- 즉 "종료 결과"와 "종료 이유"를 분리해서 읽어야 한다.

## 아주 작은 예시

어느 파드가 재시작됐다고 가정해 보자.

1. 앱 로그에는 마지막 줄이 `Killed`다.
2. `kubectl describe pod`를 보면 종료 이유가 `OOMKilled`다.
3. 같은 컨테이너 cgroup의 `memory.events`를 보면 `oom_kill` 값이 이전보다 1 늘어 있다.

이 셋은 서로 다른 원인이 아니라, 같은 사건을 다른 관찰 지점에서 본 것이다.

## 자주 헷갈리는 포인트

- `Killed`만 봤다고 해서 항상 OOM이라고 단정하면 안 된다. 다만 메모리 문맥이라면 가장 먼저 연결해 볼 표지판은 맞다.
- 종료 코드 `137`도 단독으로는 OOM 확정이 아니다. 일반 `SIGKILL`과 OOM kill이 같은 숫자로 보일 수 있다.
- `OOMKilled`가 보인다고 해서 호스트 전체 메모리가 바닥났다는 뜻은 아니다. 컨테이너 cgroup 한도만 넘겨도 이렇게 보일 수 있다.
- `memory.events`는 로그 문장이 아니라 누적 카운터다. 값이 늘었는지 전후 비교로 읽어야 한다.
- `oom`과 `oom_kill`은 같은 글자가 아니어도 된다. 초보자 1차 독해에서는 "`oom_kill`이 늘었는가"를 더 직접적인 신호로 보면 된다.

## 처음 보는 사람용 최소 체크 순서

| 순서 | 무엇을 보나 | 왜 이 순서인가 |
| --- | --- | --- |
| 1 | 앱 로그의 `Killed` | 사용자가 제일 먼저 마주치는 표면 증상이라서 |
| 2 | Kubernetes의 `OOMKilled` 여부 | 플랫폼이 메모리 종료로 해석했는지 빠르게 확인하려고 |
| 3 | `memory.events`의 `oom_kill` 변화 | 커널/cgroup 쪽 기록으로 같은 사건을 교차 확인하려고 |

여기까지 확인했으면 초보자 단계에서는 "메모리 축 문제일 가능성이 높다"까지 잡으면 충분하다. 왜 limit를 넘었는지, `memory.high`를 어떻게 잡아야 하는지 같은 운영 상세는 다음 문서로 넘기면 된다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`OOMKilled`가 왜 호스트 전체 OOM과 다를 수 있는지"가 궁금하면: [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - "`SIGTERM`/`SIGKILL` 같은 일반 종료와 무엇이 다른지"를 더 보려면: [signals, process supervision](./signals-process-supervision.md)
> - "`memory.high`와 `memory.max`가 어떻게 다른지"까지 이어서 보려면: [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
> - 메모리 primer부터 다시 잡고 싶으면: [메모리 관리 기초](./memory-management-basics.md)

## 한 줄 정리

앱 로그의 `Killed`, Kubernetes의 `OOMKilled`, cgroup의 `memory.events`는 "메모리 한도에 부딪혀 커널이 프로세스를 정리했다"는 같은 사건을 서로 다른 높이에서 보여 주는 표지판이다.
