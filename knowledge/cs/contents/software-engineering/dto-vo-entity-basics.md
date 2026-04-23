# DTO, VO, Entity 기초 (DTO, VO, Entity Basics)

> 한 줄 요약: DTO는 데이터 전달 포맷, VO는 값 동등성을 가진 도메인 개념, Entity는 식별자로 추적하는 저장 단위이며, 셋을 뒤섞으면 변경 비용이 빠르게 커진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Repository, DAO, Entity](./repository-dao-entity.md)
- [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
- [database 카테고리 인덱스](../database/README.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: dto vo entity 차이, dto 뭐예요, value object 설명, entity 설명, dto vs entity, dto vs vo, request dto response dto, jpa entity vs domain entity, 도메인 객체 차이, dto 왜 쓰나요, 입문 dto, beginner dto entity vo

## 핵심 개념

세 개의 이름이 자주 함께 나오다 보니 같은 것처럼 느껴지지만, 각각이 답하는 질문이 다르다.

- **DTO (Data Transfer Object)** — "이 데이터를 어떤 형태로 주고받을까?" 계층 간 전달을 위한 컨테이너. 로직을 가지지 않고 필드와 생성자/접근자만 있다.
- **VO (Value Object)** — "이 값이 무엇인지"가 중요하고, 식별자가 아닌 값 자체로 동등성을 따진다. 예: `Money(1000, "KRW)`.
- **Entity** — "이 객체가 누구인지(식별자)"가 중요하고, 식별자가 같으면 같은 객체로 취급한다. 예: 주문 ID가 같으면 같은 주문.

입문자가 가장 많이 겪는 혼란은 JPA `@Entity`를 곧 도메인 모델로 쓰고, API 응답에도 같이 사용하는 경우다.

## 한눈에 보기

| 구분 | 핵심 관심사 | 동등성 기준 | 불변성 | 위치 |
|---|---|---|---|---|
| DTO | 데이터 전달 형태 | 보통 없음 | 선택 (record 권장) | Controller ↔ Service 사이, API 경계 |
| VO | 값의 의미와 불변식 | 값 필드 전체 | 불변 | Domain 레이어 |
| Entity | 식별자 기반 추적 | ID | 가변 허용 | Domain 레이어, Persistence 레이어 |

## 상세 분해

**DTO**

DTO는 호출자와 피호출자 사이의 계약을 좁히는 역할이다. HTTP 요청을 받는 `RequestDto`, 응답을 내보내는 `ResponseDto`, 서비스 간 전달에 쓰는 `CommandDto` 등이 있다.

```java
public record CreateOrderRequest(String productId, int quantity) {}
public record OrderSummaryResponse(String orderId, String status, int total) {}
```

**VO (Value Object)**

VO는 같은 값이면 같은 것이다. `new Money(1000, "KRW").equals(new Money(1000, "KRW"))`는 `true`여야 한다. 불변으로 만들고, 값 검증 로직을 생성자에 담는다.

```java
public record Money(int amount, String currency) {
    public Money {
        if (amount < 0) throw new IllegalArgumentException("금액은 음수일 수 없다");
    }
}
```

**Entity**

Entity는 ID가 같으면 같은 객체다. 같은 사람이 이름을 바꿔도 여전히 같은 사람인 것처럼, 필드가 바뀌어도 ID가 같으면 동일 엔티티다.

- JPA `@Entity`는 테이블 매핑 기술 도구이고, 도메인 Entity와 꼭 같은 개념이 아니다.
- 도메인 Entity는 비즈니스 규칙과 불변식을 담는 객체이고, JPA `@Entity`는 저장 포맷이다.

## 흔한 오해와 함정

- "JPA `@Entity` = 도메인 모델"이라 생각하면, 저장 구조가 바뀔 때 도메인 로직도 같이 흔들린다.
- DTO를 여러 용도에 재사용하면 점점 필드가 늘어나 어느 시점에 어떤 필드가 채워지는지 파악하기 어렵다. 용도별 DTO를 따로 두는 편이 낫다.
- VO를 가변 객체로 만들면 "값이 같으면 같다"는 계약이 깨진다. VO는 반드시 불변으로.

## 실무에서 쓰는 모습

Spring 웹 레이어에서는 컨트롤러가 `RequestDto`를 받아 서비스에 `Command`나 파라미터로 전달하고, 서비스는 `ResponseDto`를 반환하는 흐름이 일반적이다. 도메인 `Entity`와 JPA `@Entity`를 분리하고 사이에 변환 로직을 두면, ORM을 바꾸거나 조회 최적화를 해도 도메인 코드가 안전하다.

## 더 깊이 가려면

- [Repository, DAO, Entity](./repository-dao-entity.md) — Entity와 Repository의 역할 분리
- [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) — DTO/Entity가 경계를 넘을 때 생기는 문제 패턴

## 면접/시니어 질문 미리보기

- "DTO와 VO의 차이가 뭔가요?" — DTO는 데이터를 담아 나르는 그릇이고, VO는 값 자체가 의미이고 동등성을 값으로 판단한다. VO는 불변이고 도메인 규칙을 담을 수 있다.
- "JPA Entity를 API 응답으로 직접 반환하면 왜 문제가 되나요?" — Lazy 로딩 예외, 직렬화 문제, 테이블 컬럼이 그대로 노출되어 API 계약이 DB 구조에 묶이는 문제가 생긴다.
- "Immutable DTO는 어떻게 만드나요?" — Java 16+의 `record`를 쓰면 자동으로 불변 DTO가 된다.

## 한 줄 정리

DTO는 전달 포맷, VO는 값의 의미, Entity는 식별자 추적이며, 셋의 경계를 분리해야 변경 이유가 서로 섞이지 않는다.
