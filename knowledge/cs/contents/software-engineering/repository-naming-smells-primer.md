# Repository Naming Smells Primer

> 한 줄 요약: 처음 배우는데 `Repository` 메서드 이름이 헷갈리면, "무엇을 저장/조회하나"를 도메인 말투로 말하면 repository 계약에 가깝고, "어느 테이블을 어떤 SQL로 건드리나"가 이름에 드러나면 DAO/API 냄새일 가능성이 크다.

**난이도: 🟢 Beginner**

관련 문서:

- [Software Engineering README: Repository Naming Smells Primer](./README.md#repository-naming-smells-primer)
- [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)
- [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md)
- [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md)
- [Spring Data Repository vs Domain Repository Bridge](../spring/spring-data-vs-domain-repository-bridge.md)

retrieval-anchor-keywords: repository naming smells, repository method naming, repository vs dao naming, domain language repository contract, sql shaped dao api, repository method names beginner, repository 메서드 이름, repository 네이밍 냄새, dao 메서드 이름, repository 메서드 이름 왜 save find 인가요, repository 이름 처음 헷갈려요, repository와 dao 이름 차이 뭐예요, 언제 repository 말투를 쓰나요, insert select update가 왜 dao 같아요, query model 이름까지 섞여서 헷갈려요

처음 배우는데 `OrderRepository` 안에 `insertOrderRow`, `selectOrdersJoinMember`, `updateOrderTableStatus` 같은 이름이 보이면 "이게 repository가 맞나?"라는 감각이 드는 편이 정상이다. 이 문서는 **"repository 메서드 이름이 왜 `save/find` 말투인지", "언제 DAO 말투로 보는지"** 같은 첫 질문이 들어왔을 때 먼저 도착해야 하는 1페이지 primer다.

## 큰 그림 먼저

초심자용으로는 이렇게 보면 가장 덜 헷갈린다.

- **repository 계약**은 "도메인이 무엇을 원하나"를 말한다.
- **DAO/API 이름**은 "DB를 어떻게 건드리나"를 말한다.

짧게 외우면 이렇다.

- `OrderRepository.save(order)`는 "주문을 저장한다"는 약속에 가깝다.
- `OrderDao.insertOrderRow(orderRow)`는 "orders row를 insert한다"는 구현 세부에 가깝다.

즉 메서드 이름이 **비즈니스 대상과 의도**를 먼저 말하면 repository 쪽, **테이블/SQL 동작**을 먼저 말하면 DAO 쪽일 가능성이 크다.

## 30초 판별표

| 이름에서 먼저 보이는 것 | repository 계약에 가까운 신호 | DAO/API 냄새 신호 |
|---|---|---|
| 대상 | `Order`, `Coupon`, `Inventory` 같은 도메인 개념 | `order_row`, `orders_table`, `tb_order` 같은 테이블 개념 |
| 동사 | `save`, `find`, `load`, `remove`, `exists` | `insert`, `select`, `update`, `delete`, `join`, `upsert` |
| 조건 표현 | `OrderId`, `OrderNumber`, `status` 같은 업무 조건 | `created_at_desc_limit_100`, `leftJoinMember`, `groupByDate` 같은 SQL 모양 |
| 반환 의도 | `Order`, `Optional<Order>`, `OrderSummaryView` | `OrderRow`, `ResultSet`, `Tuple`, `Map<String, Object>` |
| 읽는 사람이 받는 느낌 | "무엇을 하고 싶은지"가 먼저 보인다 | "DB에 어떻게 접근하는지"가 먼저 보인다 |

## 메서드 이름을 볼 때 하는 3질문

처음 배우는데 이름 판별이 막히면 아래 3질문만 먼저 본다.

1. 이 이름은 **업무 대상을 말하나**, 아니면 **테이블/컬럼을 말하나**?
2. 이 이름은 **원하는 결과를 말하나**, 아니면 **SQL 동작 자체를 말하나**?
3. 이 이름을 서비스 코드가 읽을 때 **비즈니스 문장처럼 읽히나**, 아니면 **쿼리 문장처럼 읽히나**?

`YES`가 repository 쪽에 2개 이상이면 domain-language 계약에 가깝고, DAO 쪽에 2개 이상이면 table/SQL-shaped API일 가능성이 높다.

## 예시로 바로 구분하기

### repository 계약처럼 읽히는 이름

```java
public interface OrderRepository {
    Optional<Order> findById(OrderId orderId);
    Optional<Order> findByOrderNumber(OrderNumber orderNumber);
    Order save(Order order);
    boolean existsByOrderNumber(OrderNumber orderNumber);
    void delete(Order order);
}
```

이 이름들은 공통적으로 다음을 지킨다.

- `Order`라는 도메인 대상을 중심에 둔다
- 저장/조회 계약만 말한다
- 내부 SQL, join, row 모양이 이름에 새어 나오지 않는다

### DAO/API처럼 읽히는 이름

```java
public interface OrderDao {
    void insertOrderRow(OrderRow row);
    List<OrderRow> selectOrdersByStatusOrderByCreatedAtDesc(String status);
    int updateOrderTableStatus(long orderPk, String status);
    List<OrderMemberJoinRow> selectOrderJoinMemberRows(long memberPk);
}
```

이 이름들은 나쁘다기보다 **다른 경계**를 말한다.

- `row`, `table`, `join`이 이름에 직접 보인다
- SQL/테이블 작업 방식이 메서드 표면에 드러난다
- 서비스 코드가 읽으면 비즈니스 문장보다 DB 조작 문장처럼 느껴진다

## 처음 많이 헷갈리는 경우

### 1. `findBy...`라고 시작하면 다 repository인가요?

아니다. `findBy` 하나만으로는 부족하다.

- `findById(OrderId id)`는 repository 계약처럼 읽힌다
- `findByCreatedAtBetweenOrderByIdDescLimit100(...)`는 query API/DAO 냄새가 강하다

핵심은 `findBy`가 아니라, **그 뒤에 무엇이 붙느냐**다.

### 2. `insert/update/delete`를 쓰면 무조건 DAO인가요?

대개는 DAO/API 말투에 더 가깝다.
repository는 보통 "도메인 대상을 저장/삭제한다"는 쪽으로 읽히게 `save`, `delete`, `remove` 같은 표현을 쓴다.

즉 초심자 기준에서는 이렇게 기억하면 된다.

- `save(order)`는 도메인 계약 말투
- `insertOrderRow(row)`는 SQL 작업 말투

### 3. Spring Data JPA query method는 이름이 길어도 repository 아닌가요?

여기서 많이 섞인다.

- `SpringDataOrderJpaRepository extends JpaRepository<...>` 안의 긴 query method는 **프레임워크 adapter 내부 도구**일 수 있다
- 하지만 domain/application이 의존하는 `OrderRepository` 표면까지 그 긴 이름이 그대로 올라오면 **도메인 계약이 SQL 말투로 오염**되기 쉽다

즉 beginner 눈높이에서는 이렇게 자르면 된다.

- adapter 내부 Spring Data 메서드: 길 수 있다
- 바깥 domain repository 계약: 가능한 한 도메인 문장으로 유지한다

## 이름이 보내는 설계 신호

| 메서드 이름 | 읽히는 신호 | 더 자연스러운 위치 |
|---|---|---|
| `save(order)` | aggregate 저장 계약 | domain repository |
| `findByOrderNumber(orderNumber)` | 업무 식별자 조회 계약 | domain repository |
| `insertOrderRow(row)` | row insert 작업 | DAO/adapter |
| `selectOrderJoinMemberRows(...)` | join 결과 조회 | DAO/query adapter |
| `findDashboardDataByPeriodAndStatus(...)` | 화면/검색 읽기 책임 | query repository/read model |

여기서 중요한 점은 "DAO는 나쁘다"가 아니다.

- DAO는 테이블/SQL 작업을 드러내는 데 적합하다
- repository는 도메인 계약을 드러내는 데 적합하다
- 대시보드/목록/검색은 query repository/read model이 더 적합한 경우가 많다

즉 **이름이 어떤 책임을 드러내야 하는지**에 따라 자리가 갈린다.

## 빠른 before/after

### before

```java
public interface OrderRepository {
    void insertOrder(OrderEntity entity);
    List<OrderEntity> selectOrdersByMemberId(long memberId);
    int updateOrderStatus(long orderId, String status);
}
```

처음 배우는데 이 이름들은 repository보다 DAO처럼 읽힌다.

- `Entity`, `select`, `update`가 표면에 보인다
- 서비스 코드가 주문 도메인보다 DB 작업을 더 많이 알게 된다

### after

```java
public interface OrderRepository {
    Order save(Order order);
    List<Order> findByMemberId(MemberId memberId);
    Optional<Order> findById(OrderId orderId);
}
```

이렇게 바꾸면 최소한 계약 표면은 더 도메인 말투로 읽힌다.

만약 정말 "주문 목록 검색"이 핵심이면 repository를 억지로 늘리기보다 이렇게 분리하는 편이 낫다.

```java
public interface OrderQueryRepository {
    List<OrderSummaryView> search(OrderSearchCondition condition);
}
```

## 자주 보이는 냄새 체크리스트

- 메서드 이름에 `table`, `row`, `entity`, `join`, `select`, `insert`, `update`가 반복된다
- 메서드 이름이 업무 문장보다 SQL 문장처럼 읽힌다
- `OrderRepository`인데 반환 타입이 `OrderRow`, `Tuple`, `Map<String, Object>` 위주다
- 같은 인터페이스에 `save(order)`와 `selectOrderJoinDashboardRows(...)`가 같이 있다
- 이름이 점점 `findForAdminList`, `findForDashboard`, `findEverything`처럼 화면별로 늘어난다

2개 이상 보이면 "repository 계약, DAO, query model이 섞였나?"를 의심해 볼 가치가 있다.

## 한 줄 정리

처음 배우는데 메서드 이름이 헷갈리면, **repository는 도메인이 원하는 저장/조회 문장, DAO는 테이블/SQL 작업 문장**이라는 큰 그림부터 잡으면 판단 속도가 훨씬 빨라진다.
