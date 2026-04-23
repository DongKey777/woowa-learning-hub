# Replay Store Outage / Degradation Recovery

> 한 줄 요약: nonce, `jti`, event id, replay cache 같은 저장소가 죽으면 재전송 방어가 사라지므로, replay defense 시스템도 risk-tiered fail policy, bounded fallback, recovery drill을 따로 가져야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md)
> - [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
> - [Webhook Signature Verification / Replay Defense](./webhook-signature-verification-replay-defense.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Database: 멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [System Design: Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
> - [System Design: Replay / Repair Orchestration Control Plane](../system-design/replay-repair-orchestration-control-plane-design.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)

retrieval-anchor-keywords: replay store outage, nonce store outage, jti replay cache outage, replay defense degradation, dedup store outage, nonce validation outage, replay recovery drill, fail-open fail-closed replay, bounded fallback

---

## 핵심 개념

많은 시스템에서 replay defense는 "서명 검증 뒤에 한 번 더 보는 저장소 조회"처럼 취급된다.  
하지만 그 저장소가 죽는 순간, 보안 의미는 크게 달라진다.

예:

- HMAC nonce store 장애
- DPoP `jti` replay cache 장애
- webhook event id dedup store 장애
- client assertion `jti` store 장애

즉 replay defense도 별도 dependency이며, outage 시 어떤 요청은 막고 어떤 요청은 제한적으로 계속 받을지 미리 정해야 한다.

---

## 깊이 들어가기

### 1. replay store는 종류가 달라도 실패 모드가 비슷하다

보통 저장되는 것은 다르다.

- nonce
- `jti`
- event id
- request fingerprint

하지만 운영 문제는 비슷하다.

- 저장소 timeout
- 부분 region 장애
- write 성공/조회 실패 비대칭
- TTL cleanup 밀림
- split brain 또는 eviction 폭주

즉 구현체가 Redis든 DB든, outage semantics를 따로 다뤄야 한다.

### 2. replay defense는 risk tier마다 fail policy가 달라야 한다

같은 fallback을 모든 요청에 적용하면 안 된다.

예:

- 결제/권한 변경/고액 이체: fail-closed
- 읽기 webhook ack, 저위험 callback: 제한적 degraded mode 가능
- internal idempotent event processing: bounded fallback 가능

핵심은 replay check가 없는 상태에서 재전송이 어떤 피해를 내는지 보는 것이다.

### 3. timestamp window는 store outage 대체재가 아니다

자주 나오는 오해:

- "nonce store가 죽었으니 timestamp 30초만 보면 된다"

문제:

- 그 30초 안에서는 같은 요청을 얼마든지 재전송할 수 있다
- load balancer retry와 공격 replay가 구분되지 않는다
- clock skew가 있으면 윈도우를 더 넓혀야 하고 더 위험해진다

timestamp는 replay 면적을 줄일 뿐, dedup 자체를 대체하지 못한다.

### 4. bounded fallback은 작고 명시적이어야 한다

그나마 가능한 fallback:

- single node in-memory short cache
- route-scoped temporary deny or quota tightening
- one-shot operation에 대한 idempotency key 재사용
- provider-supplied event id와 local processing state 결합

중요한 것은 fallback의 한계가 명확해야 한다는 점이다.

- 어떤 route에만 허용하는가
- 몇 분 동안만 쓰는가
- false negative risk가 어느 정도인가

### 5. read/write 비대칭 장애는 특히 위험하다

예를 들어:

- write는 됐는데 read가 실패한다
- read는 되는데 write가 유실된다

이 경우 단순 "cache down"보다 더 위험하다.

- 중복 요청을 이미 저장했는데 못 읽어 다시 허용할 수 있다
- 이미 허용한 nonce를 기록 못 해 뒤이어 온 replay를 또 허용할 수 있다

따라서 replay store health는 availability만이 아니라 consistency semantics까지 봐야 한다.

### 6. dedup과 idempotency는 비슷하지만 같은 것은 아니다

많이 섞이는 개념:

- replay defense: 같은 signed request가 다시 오는 것을 막음
- idempotency: 같은 business request가 여러 번 와도 결과를 한 번으로 맞춤

idempotency가 있더라도:

- 인증된 요청 재전송 자체를 허용하게 될 수 있고
- side-channel, rate limit, audit 의미는 달라질 수 있다

따라서 "idempotent하니 replay store 없어도 된다"는 결론은 위험하다.

### 7. observability 없이 replay degradation은 조용히 열린다

필요한 지표:

- replay check bypass count
- replay store timeout rate
- degraded route count
- in-memory fallback hit ratio
- duplicate accept suspicion count

이 정보가 없으면 운영자는 "지금 replay protection이 약해진 상태"를 모른 채 지나간다.

### 8. recovery drill은 security dependency로서 테스트해야 한다

drill 시나리오 예:

- replay store full outage
- one region only timeout
- write path partial failure
- TTL sweep lag causing false replay
- cache flush causing duplicate acceptance spike

목표:

- 위험 route가 실제로 fail-closed 되는가
- degraded mode가 시간 제한과 범위 제한을 지키는가
- observability가 bypass 상태를 보여 주는가

---

## 실전 시나리오

### 시나리오 1: HMAC nonce store가 죽었는데 결제 API는 계속 열려 있다

문제:

- 서명은 검증되지만 replay 차단이 사라졌다

대응:

- 결제/권한 변경 route는 fail-closed 한다
- degraded mode는 저위험 route로만 제한한다
- bypass count와 route class를 즉시 alert한다

### 시나리오 2: webhook dedup store가 일시 장애라 중복 처리 위험이 커진다

문제:

- provider retry와 공격 replay를 구분하기 어렵다

대응:

- event id + business idempotency를 함께 본다
- side effect route는 queue 격리 후 지연 처리한다
- store 복구 뒤 backfill/reconcile을 돌린다

### 시나리오 3: DPoP `jti` store write만 실패해서 재전송이 조용히 통과한다

문제:

- availability 지표는 정상처럼 보일 수 있다

대응:

- write acknowledgment failure를 separate metric으로 본다
- high-risk audience는 fail-closed 한다
- duplicate proof suspicion 이벤트를 남긴다

---

## 코드로 보기

### 1. risk-tiered replay fallback 개념

```java
public void verifyReplay(RouteClass routeClass, String key, Instant timestamp) {
    ReplayCheckResult result = replayStore.checkAndRecord(key, timestamp);

    if (result.allowed()) {
        return;
    }

    if (result.storeUnavailable() && routeClass == RouteClass.LOW_RISK) {
        boundedFallbackCache.record(key, Duration.ofSeconds(30));
        return;
    }

    throw new ReplayProtectionUnavailableException();
}
```

### 2. 운영 체크리스트

```text
1. replay store 장애 시 route class별 fail policy가 정의돼 있는가
2. timestamp window를 replay store의 대체재로 오해하지 않는가
3. read/write partial failure를 separate health signal로 보는가
4. degraded mode가 time-boxed, route-scoped로 제한되는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 전면 fail-closed | replay 방어가 강하다 | dependency outage 시 가용성이 급락한다 | 결제, 권한 변경, 고위험 API |
| 제한적 degraded fallback | 일부 가용성을 지킨다 | replay 면적이 열릴 수 있다 | 저위험 route, internal ack path |
| timestamp-only fallback | 구현이 쉽다 | 진짜 dedup이 안 된다 | 가능하면 피한다 |
| in-memory short fallback | 좁은 창을 메울 수 있다 | multi-node 일관성이 약하다 | 짧은 emergency window |

판단 기준은 이렇다.

- replay 허용 시 business side effect가 큰가
- route가 이미 idempotent하고 추가 guardrail이 있는가
- store outage를 observability로 바로 볼 수 있는가
- degraded mode를 짧게 제한할 수 있는가

---

## 꼬리질문

> Q: replay store가 죽었을 때 timestamp 검증만 남겨도 충분한가요?
> 의도: freshness와 dedup을 구분하는지 확인
> 핵심: 아니다. timestamp는 재전송 창을 줄일 뿐, 같은 요청의 재사용 자체를 막지는 못한다.

> Q: 왜 replay store outage도 별도 incident로 봐야 하나요?
> 의도: 보안 dependency의 중요성을 이해하는지 확인
> 핵심: replay defense가 꺼진 상태는 인증은 살아 보여도 재전송 방어가 약해진 별도 보안 장애이기 때문이다.

> Q: idempotency가 있으면 replay 방어는 필요 없나요?
> 의도: business dedup과 security replay를 구분하는지 확인
> 핵심: 아니다. 결과 중복만 줄여 줄 뿐, 인증된 요청 재사용의 보안 의미까지 없애지 못한다.

> Q: degraded mode는 어떻게 제한해야 하나요?
> 의도: fallback 범위 제어를 이해하는지 확인
> 핵심: low-risk route에만, 짧은 시간 동안, 명시적 observability와 함께 열어야 한다.

## 한 줄 정리

Replay defense를 운영 가능하게 만드는 핵심은 nonce/jti store를 평범한 캐시가 아니라 보안 dependency로 보고, outage 시 route별 fail policy와 bounded fallback을 미리 정해 두는 것이다.
