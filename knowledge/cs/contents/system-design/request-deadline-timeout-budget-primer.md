# Request Deadline and Timeout Budget Primer

> 한 줄 요약: timeout budget은 "각 레이어가 얼마나 오래 기다릴지"를 따로 늘리는 일이 아니라, 한 요청의 남은 시간을 위에서 아래로 나눠 쓰는 약속이다.

retrieval-anchor-keywords: request deadline primer, timeout budget primer, end-to-end deadline, client timeout budget, app timeout budget, cache timeout basics, db timeout basics, remaining budget, fail-fast ladder, 처음 timeout budget 뭐예요, 왜 timeout을 계단처럼, timeout budget basics, deadline propagation basics, request timeout beginner

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)

---

## 핵심 개념

처음에는 timeout을 "각자 적당히 긴 값"으로 잡기 쉽다. 하지만 초급자가 먼저 잡아야 할 그림은 더 단순하다. 요청 하나에는 전체 마감 시각이 하나 있고, app은 그 남은 시간을 cache와 DB에 더 짧게 나눠 준다. 그래서 timeout budget은 "오래 기다릴지"보다 "남은 시간 안에서 어디까지 시도할지"를 정하는 약속이다.

가장 단순한 모양은 아래다.

```text
Client deadline 1500ms
  -> App budget 1200ms
      -> Cache timeout 50ms
      -> DB timeout 200ms
```

핵심은 아래 네 줄이면 충분하다.

- client는 전체 요청의 끝 시간을 정한다
- app은 남은 시간을 보고 하위 호출 시간을 나눈다
- cache는 우회로라서 짧게 끊는다
- DB는 app보다 더 짧게 끝나야 다음 요청과 덜 겹친다

## 한눈에 보는 계단

| 레이어 | 초급자용 역할 | 너무 길면 생기는 일 | 먼저 기억할 말 |
|---|---|---|---|
| client deadline | 사용자 요청의 전체 마감 | 사용자는 포기했는데 서버 일은 계속 남음 | "이 요청은 언제까지 유효한가?" |
| app budget | 남은 시간을 나눠 주는 조정자 | cache와 DB가 합쳐져 전체 시간을 넘김 | "새 호출을 시작해도 되나?" |
| cache timeout | 빠른 길인지 빨리 판단 | cache 기다리다 본 작업까지 늦어짐 | "느리면 빨리 포기" |
| DB timeout | 마지막 핵심 작업의 상한 | 오래된 작업이 뒤에 남음 | "아래로 갈수록 더 짧게" |

처음이고 "`왜 timeout을 계단처럼 두죠?`", "`뭐예요, 다 1초로 맞추면 안 되나요?`"가 헷갈리면 "위는 전체 마감, 아래는 더 짧은 하위 제한"만 먼저 기억하면 된다.

## 간단 예시

상품 목록을 읽는 요청이 있다고 하자.

1. client는 1500ms 안에 끝나길 원한다.
2. app은 응답 마무리 시간을 빼고 1200ms만 실제 작업에 쓴다.
3. cache는 50ms 안에 안 오면 바로 포기한다.
4. DB는 200ms까지만 기다린다.

이 설계의 목적은 고급 장애 분석이 아니다. "cache가 조금 느릴 때 cache도 오래 기다리고, DB도 오래 기다리고, 사용자는 다시 눌러서 요청이 겹치는 상황"을 먼저 막는 데 있다.

짧은 의사코드로 보면 이 정도다.

```text
remaining = client_deadline - now

if remaining <= 100ms:
  fail_fast

cache_timeout = 50ms
db_timeout = min(200ms, remaining - 100ms)
```

## 흔한 헷갈림

- timeout budget과 retry는 같은 말이 아니다. timeout budget은 한 번의 수명, retry는 다시 시도할 횟수다.
- cache timeout이 짧다고 cache가 중요하지 않은 것은 아니다. "빠른 길인지 빨리 판단"하려는 뜻이다.
- app timeout을 client와 똑같이 두면 단순해 보여도, 실제로는 응답 정리 시간 없이 하위 호출이 이어질 수 있다.
- 이 문서 단계에서는 `lock wait`, `pool acquire`, `retry storm` 세부 운영값까지 외우지 않아도 된다. 그런 분기는 관련 문서로 넘기는 편이 안전하다.

## 여기서 멈추고 다음으로 갈 것

이 문서의 목표는 timeout budget의 첫 그림을 잡는 것까지다. 아래 질문이 생기면 그때 다음 문서로 이동하면 된다.

| 지금 질문 | 다음 문서 | 이유 |
|---|---|---|
| "`왜 느린 요청이 여러 시도로 불어나죠?`" | [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md) | retry와 overload를 별도 축으로 설명한다 |
| "`프록시, 게이트웨이, 서비스 hop마다 deadline은 어떻게 전달하죠?`" | [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) | 네트워크 hop 전파 규칙은 이 문서 범위를 넘는다 |
| "`DB timeout은 statement, lock, pool 중 뭘 먼저 보죠?`" | [Database Scaling Primer](./database-scaling-primer.md) | DB 운영 파라미터는 초급 입문 다음 단계다 |

처음이면 "`언제 deeper 문서로 가야 해요?`"의 기준도 단순하다. app, cache, DB가 왜 같은 timeout을 쓰면 안 되는지만 설명할 수 있으면 이 문서는 충분히 끝낸 것이다.

## 한 줄 정리

timeout budget은 client의 전체 마감을 app이 하위 호출에 더 짧게 나눠 주는 규칙이며, Beginner 단계에서는 "위는 길고 아래는 짧다"는 계단 그림을 먼저 잡으면 된다.
