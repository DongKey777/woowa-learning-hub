# Repository, DAO, Entity

> 한 줄 요약: 같은 주문 생성 예시로 보면 `Repository`는 "주문을 저장해 달라"는 창구이고, `DAO`는 SQL 실행 도구, `Entity`는 DB에 맞춘 저장 모양이다.

**난이도: 🟢 Beginner**

관련 문서:
- [Software Engineering README: Repository, DAO, Entity](./README.md#repository-dao-entity)
- [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
- [Controller / Service / Repository after 예시 - 주문 생성 흐름을 Controller Service Repository로 나눈 상태](./layered-architecture-basics.md#after-주문-생성-흐름을-controller-service-repository로-나눈-상태)
- [Service 계층 기초](./service-layer-basics.md)
- [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
- [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)
- [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md)
- [Repository Naming Smells Primer](./repository-naming-smells-primer.md)
- [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)
- [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- [Module API DTO Patterns](./module-api-dto-patterns.md)
- [Record and Value Object Equality](../language/java/record-value-object-equality-basics.md)
- [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md)

retrieval-anchor-keywords: repository dao entity beginner, repository dao entity 차이, 주문 생성 repository dao entity, repository는 뭐예요, dao는 뭐예요, entity는 뭐예요, repository dao entity 뭐가 달라요, service가 dao를 바로 알아도 되나요, entity 저장 모양, entity를 dto로 써도 되나요, repository와 query model 차이, dao와 query model 차이, persistence mental model, 왜 repository가 dao 위에 있어요, what is repository entity

처음에는 용어 뜻을 길게 외우기보다, **"주문 생성 흐름에서 누가 무엇을 맡는지"**만 구분하면 된다. 이 문서는 [계층형 아키텍처 기초](./layered-architecture-basics.md)의 같은 주문 생성 시나리오를 저장 책임 쪽으로 한 칸 더 내려서 연결하고, 더 큰 설계 그림이 필요하면 [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)로 다시 올라가면 된다.

## 처음 막힐 때 바로 고르는 질문

초급자가 실제로 많이 하는 말은 정의보다 아래 증상에 가깝다.

| 지금 머리에 떠오르는 말 | 먼저 붙일 이름 | 이 문서에서 바로 볼 자리 | 다음 한 걸음 |
|---|---|---|---|
| "`service`가 `dao`를 바로 알아도 되나요?" | 저장 책임 경계 문제 | [같은 주문 생성 시나리오로 이어 보기](#같은-주문-생성-시나리오로-이어-보기) | [Repository Interface Contract Primer](./repository-interface-contract-primer.md) |
| "`entity`를 DTO처럼 그냥 넘기면 안 돼요?" | 타입 섞임 문제 | [레이어 계약까지 같이 보면](#레이어-계약까지-같이-보면) | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) |
| "`dao`가 너무 많아졌는데 이게 맞나요?" | 읽기/쓰기 모델 분리 문제 | [언제 어디까지 나누면 되나](#언제-어디까지-나누면-되나) | [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md) |
| "`repository`, `dao`, `entity`가 다 저장 아니에요?" | 용어 층위 구분 문제 | [한 표로 먼저 보기](#한-표로-먼저-보기) | 이 문서 끝까지 |

짧게 외우면 이렇다.

- `Repository`는 서비스가 말 거는 저장 창구다.
- `DAO`는 SQL을 실행하는 손발이다.
- `Entity`는 DB에 맞춘 저장 모양이다.

## 먼저 잡는 한 줄 멘탈 모델

서비스는 "주문을 저장해 주세요"라고 부탁하고, 저장 계층 내부는 그 부탁을 **Repository -> DAO -> Entity** 흐름으로 DB 친화적인 모양으로 바꿔 처리한다고 보면 된다.

- `Repository`: 서비스가 보는 저장 창구
- `DAO`: 테이블과 SQL을 다루는 손발
- `Entity`: DB 컬럼에 맞춘 저장 상자
- `Mapper`: 도메인 객체와 저장 상자를 바꾸는 번역기

## 한 표로 먼저 보기

| 용어 | 먼저 떠올릴 질문 | 주로 쓰는 말투 | 작은 기억 문장 |
|---|---|---|---|
| Repository | "이 유스케이스가 무엇을 저장하지?" | 주문, 회원, 결제 같은 도메인 말투 | "주문 저장 창구" |
| DAO | "어떤 SQL을 실행하지?" | `insert`, `select`, `update` 같은 테이블 말투 | "row를 읽고 쓰는 도구" |
| Entity | "DB에 어떤 모양으로 넣지?" | `order_id`, `status` 같은 컬럼 말투 | "저장용 상자" |
| Mapper | "객체를 어디서 바꾸지?" | `toEntity`, `toDomain` 같은 변환 말투 | "번역기" |

초심자는 아래 네 줄만 먼저 잡아도 충분하다.

| 문장 | 더 가까운 대상 |
|---|---|
| `orderRepository.save(order)` | Repository |
| `INSERT INTO orders ...` | DAO |
| `OrderEntity(orderId, status, totalAmount)` | Entity |
| `mapper.toEntity(order)` | Mapper |

## 같은 주문 생성 시나리오로 이어 보기

[계층형 아키텍처 기초](./layered-architecture-basics.md)에서 본 주문 생성 흐름을 저장 책임 기준으로 다시 보면 이렇게 읽힌다.

| 위치 | 같은 예시에서 하는 일 | 이 문서에서 볼 포인트 |
|---|---|---|
| Controller | 요청을 받는다 | 저장 세부를 모른다 |
| Service | 재고 확인 후 `orderRepository.save(order)`를 호출한다 | "무엇을 저장할지"만 말한다 |
| Repository 구현체 | `orderDao.insert(mapper.toEntity(order))` | 저장 기술을 조립한다 |
| DAO | `orders` 테이블에 `INSERT`를 날린다 | SQL과 row 접근을 맡는다 |
| Entity | `order_id`, `status`, `total_amount`를 담는다 | DB 모양에 맞춘다 |

즉 같은 주문 생성 예시라도, 계층 문서에서는 "Controller/Service/Repository를 왜 나누는가"가 중심이고, 여기서는 **Repository 아래에서 저장 책임이 어떻게 더 쪼개지는가**가 중심이다.

## 레이어 계약까지 같이 보면

`Repository`, `DAO`, `Entity`만 따로 외우면 다시 "`그럼 request DTO는 어디까지 가나요?`"가 막히기 쉽다.
같은 주문 생성 장면을 한 줄로 펼치면 아래처럼 읽으면 된다.

| 경계 | 기본 타입 | 이 문서에서 기억할 포인트 |
|---|---|---|
| Controller -> Service | `CreateOrderRequest`, `CreateOrderCommand` | 요청 계약은 저장 계층까지 그대로 들고 가지 않는다 |
| Service -> Repository | `Order` | Service는 저장 기술 대신 도메인 의미로 부탁한다 |
| Repository 구현 -> DAO | `OrderEntity` | 저장 구현체가 DB 친화적인 모양으로 변환한다 |
| DAO -> DB | row, SQL | DAO는 테이블/쿼리 문장에 집중한다 |

짧게 외우면 이렇다.

- request DTO는 웹 계약이다.
- `Order`는 규칙을 가진 도메인 대상이다.
- `OrderEntity`는 저장 모양이다.
- DAO는 그 저장 모양을 SQL로 옮긴다.

즉 `Repository/DAO/Entity` 구분은 persistence 내부 얘기이면서도, 동시에 "`request DTO -> domain -> entity`를 한 타입으로 뭉치지 않는다"는 레이어 계약과 연결된다.

## 작은 주문 저장 코드 예시

```java
public interface OrderRepository {
    void save(Order order);
}

@Component
class JdbcOrderRepository implements OrderRepository {
    private final OrderDao orderDao;
    private final OrderEntityMapper mapper;

    @Override
    public void save(Order order) {
        orderDao.insert(mapper.toEntity(order));
    }
}
```

이 코드에서 초심자가 볼 핵심은 세 가지다.

- `Service`는 `OrderDao` 대신 `OrderRepository`를 의존한다.
- Repository 구현체가 DAO와 Mapper를 조립해 저장 기술 세부를 숨긴다.
- `Entity`는 도메인 의미 전체보다 DB 저장 모양에 더 가깝다.

## 20초 판단표: 지금 이 코드는 어디 말투인가

코드를 읽다 헷갈리면 "이 줄이 누구 말투인가?"만 먼저 보면 된다.

| 코드/문장 신호 | 더 가까운 자리 | 왜 그렇게 보나 |
|---|---|---|
| `save(order)`, `findByMemberId(memberId)` | Repository | 도메인 의미로 저장을 부탁한다 |
| `SELECT * FROM orders`, `insert(...)` | DAO | 테이블과 SQL이 직접 보인다 |
| `OrderEntity(orderId, status)` | Entity | 컬럼 모양에 맞춘 저장 데이터다 |
| `CreateOrderRequest`, `OrderResponse` | DTO | 웹/API 계약 말투다 |

처음에는 완벽히 나누려 하지 말고, `도메인 말투 / SQL 말투 / 저장 모양 / 요청-응답 말투` 네 칸으로만 자르면 충분하다.

## 각 용어를 짧게 풀기

`Repository`는 도메인 언어로 저장을 부탁받는 계약이다. `DAO`는 SQL과 테이블 접근을 직접 담당하는 구현 도구다. `Entity`는 DB에 저장하기 쉬운 납작한 데이터 모양이고, `Mapper`는 도메인 객체와 이 저장 모양을 서로 바꾼다.

그래서 `saveOrder`, `findById`는 Repository 말투에 가깝고, `insertOrderRow`, `selectOrders`는 DAO 말투에 더 가깝다. `@Entity`와 도메인 객체를 같은 것으로 단정하면 헷갈리기 쉬우므로, 저장 편의 모양인지 도메인 규칙 객체인지 먼저 구분하는 편이 안전하다.

## 언제 어디까지 나누면 되나

| 상황 | 시작 구조 | 이유 |
|---|---|---|
| CRUD가 작고 단순하다 | `Repository` 중심 | 흐름 이해가 먼저다 |
| SQL이 길어지고 테이블별 접근이 선명하다 | `Repository + DAO` | 도메인 말투와 SQL 말투를 분리하기 쉽다 |
| 도메인 객체와 DB 모양 차이가 크다 | `Repository + DAO + Entity + Mapper` | 변환 책임을 분리해야 누수를 줄이기 쉽다 |
| 조회 화면 요구가 커진다 | 별도 query model 검토 | 저장 계약과 읽기 화면 요구를 섞지 않기 쉽다 |

작은 프로젝트에서는 보통 `Repository` 하나로 시작해도 충분하다. 구조가 커질수록 DAO, Entity, Mapper를 하나씩 꺼내는 편이 초심자에게 더 자연스럽다.

## 자주 하는 혼동

- "Repository와 DAO는 같은 말 아닌가요?"
  - 둘 다 저장소처럼 보이지만, Repository는 도메인 관점이고 DAO는 테이블/SQL 관점이다.
- "Entity가 곧 도메인 객체 아닌가요?"
  - 항상 그렇지 않다. 저장용 모양과 규칙 중심 객체는 다를 수 있다.
- "Request DTO를 바로 `repository.save(...)`에 넘기면 안 되나요?"
  - 그러면 웹 계약이 저장 계층까지 흘러가서 입력 형식과 DB 모양이 같이 묶인다. Service에서 domain object나 command로 한 번 끊는 편이 안전하다.
- "작은 프로젝트인데 다 나눠야 하나요?"
  - 아니다. Repository 하나로 시작하고 필요할 때만 더 쪼개면 된다.
- "조회가 복잡해지면 DAO 메서드만 늘리면 되나요?"
  - 화면 중심 읽기가 커지면 [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md)로 분리 판단을 보는 편이 낫다.

## 다음에 읽을 문서

- "왜 Repository를 인터페이스 계약으로 두는지"가 더 궁금하면: [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
- "지금 막힌 질문부터 고르고 싶으면": [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)
- "메서드 이름만 봐도 Repository와 DAO를 구분하고 싶으면": [Repository Naming Smells Primer](./repository-naming-smells-primer.md)
- "도메인 객체와 JPA Entity를 어디서 나눌지"가 궁금하면: [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- "Spring에서 이 연결을 누가 주입하나요?"가 다음 질문이면: [의존성 주입 기초](./dependency-injection-basics.md)
- "읽기 모델 분리까지 이어서 보고 싶으면": [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md)

## 한 줄 정리

같은 주문 생성 예시에서 `Service`는 `Repository`에 저장을 부탁하고, Repository 아래에서 `DAO`와 `Entity`가 SQL 실행과 저장 모양을 맡는다고 기억하면 첫 구분은 충분하다.
