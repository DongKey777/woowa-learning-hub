# Circuit Breaker 기초 (Circuit Breaker Basics)

> 한 줄 요약: Circuit Breaker는 외부 서비스 장애가 연쇄적으로 전파되는 것을 막기 위해 요청을 빠르게 차단하고 복구를 기다리는 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: circuit breaker basics, 서킷 브레이커 입문, circuit breaker 뭐예요, open half-open closed 상태, 연쇄 장애 방지, cascading failure 기초, 장애 격리 패턴, fallback 기초, 외부 서비스 장애 처리, beginner circuit breaker, resilience4j 기초, fail fast pattern, 복구 대기 패턴

---

## 핵심 개념

Circuit Breaker는 전기 회로의 차단기에서 이름을 가져왔다. 전기가 과하게 흐르면 차단기가 열려서 더 큰 피해를 막는 것처럼, 소프트웨어에서도 외부 서비스가 계속 실패할 때 추가 호출을 차단해 시스템 전체가 다운되는 것을 막는다.

입문자가 자주 헷갈리는 지점은 **왜 실패할 때 재시도하지 않고 차단하는가**이다.

외부 서비스가 장애 상태일 때 계속 재시도하면:

- 모든 요청 스레드가 타임아웃을 기다리며 묶인다.
- 장애 서비스에 더 많은 요청이 쌓여 복구가 더 느려진다.
- 결국 내 서비스도 응답 불능이 된다.

Circuit Breaker는 이런 **연쇄 장애(cascading failure)**를 막는다.

---

## 한눈에 보기

Circuit Breaker의 세 가지 상태:

| 상태 | 의미 | 동작 |
|---|---|---|
| Closed | 정상 | 요청을 그대로 통과시킨다 |
| Open | 차단 | 요청을 즉시 실패 처리한다 (외부 호출 없음) |
| Half-Open | 탐색 | 소수 요청을 통과시켜 복구 여부를 확인한다 |

```text
Closed
  [실패율 임계치 초과]
    -> Open (차단 시작)
        [대기 시간 경과]
          -> Half-Open (일부 요청 허용)
              [성공]  -> Closed (정상 복귀)
              [실패]  -> Open  (다시 차단)
```

---

## 상세 분해

### Closed 상태 (정상)

요청을 외부 서비스로 그대로 전달한다. 실패 횟수를 카운트하고, 임계치(예: 10초 안에 50% 실패)를 넘으면 Open으로 전환한다.

### Open 상태 (차단)

외부 서비스로 요청을 보내지 않는다. 즉시 에러를 반환하거나 미리 정의한 fallback 응답을 반환한다.

- fallback 예시: 캐시된 이전 값 반환, 기본값 반환, 서비스 불가 메시지 반환

일정 시간(예: 30초)이 지나면 Half-Open으로 전환한다.

### Half-Open 상태 (탐색)

소수의 요청만 실제로 통과시켜 외부 서비스가 복구됐는지 확인한다.

- 통과한 요청이 성공하면 → Closed로 복귀
- 실패하면 → 다시 Open으로 전환

---

## 흔한 오해와 함정

- **"Circuit Breaker가 있으면 타임아웃이 필요 없다"**: 둘은 함께 써야 한다. 타임아웃 없이 Circuit Breaker만 쓰면 Open 전환 전까지 스레드가 계속 묶인다.
- **"모든 서비스 호출에 Circuit Breaker를 넣어야 한다"**: 오히려 불필요하게 넣으면 정상 상황에서도 Open이 되어 가용성이 낮아진다. 외부 의존성이 크거나 장애 전파가 우려되는 경로에만 적용하는 편이 실용적이다.
- **"Circuit Breaker가 열리면 요청이 버려진다"**: fallback 로직을 잘 설계하면 캐시된 값이나 기본값을 돌려줘서 완전 실패가 아닌 부분 서비스를 유지할 수 있다.

---

## 실무에서 쓰는 모습

가장 흔한 시나리오는 외부 결제 API나 알림 서비스 호출 앞에 Circuit Breaker를 두는 것이다.

1. 결제 서비스가 5초 연속으로 타임아웃이 발생한다.
2. Circuit Breaker가 Open 상태로 전환한다.
3. 이후 결제 요청은 즉시 "결제 서비스 일시 점검 중" 응답을 반환한다.
4. 30초 후 Half-Open으로 전환, 한 건의 요청을 실제로 보낸다.
5. 성공하면 Closed로 복귀하고 정상 처리를 재개한다.

Java 생태계에서는 Resilience4j 라이브러리가 Circuit Breaker 구현체로 자주 쓰인다.

---

## 더 깊이 가려면

- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md) — Circuit Breaker와 연결 관리, 로드밸런싱의 관계
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md) — Circuit Breaker와 함께 쓰는 타임아웃·재시도 전략

---

## 면접/시니어 질문 미리보기

> Q: Circuit Breaker의 세 가지 상태를 설명해 주세요.
> 의도: 기본 동작 원리를 구두로 설명할 수 있는지 확인
> 핵심: Closed(정상 통과), Open(즉시 차단), Half-Open(탐색 중)이며, 실패율이 임계치를 넘으면 Open, 복구 확인 후 Closed로 돌아온다.

> Q: Circuit Breaker가 없으면 외부 서비스 장애가 어떻게 내 서비스로 전파되나요?
> 의도: 연쇄 장애 메커니즘 이해 확인
> 핵심: 타임아웃을 기다리는 스레드가 쌓여 스레드 풀이 고갈되고, 결국 내 서비스도 응답을 못 하게 된다.

> Q: Open 상태에서 fallback은 왜 중요한가요?
> 의도: 단순 에러 반환과 graceful degradation의 차이 이해 확인
> 핵심: 차단만 하고 fallback이 없으면 사용자에게 에러만 보인다. fallback으로 캐시값이나 기본값을 돌려주면 서비스가 부분적으로 살아있을 수 있다.

---

## 한 줄 정리

Circuit Breaker는 외부 서비스 장애 시 Open으로 전환해 연쇄 실패를 빠르게 차단하고, Half-Open으로 복구를 탐색한 뒤 Closed로 복귀하는 세 상태 전환 패턴이다.
