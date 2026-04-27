# CI Log Merge Behavior Primer

> 한 줄 요약: test runner나 CI가 child의 stdout/stderr를 따로 받으면 각 stream 내부 순서는 대체로 유지돼도, 둘을 합친 전체 순서는 reader timing과 buffering 때문에 흔들릴 수 있다. 그래서 "무슨 일이 먼저였는가"가 중요하면 로그 줄마다 source, timestamp, sequence id를 같이 남기는 편이 안전하다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [stdout/stderr Ordering After Redirect](./stdio-buffering-after-redirect.md) 다음에 읽는 beginner bridge다. 로컬에서는 멀쩡해 보인 로그가 CI 콘솔이나 test runner transcript에서 줄 순서가 섞여 보일 때, "child buffer", "별도 pipe", "parent merge", "복원용 metadata"를 한 장면으로 묶어 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [stdout/stderr Ordering After Redirect](./stdio-buffering-after-redirect.md)
- [TTY-Aware Output Capture Patterns](./tty-aware-output-capture-patterns.md)
- [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
- [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
- [Shell Redirection Order Primer](./shell-redirection-order-primer.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Observability and Debugging Master Note](../../master-notes/observability-debugging-master-note.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: operating-system-00075, ci log merge behavior primer, ci stdout stderr merge, ci log ordering unstable, test runner stdout stderr merge, separate pipes merged transcript, global order unstable logs, stdout stderr timestamps sequence ids, ci console interleaving, github actions stdout stderr order, junit runner merged logs, child stdout stderr separate readers, per stream ordering only, line merge timing, log source field stdout stderr, monotonic timestamp logs, sequence id log ordering, merged transcript meaning preservation, flaky ci log order, redirect ordering in ci, stdout stderr transcript reconstruction, beginner ci logging primer, ci merged log sequence number, ci merged log timestamp strategy

## 먼저 잡는 멘탈 모델

CI나 test runner는 흔히 child 프로세스를 이렇게 붙잡는다.

```text
child stdout -> pipe A -> reader A
child stderr -> pipe B -> reader B
reader A/B가 읽은 결과를
CI 콘솔 / log collector / transcript 파일에 합쳐서 기록
```

여기서 초보자가 먼저 잡아야 할 한 줄은 이것이다.

> **stdout/stderr를 따로 받은 뒤 나중에 합치면, 각 pipe 안의 순서는 비교적 남아도 둘을 가로지르는 전역 순서는 쉽게 흔들린다.**

즉 "코드에서 먼저 실행한 로그"와 "CI 화면에 먼저 찍힌 줄"은 다를 수 있다.

## 왜 로컬과 CI가 다르게 보이나

로컬 터미널에서는 stdout/stderr가 사람이 보기엔 한 화면에서 자연스럽게 섞여 보일 수 있다.
하지만 CI나 test runner는 보통 아래 단계를 더 거친다.

1. child가 stdout/stderr에 각각 쓴다
2. 각 stream이 자기 buffer 정책대로 flush된다
3. parent reader thread/event loop가 pipe A/B를 따로 읽는다
4. CI가 읽은 chunk나 line을 자기 규칙으로 합친다
5. 웹 콘솔이나 artifact viewer가 다시 렌더링한다

그래서 CI에서는 child 바깥의 merge 단계가 하나 더 생긴다.

## 한눈에 보는 순서 보장 범위

| 무엇의 순서인가 | 흔히 어느 정도 믿을 수 있나 | 왜 한계가 생기나 |
|---|---|---|
| stdout 한 stream 내부 순서 | 비교적 유지 | 같은 fd에서 child가 쓴 순서대로 byte가 흐르기 쉽다 |
| stderr 한 stream 내부 순서 | 비교적 유지 | 이것도 같은 fd 내부 순서는 대체로 남는다 |
| stdout vs stderr 사이 전역 순서 | 약함 | separate pipes, 다른 buffering, 다른 reader timing이 개입한다 |
| CI 화면에 보인 줄 순서 | 가장 약함 | parent merge 정책, chunk split, UI flush timing까지 섞인다 |

초보자용으로는 이렇게 기억하면 충분하다.

- **한 stream 안 순서**는 상대적으로 믿기 쉽다
- **두 stream 사이 순서**는 쉽게 흔들린다

## 가장 흔한 merge 방식

CI나 runner가 stdout/stderr를 합칠 때는 보통 아래 셋 중 하나에 가깝다.

| 방식 | 어떻게 합치나 | 장점 | 흔한 오해 |
|---|---|---|---|
| read-ready 순서 merge | 먼저 읽힌 쪽 line/chunk를 바로 기록 | 구현이 단순하고 실시간성이 좋다 | "먼저 기록됐으니 child도 먼저 실행했다" |
| line-buffered merge | 줄바꿈이 생긴 단위로 합친다 | 콘솔에서 읽기 편하다 | partial line, progress bar, stack trace는 여전히 어색할 수 있다 |
| collector 재정렬 | timestamp나 내부 event time 기준으로 일부 재배열 | 화면 정리가 좋아질 수 있다 | collector 시간이 곧 child 실행 시간이라고 착각하기 쉽다 |

많은 환경은 첫 번째나 두 번째에 가깝다.
즉 **"누가 먼저 썼나"보다 "누가 먼저 읽혔나"**가 화면 순서를 만들 수 있다.

## 간단한 예시

child 코드가 아래처럼 생겼다고 하자.

```text
stdout: start test A
stderr: warning on A
stdout: finish test A
```

하지만 실제 타임라인은 이렇게 될 수 있다.

| 시점 | child 내부에서 일어난 일 | 밖에서 보일 수 있는 것 |
|---|---|---|
| 1 | stdout에 `start test A`를 씀 | stdout buffer에 잠시 머물 수 있다 |
| 2 | stderr에 `warning on A`를 씀 | stderr가 먼저 reader에 도착할 수 있다 |
| 3 | CI가 stderr pipe를 먼저 읽음 | `warning on A`가 먼저 화면에 뜬다 |
| 4 | stdout이 나중에 flush됨 | `start test A`가 뒤늦게 뜬다 |

그래서 CI transcript는 아래처럼 보일 수 있다.

```text
[stderr] warning on A
[stdout] start test A
[stdout] finish test A
```

이건 곧바로 "테스트가 warning부터 냈다"를 뜻하지 않는다.
그보다는 **merge 시점이 child 실행 시점과 다를 수 있다**는 뜻에 가깝다.

## 왜 timestamps만 있어도 충분하지 않을 때가 있나

초보자가 흔히 드는 생각은 "그럼 시간 찍으면 끝 아닌가?"다.
반은 맞고, 반은 부족하다.

| metadata | 도움이 되는 점 | 부족한 점 |
|---|---|---|
| wall-clock timestamp | 대략적인 앞뒤 관계를 본다 | clock jump, millisecond 동률, multi-process skew가 있다 |
| monotonic timestamp | 같은 프로세스 안 경과시간 비교가 안정적이다 | 다른 프로세스/머신과 바로 대조하기 어렵다 |
| sequence id | 같은 producer 안에서 정확한 순서를 강하게 남긴다 | 서로 다른 producer 사이 비교는 별도 기준이 필요하다 |
| source(stdout/stderr) | 원래 어느 stream인지 보존한다 | 시간축 자체를 복원하진 못한다 |

핵심은 이것이다.

- timestamp는 **언제쯤**을 알려 준다
- sequence id는 **같은 producer 안에서 무엇이 먼저였는지**를 강하게 알려 준다
- source는 **어느 stream에서 왔는지**를 잃지 않게 해 준다

## beginner-safe 기본 로그 필드

"전역 순서가 흔들려도 의미를 지키기"가 목표라면, 로그 한 줄마다 아래 정도를 먼저 붙이는 편이 안전하다.

| 필드 | 왜 필요한가 | 예시 |
|---|---|---|
| `source` | stdout/stderr 구분 보존 | `stdout`, `stderr` |
| `ts` | 대략적인 시간축 | `2026-04-27T10:15:31.482Z` |
| `mono_ms` | 같은 프로세스 안 상대 순서 확인 | `18342` |
| `seq` | 같은 producer 안 정확한 증가 순서 | `417` |
| `test` / `case` | 어떤 테스트/작업 줄인지 묶기 | `OrderServiceTest#timeoutCase` |

가능하면 `source + ts + seq` 조합이 최소 기본형에 가깝다.

## sequence id는 어디에 붙이나

beginner 관점에서는 어렵게 생각할 필요 없다.
중요한 것은 "누가 sequence를 소유하느냐"다.

| sequence 소유 범위 | 장점 | 한계 | 잘 맞는 경우 |
|---|---|---|---|
| process-wide 단일 seq | 가장 단순하다 | stdout/stderr가 각기 다른 logger면 연결이 번거롭다 | 한 프로세스가 한 logger로 모두 내보낼 때 |
| stream별 seq | 구현이 쉽다 | stdout seq 10과 stderr seq 10은 비교 불가 | stdout/stderr를 별도 producer로 다룰 때 |
| test-case별 seq | 케이스 단위 재구성이 쉽다 | 전역 비교는 약해진다 | 병렬 테스트 러너 |

처음에는 보통 아래 규칙만 지켜도 큰 도움이 된다.

- **한 producer 안에서는 seq가 절대 역행하지 않게 한다**
- 로그를 합칠 때 **source와 seq를 함께 보존한다**

## CI가 parent timestamp를 찍는 경우의 함정

일부 시스템은 child가 로그 시각을 넣지 않고, parent가 "읽은 순간"에 timestamp를 붙인다.
이 방식은 운영상 편하지만 해석할 때 주의가 필요하다.

| parent-read timestamp가 좋은 점 | 조심할 점 |
|---|---|
| 중앙 수집 시각이 통일된다 | child가 실제로 쓴 시각과 다를 수 있다 |
| collector 입장에서 구현이 쉽다 | pipe backlog나 reader 지연이 시간축을 밀 수 있다 |
| UI 정렬이 단순하다 | stdout/stderr 중 늦게 읽힌 쪽이 뒤늦은 사건처럼 보일 수 있다 |

그래서 중요한 incident 분석에서는 가능하면 아래 구분이 좋다.

- child event time
- collector read time

둘을 같은 뜻으로 쓰면 혼동이 커진다.

## 흔한 혼동

### "stderr가 먼저 보였으니 에러가 먼저 발생했다"

항상 그렇지는 않다. stderr가 덜 버퍼링되거나 reader가 먼저 읽었을 수 있다.

### "같은 CI job인데 로그 순서가 매번 달라진다"

이상한 일이 아닐 수 있다. separate pipes, thread scheduling, line flush timing이 조금만 달라도 merge 결과가 달라질 수 있다.

### "`2>&1`처럼 처음부터 합치면 전역 순서가 완벽히 보존된다"

부분적으로만 그렇다. child 바깥의 late merge 문제는 줄지만, child 내부 stdout/stderr buffering 차이는 여전히 남을 수 있다.

### "timestamp만 있으면 sequence id는 필요 없다"

밀리초 동률, clock skew, parent-read timestamp 같은 경우에는 여전히 모호함이 남는다. 같은 producer 안 순서를 강하게 남기려면 seq가 더 직접적이다.

## 빠른 판단표

| 지금 필요한 것 | beginner-safe 선택 |
|---|---|
| stdout/stderr 의미 구분이 중요함 | separate pipes를 유지하되 `source`, `ts`, `seq`를 함께 남긴다 |
| 단일 transcript가 더 중요함 | early merge를 검토하되 buffering 차이는 별도로 의식한다 |
| incident 타임라인 복원이 중요함 | wall-clock + monotonic + sequence id를 함께 남긴다 |
| 병렬 테스트 케이스가 많음 | `test/case id`를 로그 필드에 넣어 섞인 줄을 다시 묶는다 |

## 초보자를 위한 실전 규칙 4개

1. CI 콘솔 순서를 곧바로 프로그램 실제 실행 순서로 읽지 않는다.
2. stdout/stderr를 따로 받는 구조라면 전역 순서는 약하다고 가정한다.
3. 줄마다 `source`와 `timestamp`를 먼저 남기고, 중요도가 높으면 `sequence id`까지 붙인다.
4. 병렬 테스트나 다중 worker라면 `test id`나 `worker id`도 같이 남긴다.

## 여기서 다음으로 이어질 질문

- child 쪽 stdout/stderr 순서가 왜 애초에 흔들리는지는 [stdout/stderr Ordering After Redirect](./stdio-buffering-after-redirect.md)
- separate pipes, merged stream, PTY capture를 언제 고를지는 [TTY-Aware Output Capture Patterns](./tty-aware-output-capture-patterns.md)
- CI에서 출력이 늦는 문제가 merge가 아니라 pipe 정체인지 보려면 [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
- PTY를 붙였더니 progress bar나 색상 때문에 transcript가 더 복잡해지는 이유는 [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)

## 한 줄 정리

CI와 test runner는 stdout/stderr를 separate pipes로 읽은 뒤 나중에 합치는 경우가 많아서, 화면에 보인 줄 순서만으로는 원래 전역 순서를 믿기 어렵다. 그럴수록 `source`, timestamp, sequence id 같은 복원용 metadata가 로그 의미를 지켜 준다.
