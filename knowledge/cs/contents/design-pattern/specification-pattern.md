# Specification Pattern: 조건식을 조합 가능한 도메인 규칙으로 만들기

> 한 줄 요약: Specification 패턴은 복잡한 조건문을 재사용 가능한 명세 객체로 분리해, 검색·검증·정책 판단을 조합 가능하게 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [전략 패턴](./strategy-pattern.md)
> - [Policy Object Pattern](./policy-object-pattern.md)
> - [Specification vs Query Service Boundary](./specification-vs-query-service-boundary.md)
> - [Query Object and Search Criteria Pattern](./query-object-search-criteria-pattern.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Specification 패턴은 **"이 조건을 만족하는가?"를 객체로 표현**하는 패턴이다.  
단순한 boolean 함수처럼 보이지만, 진짜 가치는 **조합 가능성**에 있다.

backend에서는 다음 상황에서 특히 유용하다.

- 주문 검색 조건이 계속 늘어날 때
- 쿠폰/회원/권한 조건을 조합할 때
- 승인 가능 여부를 계산할 때
- 정책이 `AND`, `OR`, `NOT`으로 합성될 때

### Retrieval Anchors

- `specification pattern`
- `predicate composition`
- `order search filter`
- `eligibility rule`
- `JPA Specification`
- `specification vs query service`
- `specification vs policy object`
- `boolean specification`
- `rich decision result`
- `eligibility specification`

---

## 깊이 들어가기

### 1. 전략과 명세는 방향이 다르다

전략 패턴은 "어떤 방식으로 할까"를 담는다.  
Specification은 "조건을 만족하는가"를 담는다.

| 구분 | 전략 패턴 | Specification |
|---|---|---|
| 반환 | 행동 결과 | 참/거짓 |
| 목적 | 알고리즘 교체 | 조건 조합 |
| 대표 예 | 결제 방식, 정렬 방식 | 검색 필터, 승인 조건 |

둘은 비슷해 보이지만 질문이 다르다.

### 2. 명세가 많아지면 분기문보다 조합이 낫다

예를 들어 다음 조건을 생각해보자.

- 활성 사용자
- 최근 30일 내 로그인
- 특정 등급 이상
- 미사용 쿠폰 보유

이걸 `if` 문으로 계속 늘리면 읽기 어려워진다.  
명세로 쪼개면 재사용과 테스트가 쉬워진다.

### 3. DB 조건과 메모리 조건을 함께 생각해야 한다

Specification은 단순히 코드 구조만이 아니다.

- DB 쿼리로 내려갈 수 있는가
- 메모리에서 추가 필터링이 필요한가
- 성능상 어디까지 푸시다운할 것인가

특히 JPA에서는 `Specification<T>`와 자연스럽게 연결된다.

### 4. Specification은 rich decision을 대신하지 않는다

명세가 규칙 평가 객체라는 이유로, 여기에 이유 코드나 수수료 계산까지 얹기 시작하면 패턴의 성격이 바뀐다.

| 구분 | Specification | Policy Object |
|---|---|---|
| 반환 | `boolean` | decision/result object |
| 잘하는 일 | 자격/필터/guard 조합 | 결정 설명, fee/reason/action 반환 |
| 대표 소비자 | 검색, precondition, eligibility check | 서비스 흐름, 승인/환불 orchestration |
| 흔한 오해 | `why`와 `how much`까지 넣으려 한다 | boolean 조합을 전부 혼자 품으려 한다 |

Specification은 "통과했는가"를 고정하는 데 강하고,  
Policy Object는 "그래서 무엇을 해야 하는가"를 정리하는 데 강하다.

---

## 실전 시나리오

### 시나리오 1: 주문 검색 API

운영자가 주문을 조회할 때 다음 조합이 생긴다.

- 결제 완료 주문
- 취소 제외
- 특정 기간
- 특정 배송 상태

조건 객체를 분리하면 검색 API가 길어질수록 더 안정적이다.

### 시나리오 2: 쿠폰 대상자 선정

쿠폰 발급 대상은 보통 여러 규칙을 묶는다.

### 시나리오 3: 결제/승인 전 검증

금액, 등급, 계정 상태, 제한 횟수를 독립 명세로 나누면 규칙 변경이 국소화된다.

---

## 코드로 보기

### 간단한 명세 인터페이스

```java
public interface Specification<T> {
    boolean isSatisfiedBy(T candidate);

    default Specification<T> and(Specification<T> other) {
        return candidate -> this.isSatisfiedBy(candidate) && other.isSatisfiedBy(candidate);
    }

    default Specification<T> or(Specification<T> other) {
        return candidate -> this.isSatisfiedBy(candidate) || other.isSatisfiedBy(candidate);
    }

    default Specification<T> not() {
        return candidate -> !this.isSatisfiedBy(candidate);
    }
}
```

### 도메인 명세

```java
public class ActiveMemberSpecification implements Specification<Member> {
    @Override
    public boolean isSatisfiedBy(Member member) {
        return member.isActive();
    }
}

public class VipMemberSpecification implements Specification<Member> {
    @Override
    public boolean isSatisfiedBy(Member member) {
        return member.getGrade() == MemberGrade.VIP;
    }
}
```

### 조합

```java
Specification<Member> target =
    new ActiveMemberSpecification()
        .and(new VipMemberSpecification())
        .and(member -> member.getLastLoginDays() <= 30);
```

### Spring Data JPA 스타일

```java
public class OrderSpecifications {
    public static Specification<OrderEntity> paidOnly() {
        return (root, query, cb) -> cb.equal(root.get("status"), OrderStatus.PAID);
    }

    public static Specification<OrderEntity> placedAfter(LocalDateTime from) {
        return (root, query, cb) -> cb.greaterThanOrEqualTo(root.get("createdAt"), from);
    }
}
```

이 방식은 검색 조건이 늘어날수록 특히 강하다.

### Policy Object로 넘기는 경계

```java
public class RefundEligibilitySpecification implements Specification<Order> {
    @Override
    public boolean isSatisfiedBy(Order order) {
        return !order.isShipped() && order.daysSincePurchase() <= 7;
    }
}

public record RefundDecision(boolean allowed, int fee, String reason) {}

public class StandardRefundPolicy {
    private final Specification<Order> eligibility = new RefundEligibilitySpecification();

    public RefundDecision evaluate(Order order) {
        if (!eligibility.isSatisfiedBy(order)) {
            return new RefundDecision(false, 0, "NOT_ELIGIBLE");
        }
        return new RefundDecision(true, 1000, "STANDARD_FEE");
    }
}
```

여기서 boolean 조합은 Specification이 맡고,  
이유/금액/후속 액션 같은 rich decision은 Policy Object가 맡는다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `if` 문 | 가장 직관적이다 | 조건이 커지면 읽기 어렵다 | 규칙이 거의 없을 때 |
| Specification | 조건을 조합할 수 있다 | 과하면 추상화가 무거워진다 | 필터 조합이 자주 바뀔 때 |
| Policy Object | 판단 결과를 설명 가능한 형태로 돌려준다 | 단순 boolean 규칙에는 무겁다 | 이유/금액/다음 조치가 필요할 때 |
| 전용 쿼리 객체 | DB 친화적이다 | 메모리 검증과 분리된다 | 검색이 핵심일 때 |

판단 기준은 명확하다.

- "행동"을 바꾸면 전략
- "참/거짓 조건"을 조합하면 Specification
- 이유/금액/후속 액션까지 돌려줘야 하면 Policy Object
- DB 성능이 최우선이면 쿼리 설계를 먼저 본다

---

## 꼬리질문

> Q: Specification과 전략 패턴을 어떻게 구분하나요?
> 의도: 반환값과 목적의 차이를 아는지 확인한다.
> 핵심: 전략은 행동을 수행하고, Specification은 조건 만족 여부를 판단한다.

> Q: Specification을 과하게 쓰면 왜 복잡해지나요?
> 의도: 추상화를 늘리는 것이 항상 이득이 아니라는 점을 보는지 확인한다.
> 핵심: 아주 단순한 필터까지 객체로 쪼개면 오히려 읽기 어려워진다.

> Q: JPA Specification을 쓰면 쿼리 성능이 자동으로 좋아지나요?
> 의도: API 편의와 실행 계획을 혼동하지 않는지 확인한다.
> 핵심: 아니다. 명세는 구조를 돕고, 성능은 인덱스와 쿼리 계획이 좌우한다.

## 한 줄 정리

Specification 패턴은 조건문을 조합 가능한 명세로 바꿔, backend의 검색과 검증 규칙을 재사용 가능하게 만든다.
