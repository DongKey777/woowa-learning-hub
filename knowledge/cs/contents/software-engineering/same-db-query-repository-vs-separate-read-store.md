# Same-DB Query Repository Vs Separate Read Store

> 한 줄 요약: 초심자는 보통 `같은 DB 위 query repository`에서 멈추는 편이 안전하다. 별도 read store는 "쿼리가 좀 길다"가 아니라, 읽기 부하·저장 형식·운영 격리·지연 허용이 함께 분명할 때만 올라가는 다음 단계다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 떠올릴 사다리](#먼저-떠올릴-사다리)
- [1단계: 같은 DB query repository로 충분한 경우](#1단계-같은-db-query-repository로-충분한-경우)
- [JPQL로 충분한 경우 vs native query를 따로 볼 경우](#jpql로-충분한-경우-vs-native-query를-따로-볼-경우)
- [2단계: 같은 DB 안 projection/view를 추가하는 경우](#2단계-같은-db-안-projectionview를-추가하는-경우)
- [3단계: 진짜 separate read store가 필요한 경우](#3단계-진짜-separate-read-store가-필요한-경우)
- [아직 뛰지 말아야 하는 신호](#아직-뛰지-말아야-하는-신호)
- [예시: 관리자 주문 검색이 커질 때](#예시-관리자-주문-검색이-커질-때)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

관련 문서:

- [Software Engineering README: Same-DB Query Repository Vs Separate Read Store](./README.md#same-db-query-repository-vs-separate-read-store)
- [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
- [Bulk Helper Ports vs Query Model Separation](./bulk-helper-ports-vs-query-model-separation.md)
- [Helper Snapshot Bloat Vs Response DTO Separation](./helper-snapshot-bloat-vs-response-dto-separation.md)
- [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)
- [Event Sourcing, CQRS Adoption Criteria](./event-sourcing-cqrs-adoption-criteria.md)
- [Spring Testcontainers Boundary Strategy](../spring/spring-testcontainers-boundary-strategy.md)

retrieval-anchor-keywords: same db query repository, separate read store, same database read model, query repository vs separate read database, cqrs lite escalation ladder, query repository first, same db projection table, materialized view beginner, read model separation same database, separate read store criteria, jpql vs native query beginner, native query 분리 기준, read replica vs read model, jpql enough when, projection lag tradeoff

## 왜 이 문서가 필요한가

초심자는 CQRS 이야기를 들으면 종종 이렇게 건너뛴다.

- "query repository를 만들었으니 다음은 read DB 분리겠네"
- "목록 쿼리가 길어졌으니 이제 별도 저장소가 필요하겠네"

하지만 안전한 질문은 다르다.

- 지금 필요한 것은 **읽기 경로 분리**인가?
- 아니면 **읽기용 데이터 모양 분리**인가?
- 아니면 정말로 **저장소 자체 분리**인가?

이 셋은 복잡도가 다르다.

- query repository는 **쿼리 경로만 분리**한다
- projection/view는 **읽기용 데이터 모양을 분리**한다
- separate read store는 **저장소와 동기화 운영까지 분리**한다

즉 "같은 DB 위 query repository"와 "진짜 separate read store" 사이에는 안전한 중간 단계가 있다.

## 먼저 떠올릴 사다리

아래 표를 먼저 보면 전체 그림이 잡힌다.

| 단계 | 무엇이 달라지나 | 보통 여기서 멈춰도 되는 이유 | 다음 단계로 가는 신호 |
|---|---|---|---|
| 1. 같은 DB query repository | `OrderQueryRepository`가 write table을 projection으로 읽는다 | 저장소는 그대로 두고 읽기 경로만 분리해도 대부분의 CRUD 화면 문제가 줄어든다 | join/aggregation 비용이 계속 커지고 읽기용 컬럼 모양이 자주 바뀐다 |
| 2. 같은 DB projection/view | 같은 DB 안에 read table, SQL view, materialized view 같은 읽기 전용 모양을 둔다 | 운영 경계는 하나로 유지하면서도 목록/검색 성능과 쿼리 단순화를 얻을 수 있다 | write DB와 read workload의 인덱스, 트래픽, 저장 형식 요구가 충돌한다 |
| 3. separate read store | 다른 DB나 검색 엔진에 projection을 복제한다 | 읽기 부하 격리, 다른 검색 기능, 다른 저장 비용 구조를 얻는다 | 이 단계가 끝 단계다. 대신 lag, rebuild, dual schema 운영을 감당해야 한다 |

짧게 외우면 이렇다.

- **경로만 분리**할 거면 query repository
- **모양도 분리**할 거면 같은 DB projection
- **저장소까지 분리**할 거면 separate read store

## 1단계: 같은 DB query repository로 충분한 경우

이 단계는 초심자에게 가장 안전한 기본값이다.

```java
public interface OrderQueryRepository {
    Page<OrderSummaryView> findSummaries(OrderSearchCondition condition, Pageable pageable);
    Optional<OrderDetailView> findDetail(OrderId id);
}
```

핵심은 저장소를 바꾸지 않고 읽기 책임만 분리하는 것이다.

- write repository는 aggregate 저장/복원 책임을 유지한다
- query repository는 목록/상세/search projection만 다룬다
- 같은 DB, 같은 트랜잭션 환경을 그대로 쓸 수 있다

아래 상황이면 이 단계에서 멈춰도 된다.

| 신호 | 왜 아직 충분한가 |
|---|---|
| 관리자 목록, 검색, 상세가 늘어났다 | 읽기 경로 분리만으로도 write model 비대화를 막을 수 있다 |
| 쿼리가 조금 복잡하지만 DB 압박은 측정되지 않았다 | "길다"는 이유만으로 저장소를 늘릴 필요는 없다 |
| 읽고 바로 수정하는 화면이 많다 | 같은 DB가 read-after-write 기대를 맞추기 쉽다 |
| 팀이 query model, response DTO, aggregate 경계부터 정리 중이다 | 운영 복잡도보다 경계 분리가 먼저다 |

즉 첫 번째 질문은 보통 "DB를 더 만들까?"가 아니라 "읽기 화면 책임을 write model에서 떼어낼까?"다.

## JPQL로 충분한 경우 vs native query를 따로 볼 경우

초심자는 `@Query`가 길어지기 시작하면 곧바로 "native query로 갈아타야 하나?"부터 떠올리기 쉽다.
하지만 먼저 나눠야 하는 것은 **읽기 저장소 분리**가 아니라 **쿼리 표현식 선택**이다.

| 질문 | JPQL로 충분한 경우 | native query를 따로 볼 경우 |
|---|---|---|
| 지금 풀려는 문제 | 엔티티 관계를 따라 목록/상세 projection을 읽는다 | DB 전용 함수, CTE, window function, JSON/배열 타입처럼 SQL 엔진 기능이 핵심이다 |
| 초심자에게 쉬운 이유 | 엔티티/연관관계 언어로 읽혀서 write model과 연결이 보인다 | SQL이 실행 계획과 DB 문법에 더 직접 맞닿아 있다 |
| 보통 두는 자리 | 같은 `OrderQueryRepository` 안 JPQL projection | `OrderNativeQueryRepository` 같은 읽기 전용 구현이나 adapter |
| 테스트 기본값 | H2 또는 `@DataJpaTest`로 1차 확인 가능성이 높다 | 실제 DB(Testcontainers)를 먼저 떠올리는 편이 안전하다 |
| 분리 신호 | join이 조금 늘어도 엔티티 경계 설명이 된다 | "JPQL이 불편하다"가 아니라 "이 기능은 DB 문법 없이는 표현이 안 된다"가 명확하다 |

짧게 말하면 이렇다.

- **JPQL이 길다**는 이유만으로 저장소를 늘리거나 native query로 점프하지 않는다.
- **DB 전용 기능이 핵심**일 때만 native query를 읽기 전용 경계에 가둬 둔다.

예를 들어 관리자 주문 목록에서 회원명, 주문금액 합계, 상태 필터 정도를 읽는다면 보통 JPQL projection으로 충분하다.
반면 PostgreSQL `jsonb`, `date_trunc`, window function으로 랭킹/집계를 계산해야 한다면 native query 쪽이 더 자연스럽다.

## 2단계: 같은 DB 안 projection/view를 추가하는 경우

많은 팀이 이 중간 단계를 건너뛰지만, 초심자에게는 꽤 안전한 다음 단계다.

예를 들면 이런 모양이다.

- `order_summary_projection` 같은 읽기 전용 테이블
- 자주 쓰는 join을 감춘 SQL view
- 주기적으로 갱신하는 materialized view

이 단계는 "DB를 나누자"가 아니라 "읽기용 데이터 모양을 DB 안에서 먼저 고정하자"에 가깝다.

| 이 단계가 잘 맞는 상황 | 이유 |
|---|---|
| 목록 쿼리가 항상 같은 join과 aggregate를 반복한다 | projection 한 번으로 쿼리를 단순하게 만들 수 있다 |
| read path는 커졌지만 여전히 관계형 조회로 충분하다 | 검색 엔진까지 갈 이유는 없다 |
| 읽기 쿼리 전용 인덱스가 필요하다 | 같은 DB 안에서도 read table/view로 해결할 수 있다 |
| 운영팀이 아직 cross-store sync를 원하지 않는다 | backup, auth, 장애 복구 경계를 하나로 유지한다 |

이 단계가 separate read store보다 안전한 이유는 다음과 같다.

- 저장소 수가 늘지 않는다
- 백업, 권한, 모니터링 체계가 크게 늘지 않는다
- projection 재구성 범위가 상대적으로 작다
- read-after-write 요구가 강하면 같은 DB 안에서 더 다루기 쉽다

즉 읽기용 모양이 필요하다고 해서 곧바로 별도 저장소로 갈 필요는 없다.

## 3단계: 진짜 separate read store가 필요한 경우

이 단계는 "쿼리 분리"보다 훨씬 큰 결정이다.

- 다른 PostgreSQL read DB
- Elasticsearch 같은 검색 엔진
- 분석용 warehouse
- 캐시가 아니라 재구성 가능한 read model 저장소

보통 아래 신호가 여러 개 겹칠 때만 검토한다.

| 신호 | 왜 separate read store 신호인가 |
|---|---|
| 읽기 트래픽이 write DB를 실제로 압박한다 | query path 분리만으로는 부하 격리가 안 된다 |
| 전문 검색, faceting, autocomplete, geo query가 필요하다 | 저장 형식과 인덱스 전략이 write DB와 달라진다 |
| 읽기 데이터 보존 기간이나 압축 방식이 write DB와 다르다 | 저장 비용 최적화 축이 갈라진다 |
| 서비스/리전별로 읽기 확장 전략이 따로 필요하다 | 운영상 분리 가치가 커진다 |
| 팀이 lag 모니터링, backfill, rebuild, replay를 운영할 준비가 되어 있다 | 별도 read store는 "동기화 시스템"까지 함께 운영하는 일이다 |

반대로 이 단계에 올라가면 새로 생기는 책임도 분명하다.

| 새 책임 | 설명 |
|---|---|
| projection lag 관리 | 쓰기 성공 직후 읽기 결과가 늦게 보일 수 있다 |
| rebuild/backfill | read store를 다시 채우는 절차가 필요하다 |
| dual schema 관리 | write schema와 read schema를 둘 다 버전 관리해야 한다 |
| 동기화 장애 대응 | 이벤트 누락, 소비 지연, 재처리 실패를 운영해야 한다 |

그래서 "성능이 조금 불안하다" 수준이면 아직 1단계나 2단계가 더 안전한 경우가 많다.

## 아직 뛰지 말아야 하는 신호

아래 상황이면 separate read store로 점프하지 않는 편이 낫다.

| 상황 | 왜 아직 이르나 |
|---|---|
| 문제 설명이 "JPQL이 보기 싫다" 수준이다 | 코드 미감 문제와 저장소 분리는 다른 문제다 |
| 병목 측정 없이 "나중에 커질 것 같아서"만 말한다 | 운영 복잡도는 현재 비용이다 |
| 강한 read-after-write가 핵심 UX다 | lag를 설명하거나 우회하지 못하면 오히려 제품이 나빠진다 |
| schema와 화면 요구가 매주 크게 바뀐다 | read store projection 계약도 같이 흔들린다 |
| outbox/CDC/rebuild 절차가 없다 | 동기화 실패 때 복구 수단이 없다 |
| ownership이 불명확하다 | write/store/read 파이프라인 장애가 서로 미뤄지기 쉽다 |

짧게 말하면, **separate read store는 쿼리 최적화 기술이 아니라 운영 모델 변화**다.

## 예시: 관리자 주문 검색이 커질 때

같은 주문 관리자 화면이라도 단계별로 멈출 지점이 다르다.

### 단계 1. 같은 DB query repository

- 조건: 상태, 기간, 결제수단 필터가 있는 주문 목록이 생겼다
- 선택: `OrderQueryRepository`에서 join + projection으로 목록을 읽는다
- 이유: write aggregate를 억지로 목록 DTO로 만들지 않아도 된다

이 시점의 핵심은 "읽기 경로 분리"다.

### 단계 2. 같은 DB projection/view

- 조건: `order`, `order_line`, `member`, `payment`를 매번 join하면서 item count와 total price를 계산한다
- 선택: 같은 DB에 `order_summary_projection`을 두고 query repository가 그 테이블만 읽는다
- 이유: 목록 쿼리가 단순해지고, read 인덱스를 write table에 억지로 섞지 않아도 된다

이 시점의 핵심은 "읽기용 모양 고정"이다.

### 단계 3. separate read store

- 조건: 관리자 검색이 상품명 autocomplete, 복합 facet, 대량 트래픽, 지역별 read scale을 요구한다
- 선택: 검색 전용 read store로 projection을 보낸다
- 이유: 이제는 관계형 projection보다 검색 엔진/별도 read DB의 장점이 실제 비용을 이긴다

이 시점의 핵심은 "저장소 특성 차이"다.

즉 같은 화면이라도 보통은 1단계나 2단계에서 꽤 오래 버틴다.
초심자가 바로 3단계로 가야 하는 경우는 생각보다 드물다.

## 자주 하는 오해

### "CQRS면 무조건 DB도 둘이어야 하나요?"

아니다.
CQRS-lite는 같은 DB 위 query repository만으로도 충분히 시작할 수 있다.

### "read replica를 붙이면 separate read store가 된 건가요?"

아니다.
read replica는 보통 **같은 schema를 물리적으로 복제한 읽기 확장 수단**이다.
별도 read model/store는 보통 **읽기용 schema와 projection 운영**까지 함께 가진다.

### "query repository가 생기면 곧 separate read store로 가야 하나요?"

아니다.
많은 서비스는 같은 DB query repository나 같은 DB projection 단계에서 오래 머문다.

### "별도 read store가 있으면 조회 문제는 다 해결되나요?"

아니다.
오히려 lag, 동기화 실패, 재구성 비용, 운영 ownership 문제가 새로 생긴다.

## 한 줄 정리

- 초심자의 기본값은 보통 **같은 DB query repository**다.
- query repository 다음의 안전한 중간 단계는 **같은 DB projection/view**다.
- **separate read store는 저장소 분리뿐 아니라 동기화 운영까지 도입하는 일**이다.
- **JPQL이 길다**는 이유만으로 native query나 별도 저장소로 점프하지 않는다.
- "쿼리가 복잡하다"보다 "읽기 부하, 저장 형식, 운영 격리, lag 허용"이 더 강한 근거다.
- jump 기준이 흐리면 먼저 1단계나 2단계에서 멈추는 편이 안전하다.
