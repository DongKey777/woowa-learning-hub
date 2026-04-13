# Strangler Verification, Shadow Traffic Metrics

> 한 줄 요약: Strangler 전환은 트래픽을 옮기는 순간보다, 새 경로가 레거시와 충분히 같은 의미를 내는지 계측으로 증명하는 과정이 더 중요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)

> retrieval-anchor-keywords:
> - strangler verification
> - shadow traffic
> - traffic mirroring
> - response diff
> - cutover metrics
> - semantic equivalence
> - replay safety
> - migration confidence

## 핵심 개념

Strangler Fig 전환은 새 시스템이 트래픽을 받는다고 끝나지 않는다.
실제로는 "새 시스템이 레거시와 충분히 같은 결과를 낸다는 믿음"을 만들어야 한다.

그 믿음은 감이 아니라 다음으로 쌓는다.

- shadow traffic
- response diff
- side effect 차단
- 지표 기반 판정
- 재처리와 롤백 계획

즉 이 문서의 주제는 migration 자체보다 **검증 가능한 전환**이다.

---

## 깊이 들어가기

### 1. shadow traffic은 복제지만, 복제가 목적은 아니다

shadow traffic은 실제 요청을 새 경로에도 보내되 사용자 응답에는 반영하지 않는 방식이다.

목적은 세 가지다.

- 실트래픽 패턴을 본다
- 새 경로의 오류를 미리 찾는다
- 레거시와 의미 차이를 계량화한다

단순히 "요청이 잘 들어갔다"가 아니라 **같은 입력에 대해 얼마나 같은 의미를 돌려주는가**가 핵심이다.

### 2. 무엇을 비교할지 먼저 정해야 한다

모든 응답을 byte-by-byte로 비교하면 실무에서 바로 깨진다.

비교 단위는 보통 다음처럼 나눈다.

- 필수 필드 존재 여부
- 값의 동등성
- 정렬 순서
- null/empty 차이
- 부동소수점 허용 오차
- 에러 코드 의미

여기서 중요한 건 "완전히 같은가"보다 **업무적으로 같은가**를 기준으로 삼는 것이다.

### 3. shadow traffic은 side effect를 절대 그대로 흘리면 안 된다

조회는 shadow로 보내기 쉽지만, 쓰기는 훨씬 조심해야 한다.

예:

- 결제 승인
- 메일 발송
- 포인트 적립
- 외부 API 호출

이런 요청을 그대로 복제하면 새 시스템이 실수로 실제 부작용을 낼 수 있다.
그래서 shadow 대상은 보통 다음 중 하나다.

- read-only endpoint
- dry-run mode
- side effect disabled mode
- sandbox sink

### 4. cutover confidence는 단일 지표가 아니다

전환 가능 여부는 하나의 숫자로 정하기 어렵다.

보통 다음 조합을 본다.

- response diff rate
- critical field mismatch rate
- 5xx rate
- p95/p99 latency
- timeout rate
- replay lag
- fallback rate

이 중 하나만 좋아도 안 된다.
예를 들어 latency는 좋지만 의미 차이가 있으면 아직 전환하면 안 된다.

### 5. shadow traffic은 "버그 찾기"보다 "판정 가능성 확보"가 더 중요하다

실전에서는 버그가 조금 남아도 괜찮을 수 있다.
문제는 그 버그가 **얼마나 자주, 어떤 조건에서, 어떤 영향으로** 나타나는지 모르는 상태다.

shadow traffic은 그 불확실성을 줄여 준다.

- 언제 깨지는지
- 어떤 요청에서 깨지는지
- 어떤 필드가 반복적으로 어긋나는지

이 정보가 있어야 cutover 기준을 세울 수 있다.

---

## 실전 시나리오

### 시나리오 1: 주문 조회 경로를 새 서비스로 옮긴다

1. 프로덕션 읽기 요청을 shadow로 새 서비스에 복제한다
2. 응답을 레거시와 비교한다
3. mismatch 유형을 분류한다
4. 필수 필드와 edge case를 보강한다
5. 일정 기간 동안 diff가 안정적이면 live routing을 늘린다

### 시나리오 2: 가격 계산 API는 숫자보다 의미가 중요하다

가격 계산은 부동소수점, 반올림, 할인 정책 때문에 단순 diff가 어렵다.

비교 기준 예:

- 총액 오차 허용 범위
- 할인 항목 순서 무관 여부
- 쿠폰 만료 처리 방식
- 재시도 시 동일 결과 보장 여부

### 시나리오 3: 레거시와 새 서비스의 에러 표현이 다르다

레거시는 `404`를 주고, 새 서비스는 `200 + empty body`를 준다면 의미 차이가 있다.

이 경우 shadow diff에서 "응답 코드"만이 아니라 **consumer가 보는 실패 의미**를 비교해야 한다.

---

## 코드로 보기

```java
public class ShadowComparator {
    public DiffResult compare(LegacyResponse legacy, NewResponse modern) {
        DiffResult diff = new DiffResult();

        if (!legacy.orderId().equals(modern.orderId())) {
            diff.add("orderId");
        }
        if (!Objects.equals(legacy.status(), modern.status())) {
            diff.add("status");
        }
        if (Math.abs(legacy.totalAmount().subtract(modern.totalAmount()).intValue()) > 10) {
            diff.add("totalAmount");
        }

        return diff;
    }
}
```

실무에서는 이런 비교를 더 정교하게 만든다.

- ignore list
- tolerance rules
- field mapping
- semantic rule set

중요한 건 diff가 "실패/성공"만 말하지 않고, **어떤 의미 차이인지 설명**해야 한다는 점이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 바로 cutover | 빠르다 | 의미 차이를 놓치기 쉽다 | 변경이 작고 되돌리기 쉬울 때 |
| shadow traffic | 실제 입력으로 검증 가능 | 비교/마스킹/관측 비용이 든다 | 큰 경로를 옮길 때 |
| contract test + shadow | 형식과 의미를 같이 본다 | 관리 포인트가 늘어난다 | 전환 리스크가 높을 때 |

shadow traffic은 느리지만, 전환 실패 비용이 큰 시스템에서는 가장 값싸게 불확실성을 줄이는 방법이다.

---

## 꼬리질문

- 어떤 diff는 무시하고 어떤 diff는 막아야 하는가?
- replay가 side effect를 만들지 않도록 어떻게 격리할 것인가?
- shadow traffic의 데이터 마스킹 정책은 누가 소유해야 하는가?
- diff가 0이 아니어도 전환 가능한 기준은 무엇인가?

## 한 줄 정리

Strangler 전환은 라우팅이 아니라 검증의 문제이고, shadow traffic과 diff metric이 그 전환을 안전한 의사결정으로 바꾼다.
