# Architecture and Layering Fundamentals

> 한 줄 요약: Layered Architecture, Clean Architecture, Modular Monolith, DDD boundary, Repository/Entity separation은 서로 경쟁하는 선택지가 아니라 서로 다른 설계 질문에 답하는 도구다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [왜 같이 헷갈리는가](#왜-같이-헷갈리는가)
- [한 장으로 구분하기](#한-장으로-구분하기)
- [Layered Architecture](#layered-architecture)
- [Clean Architecture](#clean-architecture)
- [Modular Monolith](#modular-monolith)
- [DDD 경계: Bounded Context와 Aggregate](#ddd-경계-bounded-context와-aggregate)
- [Repository와 Entity를 왜 나누는가](#repository와-entity를-왜-나누는가)
- [한 시스템 안에서 함께 배치하기](#한-시스템-안에서-함께-배치하기)
- [처음 설계할 때 추천 순서](#처음-설계할-때-추천-순서)
- [자주 하는 실수](#자주-하는-실수)

</details>

> 관련 문서:
> - [Software Engineering README: Architecture and Layering Fundamentals](./README.md#architecture-and-layering-fundamentals)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Design Pattern: Ports and Adapters vs GoF 패턴](../design-pattern/ports-and-adapters-vs-classic-patterns.md)
> - [Design Pattern: Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](../design-pattern/hexagonal-ports-pattern-language.md)
> - [System Design: Control Plane / Data Plane Separation 설계](../system-design/control-plane-data-plane-separation-design.md)
>
> retrieval-anchor-keywords: architecture layering fundamentals, layered architecture beginner, clean architecture beginner, ports and adapters beginner, hexagonal architecture beginner, modular monolith beginner, ddd boundary beginner, bounded context beginner, aggregate boundary, repository vs entity, repository vs dao, repository entity separation, domain model vs persistence model, layering primer, clean vs layered, hexagonal folder layout, modular monolith vs microservice, ports and adapters vs gof pattern, hexagonal ports pattern language, control plane vs layered architecture, control plane data plane boundary, software engineering cross-category bridge

구조 이름이 비슷해서 코드-level 경계와 패턴-level 경계를 자주 섞는다면 [Design Pattern: Ports and Adapters vs GoF 패턴](../design-pattern/ports-and-adapters-vs-classic-patterns.md), [Design Pattern: Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](../design-pattern/hexagonal-ports-pattern-language.md)로 내려가면 용어 축이 더 선명해진다.
코드 계층을 런타임 plane 분리까지 확장해서 보고 싶다면 [System Design: Control Plane / Data Plane Separation 설계](../system-design/control-plane-data-plane-separation-design.md)로 이어 보면 좋다.

## 왜 같이 헷갈리는가

처음 설계를 공부할 때는 이름이 모두 비슷하게 들린다.
하지만 실제로는 각 개념이 답하는 질문이 다르다.

- Layered Architecture는 코드를 어떤 층으로 나눌지 묻는다.
- Clean Architecture는 의존성이 어느 방향으로 흘러야 하는지 묻는다.
- Modular Monolith는 하나의 배포 안에서 기능 경계를 어떻게 지킬지 묻는다.
- DDD boundary는 비즈니스 언어와 규칙을 어디까지 같은 모델로 볼지 묻는다.
- Repository와 Entity separation은 도메인 모델과 저장 포맷을 어떻게 분리할지 묻는다.

그래서 한 시스템 안에 이 다섯 가지가 동시에 들어가도 이상하지 않다.

## 한 장으로 구분하기

| 내가 답하고 싶은 질문 | 보는 개념 | 초심자용 핵심 문장 |
|---|---|---|
| 코드를 어떤 층으로 나눌까 | Layered Architecture | 화면, 유스케이스, 도메인, 인프라 같은 역할별 층을 만든다 |
| 의존성을 어느 방향으로 고정할까 | Clean Architecture | 바깥 기술이 안쪽 도메인에 의존하게 만든다 |
| 배포는 하나인데 기능 경계는 어떻게 지킬까 | Modular Monolith | 배포는 하나로 유지하되 내부 모듈 경계는 강하게 지킨다 |
| 어떤 비즈니스 언어를 같은 모델로 볼까 | DDD boundary | 같은 단어가 같은 의미인 범위만 같은 모델로 묶는다 |
| 저장 포맷과 도메인 규칙을 어떻게 분리할까 | Repository와 Entity separation | 도메인은 저장 세부를 모르고, 저장 계층이 변환을 책임진다 |

이 표를 먼저 잡아두면 "이 개념들이 서로 대체 관계인가?"라는 혼란이 많이 줄어든다.

## Layered Architecture

Layered Architecture는 가장 익숙한 출발점이다.
보통 아래처럼 역할별로 층을 나눈다.

- Presentation: HTTP, CLI, UI 입력/출력
- Application: 유스케이스 조합, 흐름 제어
- Domain: 핵심 규칙, 상태, 불변식
- Infrastructure: DB, 메시지 브로커, 외부 API, 파일 시스템

좋은 점:

- 읽기 쉽다
- 팀 합의가 쉽다
- 작은 CRUD 서비스에 빠르게 적용된다

조심할 점:

- 서비스 계층이 모든 규칙을 떠안으면 도메인이 빈 껍데기가 되기 쉽다
- 도메인 코드가 프레임워크 어노테이션과 DB 타입에 묶이기 쉽다
- 계층이 단순 전달만 하면 구조는 있어도 의미는 약해진다

초심자에게는 "레이어를 나누는 것" 자체보다 "각 레이어가 무엇을 몰라야 하는가"를 같이 보는 게 중요하다.

## Clean Architecture

Clean Architecture는 레이어 개수보다 **의존성 방향**을 더 중요하게 본다.

- 안쪽에는 도메인 규칙이 있다
- 바깥에는 프레임워크와 DB 같은 기술 세부가 있다
- 바깥이 안쪽에 의존해야지, 안쪽이 바깥 기술에 의존하면 안 된다

초심자 관점에서는 이렇게 이해하면 된다.

- Layered Architecture가 "층을 어떻게 나눌까"라면
- Clean Architecture는 "그 층들이 어느 방향으로 의존해야 할까"다

즉, 레이어드 구조처럼 보여도 도메인이 JPA 엔티티, 웹 DTO, 외부 SDK를 직접 알면 clean하지 않다.

언제 도움이 큰가:

- 도메인 규칙이 자주 바뀐다
- 테스트에서 인프라를 떼고 싶다
- 프레임워크 교체나 외부 시스템 교체 가능성이 있다

## Modular Monolith

Modular Monolith는 "서비스를 여러 개로 쪼개기 전 단계"가 아니라, 많은 경우 **오래 유지해도 되는 기본 선택지**다.

핵심은 두 가지다.

- 배포 단위는 하나다
- 내부 모듈 경계는 기능과 소유권 기준으로 강하게 나눈다

예를 들어 `order`, `payment`, `catalog` 모듈이 있으면:

- 각 모듈은 자기 공개 API만 외부에 보여준다
- 다른 모듈은 내부 클래스나 내부 엔티티를 직접 참조하지 않는다
- 모듈 간 협력은 공개 인터페이스나 애플리케이션 이벤트로 제한한다

초심자가 자주 헷갈리는 지점은 "패키지를 나눴으니 modular monolith"라고 생각하는 것이다.
하지만 패키지 분리만 있고 의존 규칙이 없으면 그냥 큰 모놀리스다.

## DDD 경계: Bounded Context와 Aggregate

DDD에서 가장 먼저 구분해야 할 건 경계의 종류다.

| 경계 | 무엇을 나누는가 | 초심자용 질문 |
|---|---|---|
| Bounded Context | 모델과 언어 | 이 단어가 이 범위 안에서만 같은 의미인가 |
| Aggregate | 강한 정합성과 규칙 | 어떤 객체들이 반드시 함께 일관되게 바뀌어야 하는가 |
| Module/Package | 코드 구조와 소유권 | 어떤 코드를 함께 바꾸고 숨길 것인가 |

중요한 포인트:

- Bounded Context는 "비즈니스 언어 경계"다
- Aggregate는 "트랜잭션과 불변식 경계"다
- Module은 "코드 관리 경계"다

이 셋은 자주 연결되지만, 항상 1:1로 맞지 않는다.

예를 들어:

- `주문`과 `결제`가 다른 언어와 규칙을 가지면 다른 bounded context일 수 있다
- `주문` context 안에도 `Order`, `Coupon` 같은 여러 aggregate가 있을 수 있다
- 코드 배치는 한 context를 여러 module로 나눌 수도 있고, 작은 팀에서는 한 module에 담을 수도 있다

초심자에게는 "context는 말의 경계, aggregate는 규칙의 경계"라고 먼저 잡아두는 게 가장 도움이 된다.

## Repository와 Entity를 왜 나누는가

Repository는 보통 **도메인 언어**로 말한다.
Entity는 보통 **저장 포맷**으로 말한다.

```java
// domain
public interface OrderRepository {
    Optional<Order> findById(OrderId id);
    void save(Order order);
}

// infrastructure
@Entity
class OrderEntity {
    Long id;
    String status;
}

class JpaOrderRepository implements OrderRepository {
    private final SpringDataOrderJpaRepository jpaRepository;
    private final OrderEntityMapper mapper;

    @Override
    public Optional<Order> findById(OrderId id) {
        return jpaRepository.findById(id.value())
                .map(mapper::toDomain);
    }
}
```

위 예시에서 역할은 이렇게 나뉜다.

- `OrderRepository`는 도메인이 필요한 저장 동작을 말한다
- `OrderEntity`는 ORM이나 테이블 구조에 맞는 저장 모델이다
- `JpaOrderRepository`와 `OrderEntityMapper`는 둘 사이를 연결한다

왜 분리하나:

- DB 스키마 변경이 도메인 규칙을 덜 흔들게 하려고
- 도메인 모델에 ORM 세부가 퍼지는 걸 막으려고
- API 응답 모델, 도메인 모델, 저장 모델이 뒤섞이는 걸 막으려고

초심자가 특히 조심할 점은 "JPA Entity를 곧바로 도메인 객체이자 API 응답으로 같이 쓰는 것"이다.
처음엔 편하지만 규칙, 조회 최적화, 직렬화 요구가 섞이면서 변경 비용이 빠르게 커진다.

## 한 시스템 안에서 함께 배치하기

아래처럼 한 시스템 안에 여러 개념이 동시에 들어갈 수 있다.

```text
app/
  order/
    presentation/
    application/
    domain/
      Order.java
      OrderRepository.java
    infrastructure/
      persistence/
        OrderEntity.java
        JpaOrderRepository.java
  payment/
    presentation/
    application/
    domain/
    infrastructure/
```

이 구조를 읽는 방법:

- Layered Architecture: 각 모듈 안에 presentation, application, domain, infrastructure를 둔다
- Clean Architecture: application/domain은 infrastructure 구현을 직접 모르고 인터페이스만 본다
- Modular Monolith: `order`와 `payment`는 같은 배포 안에 있지만 내부 구현은 서로 숨긴다
- DDD boundary: `order`와 `payment`가 서로 다른 용어와 규칙을 가지면 다른 bounded context로 본다
- Repository/Entity separation: 각 모듈의 domain에는 repository 인터페이스를 두고, infrastructure에는 entity와 구현체를 둔다

즉 "한 프로젝트는 하나의 아키텍처만 가져야 한다"가 아니라, **같은 프로젝트 안에서 서로 다른 관점이 겹쳐서 동작한다**고 보는 편이 맞다.

## 처음 설계할 때 추천 순서

1. 먼저 레이어를 단순하게 나눠서 코드 역할을 분리한다.
2. 도메인 규칙과 불변식을 domain 안으로 모아 service god class를 피한다.
3. 프레임워크 세부가 안쪽으로 새기 시작하면 repository interface, port 같은 경계를 도입한다.
4. 기능이 커지면 모듈 경계를 나누고 다른 모듈 내부 구현 참조를 막는다.
5. 용어와 규칙이 달라지면 bounded context를 다시 그린다.

처음부터 모든 패턴을 한 번에 넣기보다, **변경 비용이 커지는 지점에 맞춰 경계를 강화하는 방식**이 현실적이다.

## 자주 하는 실수

- Layered, Clean, DDD, Modular Monolith를 서로 하나만 골라야 하는 선택지처럼 본다
- 패키지 분리만 해두고 모듈 경계가 생겼다고 착각한다
- JPA Entity를 도메인 모델, API DTO, 저장 모델로 모두 같이 쓴다
- aggregate 경계와 서비스 배포 경계를 무조건 1:1로 맞추려 한다
- 모듈 경계도 약한데 너무 빨리 MSA로 넘어간다

한 줄 기준으로 정리하면 이렇다.

- Layered는 역할 분리
- Clean은 의존 방향 제어
- Modular Monolith는 내부 모듈 경계 강화
- DDD boundary는 비즈니스 언어와 규칙 경계 정리
- Repository/Entity separation은 도메인과 저장 세부 분리
