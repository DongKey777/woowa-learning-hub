---
schema_version: 3
title: Architecture and Layering Fundamentals
concept_id: software-engineering/architecture-layering-fundamentals
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/roomescape
- missions/lotto
- missions/baseball
- missions/shopping-cart
review_feedback_tags:
- architecture-choice
- service-bloat-root-cause
- dto-boundary-confusion
aliases:
- architecture layering fundamentals
- layered architecture map
- beginner architecture map
- modular monolith beginner
- bounded context 처음
- repository entity separation
- dto contract 어디까지
- service가 너무 비대해요
- clean architecture beginner
- 계층 설계 전체 그림
symptoms:
- layered, clean, modular monolith가 서로 대체 관계인지 헷갈려요
- controller service repository는 있는데 왜 계속 복잡한지 모르겠어요
- entity, dto, repository 경계를 어디서 끊어야 하는지 감이 안 와요
intents:
- definition
- comparison
- design
prerequisites:
- software-engineering/woowacourse-backend-mission-prerequisite-primer
- software-engineering/oop-design-basics
next_docs:
- software-engineering/layered-architecture-basics
- software-engineering/clean-architecture-layered-modular-monolith
- software-engineering/repository-dao-entity
linked_paths:
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/ports-and-adapters-beginner-primer.md
- contents/software-engineering/clean-architecture-layered-modular-monolith.md
- contents/software-engineering/repository-dao-entity.md
- contents/software-engineering/dto-vo-entity-basics.md
- contents/software-engineering/module-api-dto-patterns.md
- contents/software-engineering/ddd-hexagonal-consistency.md
confusable_with:
- software-engineering/layered-architecture-basics
- software-engineering/clean-architecture-layered-modular-monolith
- software-engineering/ddd-hexagonal-consistency
forbidden_neighbors: []
expected_queries:
- layered architecture, clean architecture, modular monolith 차이를 한 번에 잡고 싶어
- controller service repository 다음에 어떤 설계 질문을 붙여서 공부해야 해?
- 패키지는 나눴는데 왜 여전히 구조가 복잡하다는 피드백을 받는 거야?
- entity, dto, repository를 같은 모델로 쓰면 왜 경계가 흐려진다고 해?
- 아키텍처 입문에서 layered랑 bounded context를 어떤 순서로 이해하면 돼?
contextual_chunk_prefix: |
  이 문서는 layered architecture, clean architecture, modular monolith,
  DDD boundary, repository/entity separation, DTO contract를 하나의
  초심자 지도에서 연결해 주는 primer다. 구조 이름을 외우기보다 지금 어떤
  설계 질문을 하고 있는지 구분하려는 학습자에게 맞춰, 역할 분리 문제인지,
  의존 방향 문제인지, 모듈 공개 범위 문제인지, 경계 번역 문제인지를
  가려 읽게 돕는 문서라는 맥락을 각 청크 앞에 붙인다.
---
# Architecture and Layering Fundamentals

> 한 줄 요약: Layered Architecture, Clean Architecture, Modular Monolith, DDD boundary, Repository/Entity separation, DTO contract는 서로 경쟁하는 선택지가 아니라 서로 다른 설계 질문에 답하는 도구다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [계층형 아키텍처 기초](./layered-architecture-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)
- [Module API DTO Patterns](./module-api-dto-patterns.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)


retrieval-anchor-keywords: architecture layering fundamentals, layered architecture vs clean architecture 차이, modular monolith 뭐예요, bounded context 처음, repository entity separation, dto contract 어디까지, entity를 dto로 써도 되나요, service가 너무 비대해요, 패키지만 나눴는데 왜 복잡해요, clean architecture beginner, modular monolith beginner, beginner architecture map, what is layered architecture, software engineering bridge

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "controller/service/repository는 나눴는데 왜 계속 service가 비대하대요?" | roomescape나 shopping-cart 유스케이스가 service 한 클래스에 쌓이는 코드 | 계층 이름보다 유스케이스 조립, 도메인 규칙, 저장 경계가 어디 섞였는지 본다 |
| "Clean Architecture랑 Layered Architecture 중 하나를 골라야 하나요?" | 미션 구조 개선을 아키텍처 이름 대결로 이해하는 상황 | 서로 대체 관계보다 의존 방향, 모듈 공개 범위, 경계 번역 질문을 구분한다 |
| "Entity를 DTO로 바로 써도 되는지 리뷰가 계속 달려요" | API 응답 모델과 저장 모델, 도메인 객체가 같은 타입으로 흘러나가는 코드 | 내부 모델과 외부 계약의 변경 이유가 같은지 먼저 확인한다 |

<details>
<summary>Table of Contents</summary>

- [왜 같이 헷갈리는가](#왜-같이-헷갈리는가)
- [어디까지 읽고 멈출까](#어디까지-읽고-멈출까)
- [한 장으로 구분하기](#한-장으로-구분하기)
- [Layered Architecture](#layered-architecture)
- [Clean Architecture](#clean-architecture)
- [Modular Monolith](#modular-monolith)
- [DDD 경계: Bounded Context와 Aggregate](#ddd-경계-bounded-context와-aggregate)
- [Repository와 Entity를 왜 나누는가](#repository와-entity를-왜-나누는가)
- [DTO 계약은 어느 경계에서 끊을까](#dto-계약은-어느-경계에서-끊을까)
- [한 시스템 안에서 함께 배치하기](#한-시스템-안에서-함께-배치하기)
- [처음 설계할 때 추천 순서](#처음-설계할-때-추천-순서)
- [자주 하는 실수](#자주-하는-실수)

</details>

## 먼저 떠올릴 그림

초심자는 구조 이름을 외우기보다, 같은 주문 변경을 네 질문으로 나눠 보면 훨씬 덜 헷갈린다.

| 지금 보는 질문 | 먼저 붙일 이름 | 한 줄 판단 |
|---|---|---|
| 요청을 어디서 받고 검증하지? | Layered Architecture | presentation과 application의 역할을 가른다 |
| 누가 누구를 알아도 되지? | Clean Architecture | 바깥 기술이 안쪽 규칙에 의존하게 만든다 |
| `order`와 `payment`는 어디까지 서로 열어 둘까? | Modular Monolith | 같은 배포 안에서도 모듈 API만 공개한다 |
| request DTO, domain, entity를 어디서 끊지? | DTO/Repository 분리 | 경계마다 계약을 한 번씩 번역한다 |

## 왜 같이 헷갈리는가

처음 설계를 공부할 때는 이름이 모두 비슷하게 들린다.
하지만 실제로는 각 개념이 답하는 질문이 다르다.

- Layered Architecture는 코드를 어떤 층으로 나눌지 묻는다.
- Clean Architecture는 의존성이 어느 방향으로 흘러야 하는지 묻는다.
- Modular Monolith는 하나의 배포 안에서 기능 경계를 어떻게 지킬지 묻는다.
- DDD boundary는 비즈니스 언어와 규칙을 어디까지 같은 모델로 볼지 묻는다.
- Repository와 Entity separation은 도메인 모델과 저장 포맷을 어떻게 분리할지 묻는다.

그래서 한 시스템 안에 이 다섯 가지가 동시에 들어가도 이상하지 않다.

## 어디까지 읽고 멈출까

이 문서는 `controller-service-repository`를 막 이해한 초심자가 **"이제 구조 이름이 2개 이상 섞여 보여요"**라고 느낄 때 여는 브리지다.

| 지금 상태 | 여기서 얻을 것 | 다음 한 걸음 |
|---|---|---|
| Controller/Service/Repository 경계가 아직 흐리다 | 구조 이름 비교보다 `입력 / 규칙 / 저장` 기본 경계를 다시 잡는다 | [계층형 아키텍처 기초](./layered-architecture-basics.md) |
| 경계는 아는데 `layered`, `clean`, `modular monolith`가 왜 동시에 나오나 헷갈린다 | 각 이름이 답하는 질문이 다르다는 비교표 | 이 문서의 `한 장으로 구분하기`까지만 읽는다 |
| port, adapter, bounded context 같은 심화 용어까지 이어 보고 싶다 | starter 밖 follow-up 동선 | [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md), [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md) |

- stop rule: `지금 막힌 질문 1개`와 `다음 문서 1개`가 정해졌다면 여기서 멈추면 된다.
- design pattern 비교, runtime plane, 운영 구조는 이 문서의 중심이 아니라 후속 학습 주제다.

## 지금 어떤 문장으로 막혔는지부터 고르기

| 머릿속 문장 | 먼저 볼 관점 |
|---|---|
| "`controller-service-repository`는 있는데 왜 계속 복잡하지?" | Layered Architecture와 Clean Architecture를 같이 본다 |
| "패키지는 나눴는데 모듈 경계가 없다는 피드백을 받았다" | Modular Monolith 관점으로 본다 |
| "`주문 상태`라는 말이 팀마다 다르게 들린다" | DDD boundary 관점으로 본다 |
| "`@Entity`가 도메인, 응답, 저장을 다 맡고 있다" | Repository와 Entity separation 관점으로 본다 |
| "request DTO나 module DTO가 domain object처럼 끝까지 간다" | DTO contract 관점으로 본다 |

## 한 장으로 구분하기

| 내가 답하고 싶은 질문 | 보는 개념 | 초심자용 핵심 문장 |
|---|---|---|
| 코드를 어떤 층으로 나눌까 | Layered Architecture | 화면, 유스케이스, 도메인, 인프라 같은 역할별 층을 만든다 |
| 의존성을 어느 방향으로 고정할까 | Clean Architecture | 바깥 기술이 안쪽 도메인에 의존하게 만든다 |
| 배포는 하나인데 기능 경계는 어떻게 지킬까 | Modular Monolith | 배포는 하나로 유지하되 내부 모듈 경계는 강하게 지킨다 |
| 어떤 비즈니스 언어를 같은 모델로 볼까 | DDD boundary | 같은 단어가 같은 의미인 범위만 같은 모델로 묶는다 |
| 저장 포맷과 도메인 규칙을 어떻게 분리할까 | Repository와 Entity separation | 도메인은 저장 세부를 모르고, 저장 계층이 변환을 책임진다 |

이 표를 먼저 잡아두면 "이 개념들이 서로 대체 관계인가?"라는 혼란이 많이 줄어든다.

짧게 외우면:

- layered는 자리 배치다
- clean은 의존 방향이다
- modular monolith는 내부 공개 범위다
- dto/repository 분리는 경계 번역이다

## 막힐 때 먼저 나눌 질문

초심자는 용어 정의보다 **지금 어디가 헷갈리는지**부터 나누는 편이 빠르다.

| 지금 보이는 증상 | 먼저 붙잡을 질문 | 이 문서에서 연결되는 개념 |
|---|---|---|
| `controller-service-repository`는 나눴는데 service가 계속 비대해진다 | 역할 분리만 했지, 도메인 규칙과 의존 방향은 아직 안 섞였나 | Layered Architecture, Clean Architecture |
| 패키지는 나눴는데 `order`가 `payment` 내부 클래스를 계속 참조한다 | 모듈 경계를 폴더가 아니라 공개 API 기준으로 막고 있나 | Modular Monolith |
| `주문 상태`라는 말이 화면, 결제, 정산에서 조금씩 다른 뜻으로 쓰인다 | 같은 단어를 정말 같은 모델로 묶어도 되나 | DDD boundary |
| JPA `@Entity`가 API 응답, 도메인 규칙, 저장 매핑을 전부 떠안는다 | 저장 모양과 도메인 규칙을 분리해야 하나 | Repository와 Entity separation |
| request DTO나 module DTO가 저장 계층까지 흘러간다 | 경계마다 계약을 한 번 더 끊어야 하나 | DTO contract, Repository와 Entity separation |

즉 "어떤 아키텍처가 정답인가?"보다 "지금의 증상이 어떤 질문에 해당하나?"를 먼저 고르면 문서 선택이 쉬워진다.

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

짧게 비교하면:

- Layered는 책임을 세로로 나누는 출발점이다
- Clean은 그 책임들 사이 의존성을 안쪽으로 고정하는 보강 규칙이다

그래서 "레이어드 구조를 쓰면 clean은 못 쓴다"가 아니라, **레이어드 구조를 clean하게 운영할 수 있느냐**가 실제 질문에 가깝다.

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

한 줄 체크:

- 모듈 밖에서 내부 패키지를 import해도 되는가
- 다른 모듈의 entity를 직접 끌어다 써도 되는가
- 모듈 간 호출 경로가 공개 서비스나 이벤트로 모여 있는가

이 질문에 "다 열려 있다"면 modular monolith라기보다 패키지만 나눈 monolith일 가능성이 크다.

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

이 주제가 특히 헷갈리면 [Repository, DAO, Entity](./repository-dao-entity.md)가 같은 주문 생성 예시로 한 단계 더 천천히 내려가서 설명한다.

## DTO 계약은 어느 경계에서 끊을까

아키텍처 이름이 늘어나기 시작하면 초심자는 `DTO를 어디까지 들고 가야 하는지`도 같이 헷갈린다.
안전한 기본값은 **바깥 계약은 DTO로 받고, 안쪽 규칙은 domain object로 만들고, 저장 직전에는 persistence entity로 다시 끊는 것**이다.

| 경계 | 기본 계약 | 왜 여기서 끊나 |
|---|---|---|
| Controller -> Service | request DTO 또는 command | HTTP 요청 모양을 유스케이스 입력으로 한 번 번역하려고 |
| Service -> Domain | domain object, value object | 규칙을 웹/배치/메시지 형식과 분리하려고 |
| Domain -> Repository | repository interface + domain object | 도메인이 저장 기술 세부를 모르도록 하려고 |
| Repository 구현 -> DB | entity, mapper | 테이블/ORM 모양을 저장 계층 안에 가두려고 |
| Module -> Module | command/query/result DTO | 같은 JVM 안에서도 모듈 내부 모델을 숨기려고 |

짧은 주문 예시로 보면 이렇다.

- Controller는 `CreateOrderRequest`를 `CreateOrderCommand`로 바꿔 Service에 넘긴다.
- Service는 `Order.create(...)`로 domain 규칙을 적용한다.
- Repository 구현체는 `OrderEntity`로 바꿔 저장한다.
- `payment` 모듈이 `order` 모듈을 호출할 때는 `MarkOrderPaidCommand` 같은 모듈 API DTO를 쓴다.

자주 나오는 오해는 두 가지다.

- "DTO는 그냥 처음부터 끝까지 들고 가면 되지 않나요?"
  - 그러면 웹 입력 모양, 도메인 규칙, DB 컬럼 구조가 한 번에 묶인다.
- "`@Entity`를 응답 DTO로도 쓰면 코드가 줄지 않나요?"
  - 처음엔 줄어도 API 계약과 저장 구조가 같이 흔들려서 나중 비용이 커진다.

`DTO contract`를 별도 주제로 더 보고 싶다면 [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)와 [Module API DTO Patterns](./module-api-dto-patterns.md)이 바로 다음 연결 문서다.

## 한 시스템 안에서 함께 배치하기

아래처럼 한 시스템 안에 여러 개념이 동시에 들어갈 수 있다.

```text
app/
  order/
    presentation/
    application/
    api/
      MarkOrderPaidCommand.java
      MarkOrderPaidResult.java
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
- DTO contract: presentation DTO와 module api DTO는 domain/entity를 그대로 바깥에 노출하지 않는다

즉 "한 프로젝트는 하나의 아키텍처만 가져야 한다"가 아니라, **같은 프로젝트 안에서 서로 다른 관점이 겹쳐서 동작한다**고 보는 편이 맞다.

## 처음 설계할 때 추천 순서

1. 먼저 레이어를 단순하게 나눠서 코드 역할을 분리한다.
2. 도메인 규칙과 불변식을 domain 안으로 모아 service god class를 피한다.
3. 프레임워크 세부가 안쪽으로 새기 시작하면 repository interface, port 같은 경계를 도입한다.
4. request DTO, module DTO, entity를 한 타입으로 재사용하고 있다면 계약을 다시 끊는다.
5. 기능이 커지면 모듈 경계를 나누고 다른 모듈 내부 구현 참조를 막는다.
6. 용어와 규칙이 달라지면 bounded context를 다시 그린다.

처음부터 모든 패턴을 한 번에 넣기보다, **변경 비용이 커지는 지점에 맞춰 경계를 강화하는 방식**이 현실적이다.

## 자주 하는 실수

- Layered, Clean, DDD, Modular Monolith를 서로 하나만 골라야 하는 선택지처럼 본다
- 패키지 분리만 해두고 모듈 경계가 생겼다고 착각한다
- JPA Entity를 도메인 모델, API DTO, 저장 모델로 모두 같이 쓴다
- request DTO나 module DTO를 domain 규칙 객체 대신 끝까지 재사용한다
- aggregate 경계와 서비스 배포 경계를 무조건 1:1로 맞추려 한다
- 모듈 경계도 약한데 너무 빨리 MSA로 넘어간다
- bounded context와 패키지명을 같은 뜻으로 취급한다
- repository 인터페이스를 만들었는데도 서비스가 JPA 전용 타입을 그대로 다룬다

한 줄 기준으로 정리하면 이렇다.

- Layered는 역할 분리
- Clean은 의존 방향 제어
- Modular Monolith는 내부 모듈 경계 강화
- DDD boundary는 비즈니스 언어와 규칙 경계 정리
- Repository/Entity separation은 도메인과 저장 세부 분리

## 다음 한 걸음

| 지금 더 필요한 것 | 다음 문서 |
|---|---|
| 레이어를 같은 주문 생성 예시로 더 천천히 보고 싶다 | [계층형 아키텍처 기초](./layered-architecture-basics.md) |
| port, adapter, 의존 방향을 실제 경계 언어로 다시 보고 싶다 | [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) |
| 용어 비교보다 deeper trade-off 표가 필요하다 | [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md) |

## 한 줄 정리

Layered Architecture, Clean Architecture, Modular Monolith, DDD boundary, Repository/Entity separation, DTO contract는 서로 경쟁하는 선택지가 아니라 서로 다른 설계 질문에 답하는 도구다.
