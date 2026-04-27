# Persistence Follow-up Question Guide

> 한 줄 요약: 처음 영속성 문서를 읽다가 막히면 용어를 더 외우기보다, "지금 막힌 질문이 저장 계약인지, 이름 냄새인지, 읽기 분리인지, JPA 매핑인지, ORM 누수인지"를 먼저 골라 다음 문서를 정하면 훨씬 빠르다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: persistence follow up question guide basics, persistence follow up question guide beginner, persistence follow up question guide intro, software engineering basics, beginner software engineering, 처음 배우는데 persistence follow up question guide, persistence follow up question guide 입문, persistence follow up question guide 기초, what is persistence follow up question guide, how to persistence follow up question guide
<details>
<summary>Table of Contents</summary>

- [왜 이 가이드가 필요한가](#왜-이-가이드가-필요한가)
- [먼저 잡는 한 줄 멘탈 모델](#먼저-잡는-한-줄-멘탈-모델)
- [한 질문씩 내려가는 결정표](#한-질문씩-내려가는-결정표)
- [짧은 예시: 주문 저장 코드를 보고 어디로 갈까](#짧은-예시-주문-저장-코드를-보고-어디로-갈까)
- [자주 헷갈리는 지점](#자주-헷갈리는-지점)
- [초심자용 가장 안전한 읽기 순서](#초심자용-가장-안전한-읽기-순서)

</details>

> 관련 문서:
> - [Software Engineering README: Persistence Follow-up Question Guide](./README.md#persistence-follow-up-question-guide)
> - [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
> - [Repository Naming Smells Primer](./repository-naming-smells-primer.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md)
> - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
> - [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md)
> - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
> - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
>
> retrieval-anchor-keywords: persistence follow-up question guide, persistence decision table beginner, single question persistence table, repository interface contract follow-up, repository naming smells follow-up, dao vs query model entrypoint guide, persistence adapter mapping checklist next step, aggregate persistence mapping pitfalls guide, persistence model leakage anti-patterns entrypoint, beginner persistence reading order, beginner persistence decision map, beginner persistence bridge, repository to leakage guide, repository interface to leakage path, persistence doc chooser beginner, 질문형 결정표 영속성, 영속성 follow-up 선택 가이드, 영속성 문서 선택표, repository primer 다음 문서, JPA 초심자 다음 문서 고르기, ORM 누수 문서 선택, persistence beginner wayfinding, 초심자 영속성 결정표, repository interface contract primer 다음, persistence leakage anti-patterns 전에 읽기

## 왜 이 가이드가 필요한가

초심자는 보통 영속성 문서를 읽다가 이런 식으로 멈춘다.

- "`Repository`를 왜 인터페이스로 두는지는 알겠는데, 다음엔 뭘 읽지?"
- "이건 repository 이름 문제인가, DAO 문제인가, JPA 매핑 문제인가?"
- "조회 화면 때문에 복잡한 건데 왜 자꾸 엔티티 얘기만 나오지?"
- "서비스 코드에 `Entity`가 보이는데 이게 그냥 흔한 코드인지, 누수인지 모르겠다"

이때 문서를 제목 순서대로 더 읽기 시작하면 오히려 더 섞인다.

초심자에게 더 안전한 기준은 이것이다.

- **지금 막힌 질문의 종류를 먼저 고르고, 그 질문에 맞는 다음 문서 1개만 연다.**

## 먼저 잡는 한 줄 멘탈 모델

영속성 문서를 고를 때는 "저장 기술"보다 먼저, **"지금 내가 결정하려는 게 계약인지, 번역인지, 누수인지"**를 본다.

- 계약: 안쪽 코드가 무엇을 약속받아야 하나?
- 이름/분리: 지금 책임이 repository, DAO, query model 중 어디에 더 가까운가?
- 번역: domain object와 JPA entity를 어디서 바꿔 끼우나?
- 누수: ORM 세부가 서비스, 도메인, API까지 새고 있나?

이 네 칸 중 어디가 막혔는지 고르면 다음 문서가 빨라진다.

## 한 질문씩 내려가는 결정표

한 번에 문서 제목을 다 비교하지 말고, 아래 질문을 위에서 아래로 한 줄씩만 따라가면 된다.

| 순서 | 먼저 스스로 묻는 질문 | `예`면 읽을 문서 | `아니오`면 다음 질문 |
|---|---|---|---|
| 1 | "`Repository`를 왜 인터페이스/계약으로 두는지부터 아직 흐릿한가?" | [Repository Interface Contract Primer](./repository-interface-contract-primer.md) | 2번으로 간다 |
| 2 | "지금 헷갈리는 게 메서드 말투와 이름 냄새인가?" | [Repository Naming Smells Primer](./repository-naming-smells-primer.md) | 3번으로 간다 |
| 3 | "문제가 저장보다 조회 화면, 목록, 검색 설계에 더 가깝나?" | [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md) | 4번으로 간다 |
| 4 | "domain object와 `Entity`를 어디서 바꿔 끼워야 할지가 핵심인가?" | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) | 5번으로 간다 |
| 5 | "`cascade`, `orphanRemoval`, 양방향 연관관계가 도메인 규칙처럼 느껴지나?" | [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md) | 6번으로 간다 |
| 6 | "서비스, 도메인, API 응답에 `@Entity`가 직접 보이는가?" | [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) | 아래 빠른 보조 표를 본다 |

위 표를 더 짧게 읽으면, 사실 질문은 하나다.

- **"지금 막힌 지점이 계약인가, 이름인가, 조회 분리인가, 매핑인가, 누수인가?"**

이 한 질문에 대한 답만 고르면 다음 문서가 정해진다.

### 빠른 보조 표

## 한 질문씩 내려가는 결정표 (계속 2)

| 지금 눈에 먼저 들어오는 신호 | 먼저 읽을 문서 | 바로 이어 읽을 문서 |
|---|---|---|
| `Repository` 자체가 왜 필요한지 모르겠다 | [Repository Interface Contract Primer](./repository-interface-contract-primer.md) | [Repository, DAO, Entity](./repository-dao-entity.md) |
| `save/find`보다 `insert/select/update` 말투가 더 많다 | [Repository Naming Smells Primer](./repository-naming-smells-primer.md) | [Repository, DAO, Entity](./repository-dao-entity.md) |
| 목록/검색 요구 때문에 repository 메서드가 계속 늘어난다 | [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md) | [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md) |
| 서비스가 `OrderEntity`를 직접 가져와 규칙을 수행한다 | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) | [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) |
| `cascade`와 aggregate 규칙이 같은 말처럼 들린다 | [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md) | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) |
| 컨트롤러 응답 타입이 `Entity`다 | [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) |

## 짧은 예시: 주문 저장 코드를 보고 어디로 갈까

```java
@Service
public class OrderService {
    private final OrderJpaRepository orderJpaRepository;

    public void changeAddress(Long orderId, String address) {
        OrderEntity entity = orderJpaRepository.findById(orderId).orElseThrow();
        entity.setAddress(address);
    }
}
```

초심자 기준으로는 한 번에 모든 문제를 보려 하지 않는 편이 낫다.

| 코드에서 먼저 눈에 띄는 신호 | 지금 열 문서 |
|---|---|
| `OrderJpaRepository`를 서비스가 직접 안다 | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) |
| `OrderEntity`가 서비스 규칙 변경의 중심이 된다 | [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) |
| "`Repository`인데 사실 Spring Data 인터페이스와 같은 말 아닌가?"가 헷갈린다 | [Repository Interface Contract Primer](./repository-interface-contract-primer.md) |

즉 이 코드는 "repository 계약"보다 "매핑/누수" 질문이 더 크다.
그래서 첫 문서는 `Repository Interface Contract Primer`보다 `Persistence Adapter Mapping Checklist`가 더 빠를 수 있다.

같은 예시를 질문형 결정표로 바로 따라가면 이렇게 읽는다.

| 질문 | 답 | 그래서 여는 문서 |
|---|---|---|
| `Repository` 계약 자체가 흐린가? | 아니오 | 다음 질문으로 간다 |
| 조회 화면/검색 설계가 핵심인가? | 아니오 | 다음 질문으로 간다 |
| domain과 `Entity`를 어디서 나눌지가 핵심인가? | 예 | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) |
| 서비스와 응답에 `Entity`가 이미 보이는가? | 예 | [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) |

## 자주 헷갈리는 지점

- "`Repository, DAO, Entity` 문서 하나만 읽으면 다 끝나지 않나요?"
  - 큰 분류를 잡는 데는 좋지만, 실제 막힌 질문이 이름 냄새인지 누수인지까지는 별도 primer가 더 빠르다.
- "`Persistence Model Leakage Anti-Patterns`부터 보면 제일 실전 아닌가요?"
  - 증상 확인에는 빠르지만, 정상 경계 모양이 먼저 없으면 anti-pattern이 그냥 체크리스트처럼 읽힐 수 있다.
- "`aggregate` 문서면 곧바로 DDD 심화인가요?"
  - 여기서는 DDD 이론보다 "`cascade`와 규칙을 같은 말로 착각하지 않기"가 핵심이다.
- "조회 화면이 복잡해졌는데 일단 repository 메서드만 더 늘리면 안 되나요?"
  - 화면 요구가 중심이면 repository보다 query model 쪽 문서를 먼저 보는 편이 덜 꼬인다.
- "무조건 `Repository Interface Contract Primer`부터 순서대로 다 읽어야 하나요?"
  - 아니다. 이 가이드는 순차 완독표가 아니라 다음 문서 1개를 빠르게 고르는 표다. 이미 누수가 보이면 바로 `Persistence Model Leakage Anti-Patterns`로 가도 된다.

## 초심자용 가장 안전한 읽기 순서

영속성 감이 거의 없으면 아래 순서가 가장 무난하다.

1. [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
2. [Repository, DAO, Entity](./repository-dao-entity.md)
3. [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
4. [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)

중간에 이런 질문이 생기면 옆으로 새면 된다.

- 이름이 이상하면: [Repository Naming Smells Primer](./repository-naming-smells-primer.md)
- 목록/검색이 커지면: [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md)
- `cascade`/양방향이 규칙처럼 보이면: [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md)
- API 응답과 서비스 코드에 `Entity`가 보이면: [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)

한 줄 기준:

- 계약이 막히면 `Repository Interface`
- 책임 이름이 막히면 `Naming Smells`
- 읽기 분리가 막히면 `DAO vs Query Model`
- 매핑이 막히면 `Mapping Checklist`
- ORM 누수가 보이면 `Leakage Anti-Patterns`

## 한 줄 정리

처음 영속성 문서를 읽다가 막히면 용어를 더 외우기보다, "지금 막힌 질문이 저장 계약인지, 이름 냄새인지, 읽기 분리인지, JPA 매핑인지, ORM 누수인지"를 먼저 골라 다음 문서를 정하면 훨씬 빠르다.
