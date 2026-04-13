# Anti-Corruption Mapping Drift

> 한 줄 요약: Anti-Corruption Layer의 진짜 위험은 번역이 한 번 틀리는 것이 아니라, 외부 변화와 내부 모델 변화가 쌓이면서 매핑 의미가 서서히 어긋나는 drift다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [BFF Boundaries and Client-Specific Aggregation](./bff-boundaries-client-specific-aggregation.md)

> retrieval-anchor-keywords:
> - anti-corruption layer drift
> - mapping drift
> - semantic drift
> - translation drift
> - external model change
> - contract misalignment
> - field normalization
> - adapter rot

## 핵심 개념

ACL은 외부 모델이 내부 도메인을 오염시키지 않게 막는 번역 계층이다.
그런데 시간이 지나면 번역 규칙 자체가 낡는다.

이때 문제는 외부 API가 바뀌어서만 생기지 않는다.

- 내부 도메인 언어가 바뀐다
- 외부 시스템의 의미가 재정의된다
- 누가 어느 필드를 책임지는지 흐려진다
- 예외/상태 매핑이 임시방편으로 늘어난다

이렇게 누적되는 의미의 어긋남이 mapping drift다.

---

## 깊이 들어가기

### 1. drift는 문법이 아니라 의미에서 시작된다

`status`, `type`, `code` 같은 필드는 겉으로 같아 보여도 의미가 달라질 수 있다.

예:

- 외부 `CANCELLED`가 내부에서는 "환불 예정"으로 해석된다
- 외부 `PENDING`이 내부에서는 "승인 대기"와 "검토 대기"를 구분하지 못한다
- 외부 `amount`가 세금 포함인지 제외인지 바뀐다

문자열 변환은 맞는데 비즈니스 의미가 틀리면, ACL은 이미 drift 상태다.

### 2. drift는 패치가 아니라 재설계의 신호다

매핑 drift가 보이면 보통 다음이 필요하다.

- 필드 의미 재정의
- 내부 도메인 모델 재점검
- 외부 계약 버전 확인
- null/default 규칙 정리
- 실패 케이스 재분류

단순 if-else 추가로 버티면 번역 계층이 점점 규칙 저장소가 된다.

### 3. drift는 테스트로 늦게 발견된다

문제는 대부분 정상 케이스에서는 안 보인다는 점이다.

특히 drift가 잘 숨어드는 영역:

- 부분 취소
- 반품/환불
- 상태 전이 순서
- 외부 시스템의 점진적 롤아웃

그래서 계약 테스트와 샘플 재생이 중요하다.
이 부분은 [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)와 같이 봐야 한다.

### 4. ACL 번역 규칙은 소유권이 있어야 한다

번역 규칙이 여러 서비스에 흩어지면 drift를 추적할 수 없다.

좋은 방식:

- ACL 모듈 소유자 지정
- 외부 시스템별 매핑 표준화
- 예외 코드 사전 관리
- 변경 시 리뷰 체크리스트화

이 소유권이 없으면 drift는 "누가 넣었는지 모르는 임시 보정"으로 남는다.

### 5. drift는 대체 경로보다 재검증 경로가 필요하다

외부 시스템이 바뀌면 ACL도 바뀌어야 한다.
그런데 새 매핑이 옳은지 확인할 수 있어야 한다.

보통 필요한 것:

- before/after diff
- shadow compare
- sample replay
- contract test update
- business review

즉 ACL은 번역기이면서 동시에 **의미 검증 장치**여야 한다.

---

## 실전 시나리오

### 시나리오 1: 배송 상태 매핑이 조금씩 틀어진다

외부 배송사가 `RETURNED_TO_HUB` 같은 새 상태를 추가했다.
내부 ACL이 이를 기존 `IN_TRANSIT`에 그냥 붙이면, 운영과 고객 화면이 모두 잘못 보일 수 있다.

### 시나리오 2: 결제 사유 코드가 비즈니스 의미를 잃는다

처음엔 `DECLINED_CARD`, `DECLINED_LIMIT` 정도였는데 시간이 지나 `DECLINED` 하나로 뭉개진다.
그 순간 ACL은 변환기를 넘어 정보 손실 지점이 된다.

### 시나리오 3: 내부 도메인이 바뀌었는데 ACL은 그대로다

예전에는 `userType`이 중요했지만, 지금은 `tenantRole`이 기준이 되었다.
ACL이 옛 내부 모델에 맞춰져 있으면 drift가 내부 방향에서도 생긴다.

---

## 코드로 보기

```java
public class ShippingAcl {
    public InternalShipmentStatus map(String externalStatus, String reasonCode) {
        return switch (externalStatus) {
            case "IN_TRANSIT" -> InternalShipmentStatus.ON_THE_WAY;
            case "DELIVERED" -> InternalShipmentStatus.DELIVERED;
            case "RETURNED_TO_HUB" -> InternalShipmentStatus.RETURNING;
            default -> InternalShipmentStatus.UNKNOWN;
        };
    }
}
```

이런 매핑은 시작점일 뿐이다.
실무에서는 왜 `UNKNOWN`이 나왔는지, 그 의미를 추적하고 분류하는 메타데이터가 필요하다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 매핑 | 간단하다 | drift가 빨리 퍼진다 | 외부 변화가 거의 없을 때 |
| ACL 분리 | 내부 보호가 된다 | 번역 비용이 든다 | 외부가 불안정할 때 |
| ACL + shadow compare | drift를 조기에 잡는다 | 운영 복잡도가 커진다 | 고위험 연동일 때 |

drift를 늦게 발견할수록 고치는 비용이 커진다.

---

## 꼬리질문

- 현재 매핑은 값 변환인지 의미 변환인지?
- 외부 변경이 들어왔을 때 drift를 누가 확인하는가?
- UNKNOWN/DEFAULT 처리는 무엇을 의미하는가?
- ACL 테스트는 실제 외부 계약 변화까지 반영하는가?

## 한 줄 정리

Anti-Corruption mapping drift는 외부 변화와 내부 변화가 쌓여 번역 의미가 서서히 어긋나는 현상이며, 이를 잡으려면 소유권과 재검증 체계가 필요하다.
