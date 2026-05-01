# DAO vs Query Model Entrypoint

> 한 줄 요약: 처음 배우는데 헷갈리면 이렇게 보면 된다. "정해진 테이블 데이터를 읽고 쓰는 일"이면 DAO로 충분하고, "목록·검색·대시보드처럼 읽기 화면 자체가 별도 책임"이면 dedicated query repository/read model이 더 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Software Engineering README: DAO vs Query Model Entrypoint](./README.md#dao-vs-query-model-entrypoint)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
- [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md)
- [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
- [Spring Data vs Domain Repository Bridge](../spring/spring-data-vs-domain-repository-bridge.md)

retrieval-anchor-keywords: dao vs query model, dao enough, dedicated query repository, read model beginner, query repository 언제 쓰는지, dao로 충분한 경우, dao 뭐예요, query model 뭐예요, dao와 repository 차이, dao랑 query repository 차이, 처음 read model 헷갈림, list search dashboard query model, same db read model, 목록 조회 때문에 dao가 커져요, query model separation basics
retrieval-anchor-keywords: what does a query service mean, query service meaning beginner, query service란, query service가 뭐예요, query service vs dao, query service vs query repository, read service entrypoint, query model entrypoint beginner

## 핵심 개념

큰 그림부터 잡으면 이 문서는 "읽기 경로를 어디서 끊을까?"에 답한다.

- **DAO**는 테이블이나 SQL 관점의 출입구다.
- **query repository/read model**은 목록, 검색, 상세, 대시보드 같은 읽기 화면 관점의 출입구다.

처음 CRUD를 만들 때는 DAO 하나로도 충분해 보인다. 실제로도 단건 조회, 저장, 간단한 수정은 DAO만으로 끝나는 경우가 많다.

하지만 읽기 요구가 커지면 질문이 바뀐다.

- "주문을 저장/조회할까?"가 아니라
- "관리자 목록에 어떤 컬럼을 어떤 정렬로 얼마나 빨리 보여줄까?"가 된다.

이때는 DAO를 더 키우기보다, 읽기 전용 entrypoint를 따로 두는 편이 덜 헷갈린다.

## 한눈에 보기

| 질문 | DAO로 충분한 쪽 | dedicated query repository/read model 쪽 |
|---|---|---|
| 시작 질문 | "이 테이블 row를 읽고 쓰나?" | "이 화면/검색 결과를 어떻게 읽나?" |
| 입력 모양 | id, 고정 key, 단순 조건 | 검색 조건, 정렬, 페이지, 집계 기준 |
| 반환 모양 | row/entity/snapshot | summary view, detail view, page/view model |
| 잘 맞는 예 | 회원 1건 조회, 주문 상태 업데이트 | 관리자 목록, 복합 검색, 대시보드 |
| 바뀌는 이유 | 테이블 구조, 저장 로직 | 화면 요구, 읽기 성능, 조회 UX |

짧게 외우면 이렇다.

- **정해진 대상을 읽고 쓴다**면 DAO
- **무엇을 보여줄지부터 읽기가 결정한다**면 query model

## 언제 DAO면 충분한가

아래 상황이면 별도 query repository를 급히 만들 필요가 없다.

| 신호 | 왜 DAO로도 충분한가 |
|---|---|
| 단건 조회/저장이 대부분이다 | 읽기 경로가 독립 제품이 아니다 |
| 입력이 `id`나 고정 key 중심이다 | 어떤 대상을 읽을지 이미 정해져 있다 |
| 목록이 있어도 필터·정렬·집계가 단순하다 | 화면 요구가 아직 write/read 경계를 흔들지 않는다 |
| 읽고 바로 수정하는 흐름이 많다 | 같은 저장 경로에서 이해하는 편이 더 단순하다 |
| 팀이 아직 DTO, repository, entity 경계부터 정리 중이다 | read model 분리보다 기본 경계 정리가 먼저다 |

예를 들면 이런 경우다.

- `UserDao.findById(id)`
- `OrderDao.updateStatus(orderId, status)`
- `CouponDao.findExpiredCoupons(today)`

이 단계에서는 DAO가 나쁜 게 아니다. 문제보다 추상화가 더 크면 오히려 초심자에게 잡음이 된다.

## 언제 dedicated query repository/read model이 더 낫나

아래 신호가 2개 이상 겹치면 query model entrypoint를 검토할 시점이다.

| 신호 | 왜 DAO보다 query model이 낫나 |
|---|---|
| 목록, 상세, 검색이 서로 다른 필드 묶음을 원한다 | row 중심 DAO 하나로는 화면별 의도가 흐려진다 |
| pagination, sorting, filtering이 핵심이다 | 읽기 경로가 lookup이 아니라 search 제품이 된다 |
| 합계, 건수, 상태 라벨 같은 projection이 자주 붙는다 | 테이블 row보다 화면용 읽기 모델이 더 자연스럽다 |
| DAO 메서드가 `findForAdminList`, `findForDashboard`, `findEverything`처럼 늘어난다 | 읽기 책임이 DAO 안에서 비대해지고 있다 |
| read-heavy 경로라 성능과 join 전략이 자주 논의된다 | 읽기 최적화 전용 경계가 있어야 변경 이유가 선명하다 |

이때의 핵심은 "DAO를 버린다"가 아니다.

- command/write 쪽은 기존 repository/DAO를 유지하고
- read-heavy 경로만 `OrderQueryRepository`, `OrderSummaryView`처럼 분리한다

처음에는 같은 DB 위 CQRS-lite로 시작해도 충분하다.

## 흔한 오해와 함정

- "조회가 있으니 전부 query repository로 가야 하나요?"
  아니다. 단건 lookup과 단순 저장 흐름까지 모두 read model로 올리면 구조만 커진다.

- "DAO를 쓰면 설계가 뒤처진 건가요?"
  아니다. 문제 크기에 맞는 entrypoint면 충분하다. 작은 CRUD에 DAO는 정상적인 선택이다.

- "query model을 만들면 곧바로 다른 DB가 필요한가요?"
  아니다. 처음엔 같은 DB 위 projection/query repository로 시작하는 경우가 훨씬 많다.

- "DAO 메서드가 많아지면 무조건 나쁜가요?"
  메서드 수 자체보다 이유가 중요하다. 테이블 접근이 늘어난 것인지, 화면별 조회 요구가 DAO 안에 숨어든 것인지 봐야 한다.

## 실무에서 쓰는 모습

주문 관리 기능을 예로 들면 구분이 쉽다.

### 1. DAO로 충분한 시점

- 주문 1건 조회
- 주문 상태 변경
- 만료 주문 배치 조회

이때는 `OrderDao`가 `findById`, `updateStatus`, `findExpiredOrders`를 가져도 크게 문제 없다.

### 2. query model이 필요한 시점

이후 관리자 화면이 커진다.

- 기간, 상태, 결제수단으로 주문 목록 검색
- 주문별 총액, 상품 수, 고객명 표시
- 페이지네이션과 정렬 필요

여기서 DAO를 계속 키우면 결국 테이블 접근 코드 안에 화면 요구가 들어간다.

더 안전한 다음 단계는 이런 모양이다.

```java
public interface OrderQueryRepository {
    Page<OrderSummaryView> findSummaries(OrderSearchCondition condition, Pageable pageable);
    Optional<OrderDetailView> findDetail(Long orderId);
}
```

이 entrypoint는 "어떤 주문 row를 읽나?"보다 "이 화면이 어떤 읽기 결과를 원하나?"에 답한다.

## 더 깊이 가려면

- DAO, repository, entity 역할 자체를 다시 잡고 싶다면: [Repository, DAO, Entity](./repository-dao-entity.md)
- read-heavy API에서 query model 분리 기준을 더 자세히 보려면: [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
- 같은 DB query repository에서 멈출지, 별도 read store로 갈지 보려면: [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md)
- Spring Data repository와 도메인 repository 이름 충돌이 헷갈리면: [Spring Data vs Domain Repository Bridge](../spring/spring-data-vs-domain-repository-bridge.md)

## 다음 읽기

아직 "`DAO로 충분한가`, `query model까지 가야 하나`"가 바로 안 서면 한 번에 deep dive로 내려가지 말고 아래 한 칸씩만 이동하면 된다.

| 지금 남은 질문 | 다음 문서 | 그다음 안전한 한 걸음 |
|---|---|---|
| "`Repository`, `DAO`, `Entity` 말이 아직 한 덩어리다" | [Repository, DAO, Entity](./repository-dao-entity.md) | [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md) |
| "목록/검색이 커질 때 query repository를 어디까지 분리하나?" | [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md) | [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md) |
| "query model을 쓰더라도 같은 DB면 충분한가?" | [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md) | [Event Sourcing, CQRS Adoption Criteria](./event-sourcing-cqrs-adoption-criteria.md) |
| "Spring Data interface와 도메인 repository 이름이 왜 다르지?" | [Spring Data vs Domain Repository Bridge](../spring/spring-data-vs-domain-repository-bridge.md) | [Repository Interface Contract Primer](./repository-interface-contract-primer.md) |

길을 잃으면 persistence primer 묶음으로 돌아와 다음 한 칸만 다시 고르면 된다: [Software Engineering README](./README.md#dao-vs-query-model-entrypoint)

## 한 줄 정리

처음 배우는데 entrypoint 선택이 헷갈리면, **정해진 대상을 읽고 쓰는 일은 DAO, 읽기 화면 자체를 설계하는 일은 dedicated query repository/read model**이라고 기억하면 큰 그림이 잘 잡힌다.
