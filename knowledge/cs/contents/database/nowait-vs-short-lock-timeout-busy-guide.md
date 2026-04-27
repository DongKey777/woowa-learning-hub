# `NOWAIT`와 짧은 `lock timeout`은 왜 자동 retry보다 `busy`에 더 가깝게 볼까?

> 한 줄 요약: `NOWAIT`와 짧은 `lock timeout`은 "곧 성공할지 모르는 실패"라기보다 "이 경로는 오래 기다리지 않겠다"는 **짧은 락 예산 선언**에 가깝기 때문에, `insert-if-absent`에서는 기본적으로 자동 retry 큐보다 `busy` 응답으로 닫는 편이 맞다.

**난이도: 🟢 Beginner**

관련 문서:

- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [`busy`는 언제 즉시 실패하고, 언제 한 번만 짧게 재시도할까?](./busy-fail-fast-vs-one-short-retry-card.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [database 첫걸음 브리지](./database-first-step-bridge.md)

retrieval-anchor-keywords: nowait vs short lock timeout busy guide, nowait busy not automatic retry, short lock timeout busy response, insert-if-absent lock budget beginner, fail fast lock budget primer, nowait lock timeout same mental model, busy instead of retry insert-if-absent, short lock budget duplicate path, lock budget busy result, lock timeout budgeted fail fast, nowait short timeout retry policy, insert-if-absent busy result primer, nowait vs retryable difference, 짧은 락 예산 busy 가이드, nowait busy 응답, 짧은 lock timeout 자동 재시도 금지, insert-if-absent 락 예산, lock budget busy primer, beginner nowait timeout guide

## 먼저 멘탈모델

초보자는 `NOWAIT`와 짧은 `lock timeout`을 둘 다 이렇게 읽으면 된다.

- "락을 오래 기다려서 반드시 처리하겠다"가 아니다
- "조금만 보고 막혀 있으면 빨리 돌아서겠다"에 가깝다

즉 이 둘은 **성공 확률을 높이기 위한 retry 신호**라기보다 **대기 예산을 짧게 둔 혼잡 탐침**에 더 가깝다.

그래서 `insert-if-absent` 경로에서는 기본 선택이 이렇다.

- `duplicate key`면 `already exists`
- deadlock / `40001`이면 `retryable`
- `NOWAIT` / 짧은 `lock timeout`이면 우선 `busy`

## 한 장 비교표

| 항목 | `NOWAIT` | 짧은 `lock timeout` | 공통 beginner 해석 |
|---|---|---|---|
| 대기 시간 | 0에 가깝다 | 수 ms~수십 ms 정도만 기다린다 | 오래 줄 서지 않겠다는 정책 |
| 실패가 말하는 것 | "지금 잠겨 있으니 이번 시도는 바로 포기" | "조금 기다렸지만 예산 안에 못 끝남" | winner를 확정한 것이 아니라 혼잡을 본 것 |
| 기본 버킷 | `busy` | `busy` | `already exists`도 `retryable`도 아님 |
| 자동 retry 기본값 | 보통 안 붙임 | 보통 안 붙임 | blind retry가 혼잡을 키우기 쉽다 |
| 예외적 허용 | 1회 짧은 확인성 retry | 1회 짧은 확인성 retry | winner 확정이 거의 끝난 장면일 때만 |

핵심은 이것이다.

> `NOWAIT`와 짧은 `lock timeout`은 "이번 시도가 대기 예산을 다 썼다"는 공통점이 더 크다.

## 왜 자동 retry보다 `busy`가 기본인가

자동 retry는 보통 이런 질문에 "예"일 때 붙인다.

- 실패 원인이 deadlock victim처럼 일시적이고 구조적으로 다시 해볼 만한가?
- 새 트랜잭션으로 다시 시작하면 성공 확률이 눈에 띄게 올라가는가?
- retry가 시스템 혼잡을 크게 키우지 않는가?

그런데 `NOWAIT`와 짧은 `lock timeout`은 반대인 경우가 많다.

1. 이미 "길게 기다리지 않겠다"는 경로 정책이 들어 있다.
2. 바로 다시 시도하면 방금 피하려던 같은 lock queue를 다시 두드릴 수 있다.
3. 요청이 몰린 hot key라면 retry가 backlog를 더 길게 만든다.
4. 결국 성공하더라도 그것은 DB가 좋아서가 아니라 winner가 먼저 끝났기 때문일 수 있다.

그래서 초보자 기본값은:

- 서버 안 automatic retry로 넘기기보다
- `busy`로 분류하고
- 필요하면 클라이언트나 상위 레이어에 "지금은 혼잡하다"는 사실을 보이기

## `insert-if-absent`에서 가장 흔한 장면

쿠폰 발급에서 `(event_id, user_id)` unique key를 만든다고 하자.

1. 요청 A가 같은 key를 만들기 위해 진행 중이다.
2. 요청 B도 같은 key를 만들려 한다.
3. B 경로는 duplicate를 기다리며 오래 매달리지 않으려고 `NOWAIT` 또는 `50ms lock timeout`을 둔다.
4. B는 실패한다.

이때 B 실패를 자동 retry에 바로 넣으면 초보자가 놓치기 쉬운 점이 있다.

- B는 "반드시 다시 하면 된다"가 아니라 "이 경로는 길게 기다리지 않겠다"는 정책을 이미 표현했다.
- retry worker가 즉시 다시 시도하면, 사실상 그 정책을 무효화한다.
- 특히 동일 key 경쟁이 심한 순간이면 요청 수만 늘고 queue만 길어진다.

그래서 먼저 `busy`로 닫는 것이 자연스럽다.

- 의미: "이미 있음이 확정된 것은 아니지만, 이 시점 예산 안에서는 처리하지 않겠다"
- 후속 선택: `503`, per-key 정책이면 `429`, in-progress 표현이면 `202`

## 언제 `busy`로 바로 돌려야 하나

아래 조건이 2개 이상이면 초보자 기본값은 automatic retry가 아니라 `busy`다.

| 체크 질문 | `busy`로 기울어지는 이유 |
|---|---|
| 경로가 애초에 `NOWAIT` 또는 매우 짧은 `lock timeout`을 의도적으로 썼나? | "기다리지 않겠다"는 설계를 retry가 뒤집으면 안 된다 |
| hot key / guard row / slot row 같은 경쟁 지점인가? | 같은 row를 다시 두드리면 혼잡이 커진다 |
| 재시도가 새 DB attempt, 외부 I/O, fan-out을 다시 일으키나? | 확인 비용이 작지 않다 |
| 실패를 `already exists`로 바로 재분류할 fresh evidence가 아직 없나? | 아직 winner를 확인한 것이 아니다 |
| 운영 목적이 tail latency 상한 보호인가? | retry는 p99를 다시 늘릴 수 있다 |

한 줄 기억법:

- 짧은 락 예산은 **성공 보장 장치**가 아니라 **혼잡 상한 장치**

## 그럼 retry는 언제 예외적으로 허용하나

완전히 금지는 아니다. 다만 **자동 retry**와 **짧은 확인성 retry**를 구분해야 한다.

허용 가능한 쪽은 이런 장면이다.

- 같은 멱등 요청의 바로 뒤 요청처럼 보인다
- retry가 transaction 폭증이 아니라 짧은 fresh read 또는 동일 경로 1회 재확인이다
- winner가 이미 commit 직전일 가능성이 높다
- 재시도 횟수를 `1회`로 고정하고 실패 시 즉시 `busy`로 끝낼 수 있다

즉 초보자 규칙은 이렇게 외우면 된다.

- automatic retry loop: 보통 금지
- 확인성 short retry 1회: 제한적으로 가능

## `retryable`과 왜 다르나

| 신호 | 왜 다시 하나 | 다시 하는 단위 |
|---|---|---|
| deadlock / `40P01` / `1213` | 이번 시도가 희생돼서 transaction을 새로 열어야 한다 | whole transaction |
| PostgreSQL `40001` | 이전 snapshot 판단을 버리고 처음부터 다시 판단해야 한다 | whole transaction |
| `NOWAIT` / 짧은 `lock timeout` | 기다림 예산 안에 lock을 못 얻었다 | 기본은 retry 안 함, 필요 시 확인성 1회 |

`retryable`은 "새 시도가 의미 있게 달라질 수 있다"는 쪽이고,
짧은 락 예산 실패는 "애초에 기다리지 않겠다고 정한 정책이 발동했다"는 쪽이다.

## 흔한 오해

- "`NOWAIT` 실패면 잠깐 뒤 재시도하면 되니까 retryable이다"
  - 아니다. 먼저 읽어야 할 메시지는 "이 경로는 대기하지 않는다"다.
- "짧은 `lock timeout`은 결국 timeout이니까 내부 retry를 여러 번 붙여도 된다"
  - 아니다. 그러면 짧은 예산 설정 의미가 흐려진다.
- "실패했지만 같은 key 경쟁이니 결국 `already exists`로 봐도 된다"
  - 아니다. duplicate를 직접 본 것이 아니라 lock 획득을 포기한 것이다.
- "`busy`로 돌리면 너무 차갑고 retry가 더 친절하다"
  - 혼잡 구간에서는 blind retry가 더 비싸고, 전체 성공률보다 tail latency를 악화시킬 수 있다.

## 초보자용 결론

1. `NOWAIT`와 짧은 `lock timeout`은 둘 다 **짧은 락 예산**으로 먼저 묶는다.
2. 짧은 락 예산 실패는 기본적으로 `busy`다.
3. automatic retry는 정책을 무효화하고 혼잡을 키우기 쉬우므로 기본값이 아니다.
4. 예외적으로 winner 확정이 거의 끝난 장면에서만 **1회 짧은 확인성 retry**를 붙인다.

## 다음에 이어서 볼 문서

- `busy` 자체의 fail-fast 기준을 더 짧게 보면 [`busy`는 언제 즉시 실패하고, 언제 한 번만 짧게 재시도할까?](./busy-fail-fast-vs-one-short-retry-card.md)
- `insert-if-absent` 전체 3버킷 표로 돌아가려면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- Spring 예외 표면에서 `55P03` / `1205` / `40P01` / `40001`을 다시 나누려면 [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
