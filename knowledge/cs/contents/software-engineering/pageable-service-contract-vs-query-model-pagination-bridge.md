# `Pageable` leak vs query-model pagination bridge

> 한 줄 요약: `service가 Pageable을 받아요`라는 리뷰는 보통 "pagination이 문제"가 아니라 "Spring Data 타입이 유스케이스 계약을 대신했다"는 뜻이다. pagination 자체는 필요할 수 있지만, 초심자 기본값은 service 계약에서 한 번 `query` 언어로 좁히고 adapter/query repository 쪽에서 `Pageable`로 번역하는 흐름이다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Service Contract Smell Cards](./service-contract-smell-cards.md)
- [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
- [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md)
- [Bulk Helper Ports vs Query Model Separation](./bulk-helper-ports-vs-query-model-separation.md)
- [software-engineering 카테고리 인덱스](./README.md)
- [Cursor Pagination and Sort Stability Pattern](../design-pattern/cursor-pagination-sort-stability-pattern.md)

retrieval-anchor-keywords: pageable leak vs query model pagination, service가 pageable을 받는 건 무조건 냄새인가요, pageable in service beginner, pagination contract bridge, query model pagination beginner, spring data pageable leak, pageable 어디까지 넘겨요, page request value object, query repository pagination, adapter pagination boundary, 처음 pageable 헷갈려요, 왜 service가 pageable을 받으면 안 되나요, pageable smell next step, legitimate pagination adapter

## 핵심 개념

냄새 카드에서 말한 핵심은 "`Pageable`이 존재하면 안 된다"가 아니다.
핵심은 **유스케이스 service 계약이 Spring Data 언어로 굳어 버렸는가**다.

초심자에게는 아래처럼 구분하면 가장 덜 헷갈린다.

- pagination 필요 여부: 목록/검색/관리 화면이라면 충분히 필요할 수 있다
- `Pageable` 노출 위치: controller/adapter/JPA query 구현 쪽이면 자연스러울 수 있다
- service 계약 언어: 가능하면 `FindOrdersQuery`, `OrderPageRequest`, `OrderSliceResult`처럼 조회 의도를 먼저 말한다

즉 `Pageable` leak는 "pagination을 쓰지 마"가 아니라, **"pagination 세부를 어디까지 들고 갈지 구분하자"**에 가깝다.

## 한눈에 보기

| 지금 보이는 모양 | 먼저 붙일 이름 | 초심자 기본값 |
|---|---|---|
| `OrderService.findAll(Pageable pageable)` | service 계약 leak 후보 | `FindOrdersQuery` 같은 query 타입으로 한 번 좁힌다 |
| `OrderQueryRepository.findSummaries(..., Pageable pageable)` | adapter/query 구현 세부일 수 있음 | query repository 경계에서 허용 가능하되, 바깥 service 계약과 같은 층인지 먼저 확인한다 |
| controller가 `page`, `size`, `sort`를 받아 `OrderListQuery`로 만든다 | 정상적인 웹 입력 처리 | controller에서 query 객체로 번역한다 |
| JPA adapter가 `OrderListQuery`를 `Pageable`로 변환한다 | 정상적인 프레임워크 번역 | Spring Data 세부를 adapter 안에 가둔다 |
| `Page<OrderResponse>`를 service가 공개 API처럼 바로 반환한다 | 조회 계약과 프레임워크 타입이 묶임 | `OrderPageResult`나 `SliceResult<OrderSummaryView>`를 먼저 검토한다 |

짧게 외우면 이렇다.

- **pagination은 기능**
- **`Pageable`은 Spring Data 표현**
- **service 계약은 조회 의도**

## 냄새 카드 다음에 바로 답해야 하는 질문

`service가 Pageable을 받아요`를 봤을 때 초심자가 다음으로 가장 자주 막히는 지점은 보통 아래 둘이다.

1. "그럼 pagination 기능 자체도 service 밖으로 빼라는 뜻인가요?"
2. "query model을 쓰면 결국 `Pageable`을 다시 쓰는 것 아닌가요?"

둘 다 답은 "아니요, 위치를 나누자는 뜻"에 가깝다.

| 질문 | 짧은 답 | 바로 다음 행동 |
|---|---|---|
| pagination이 필요한데 `Pageable`이 왜 냄새죠? | 기능이 아니라 프레임워크 타입이 계약을 대신해서다 | 먼저 `page/size/sort`가 유스케이스에서 정말 필요한 값인지 적는다 |
| 결국 DB 조회는 `Pageable`로 하지 않나요? | 할 수 있다. 다만 보통 adapter/query repository에서 번역한다 | service 메서드 밖에서 query 객체를 하나 만든다 |
| query model이면 service가 `Pageable`을 받아도 되나요? | read-side 전용 경계인지에 따라 다르지만 beginner-safe 기본값은 여전히 query 타입이다 | `FindOrdersQuery`와 `OrderPageResult` 이름부터 고른다 |

## 언제 leak로 보는가

아래 신호가 보이면 `Pageable`은 대체로 service 계약 leak 쪽에 가깝다.

| 신호 | 왜 leak 쪽인가 |
|---|---|
| 메서드 이름은 `findOrders`, `searchOrders`인데 입력이 `Pageable` 하나뿐이다 | 조회 의도보다 Spring Data API가 앞에 보인다 |
| filter 조건은 따로 DTO에 있고 pagination만 `Pageable`로 따로 흩어져 있다 | service가 두 언어를 동시에 말한다 |
| 반환 타입이 `Page<OrderEntity>` 또는 `Page<OrderResponse>`다 | 조회 결과 계약과 프레임워크 포장이 한 번에 묶인다 |
| 테스트에서 service 호출마다 `PageRequest.of(...)`를 먼저 세팅해야 한다 | 유스케이스 설명보다 프레임워크 조립이 먼저 보인다 |

예를 들면 아래 쪽은 beginner 기준으로 냄새 카드 다음 리팩토링 후보다.

```java
public Page<OrderResponse> searchOrders(
        OrderStatus status,
        Pageable pageable
) {
    ...
}
```

이 경우 먼저 떠올릴 작은 수정은 보통 이 정도다.

```java
public OrderPageResult searchOrders(FindOrdersQuery query) {
    ...
}
```

여기서 `FindOrdersQuery` 안에 `page`, `size`, `sortBy`, `direction`, `status`를 둘 수 있다.
핵심은 pagination 정보를 없애는 것이 아니라, **service가 Spring Data 타입 대신 조회 의도 묶음을 받게 하는 것**이다.

## 언제 legitimate pagination으로 보는가

반대로 아래는 pagination이 정당한 위치에 있는 경우가 많다.

| 위치 | 왜 상대적으로 자연스러운가 |
|---|---|
| controller가 query string을 읽는 자리 | `page`, `size`, `sort`는 원래 웹 입력에 가깝다 |
| query repository adapter/JPA 구현체 | Spring Data/JPA가 실제 pagination 실행을 담당한다 |
| read-side projection 전용 adapter | SQL projection, 정렬 안정성, count query 세부를 이 층에서 다룬다 |

초심자 기본 흐름은 아래처럼 보면 안전하다.

```text
HTTP query string
-> OrderListQuery(page, size, sort, status)
-> read/query service
-> OrderQueryRepository
-> JpaOrderQueryRepository가 Pageable로 번역
```

여기서 caveat도 하나 있다.
팀에 따라 read-only application service가 `Pageable`을 직접 받을 수도 있다.
하지만 그 service가 여전히 다른 use case service와 같은 public contract라면, 초심자 기본값으로는 query 타입으로 한 번 감싸 두는 편이 경계 설명력이 더 좋다.

즉 "legitimate"의 기준은 pagination 존재 여부가 아니라 **그 타입이 유스케이스 계약인지, 구현 세부 번역 층인지**다.

## 비교 예시

아래 두 코드는 둘 다 목록 조회를 한다.
차이는 "pagination이 있느냐"가 아니라, "누가 Spring Data 언어를 직접 말하느냐"다.

```java
public interface OrderListUseCase {
    OrderPageResult findOrders(OrderListQuery query);
}

public interface OrderQueryRepository {
    Page<OrderSummaryView> findOrders(OrderListQuery query, Pageable pageable);
}
```

위 예시에서는:

- use case 계약은 `OrderListQuery`, `OrderPageResult`를 말한다
- query repository 구현은 `Pageable`을 사용할 수 있다
- `Pageable`은 안쪽 번역 도구이지, 바깥 계약 이름이 아니다

반면 아래는 leak 쪽으로 읽기 쉽다.

```java
public interface OrderService {
    Page<OrderSummaryView> findOrders(Pageable pageable);
}
```

이 시그니처만 보면 `status`, `keyword`, `정렬 기준`, `다음 단계 이동` 같은 조회 의도가 빠지고 Spring Data 표현만 남는다.

## 흔한 오해와 함정

- "`Pageable`을 감추면 결국 값 복사만 늘어나는 것 아닌가요?"
  - 작은 CRUD에서는 그렇게 느껴질 수 있다. 그래도 beginner-safe 기본값은 service contract 설명력을 먼저 얻는 쪽이다.
- "query model 문서에서 `Pageable`을 쓰던데, 그러면 smell 카드와 충돌 아닌가요?"
  - 충돌이라기보다 층 구분 문제다. query repository/JPA adapter 예시는 구현 쪽 pagination이고, smell 카드는 public service 계약을 본다.
- "`Pageable`이 있으면 무조건 나쁜 설계인가요?"
  - 아니다. 특히 Spring Data adapter 내부에서는 자연스럽다. 다만 초심자 첫 기준으로는 "service 공개 계약에 그대로 보이는가"를 먼저 본다.
- "`Slice`, cursor pagination이면 이 문서는 무효인가요?"
  - 아니다. `Pageable` 대신 cursor token이나 `Slice`를 써도 같은 질문을 적용할 수 있다. 핵심은 pagination 세부가 use case 계약을 덮는지다.

## 더 깊이 가려면

- smell card에서 바로 넘어왔다면: [Service Contract Smell Cards](./service-contract-smell-cards.md)
- read-heavy query model 큰 그림이 더 필요하면: [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
- 같은 DB query repository에서 멈춰도 되는지 보려면: [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md)
- helper port와 query repository를 헷갈린다면: [Bulk Helper Ports vs Query Model Separation](./bulk-helper-ports-vs-query-model-separation.md)
- cursor 기반 pagination 안정성까지 보려면: [Cursor Pagination and Sort Stability Pattern](../design-pattern/cursor-pagination-sort-stability-pattern.md)

## 면접/시니어 질문 미리보기

- "왜 `Pageable`을 service에서 감추려 하나요?"
  - pagination 기능을 숨기려는 게 아니라, Spring Data 표현이 유스케이스 계약 이름을 대신하지 않게 하려는 것이다.
- "read-only service는 framework 타입을 받아도 되나요?"
  - 팀 규칙에 따라 가능하다. 다만 public contract인지 adapter 성격인지 먼저 구분해야 한다.
- "query object로 감싸면 어떤 이득이 있나요?"
  - filter, sort, page 정책을 use case 언어로 묶어서 테스트와 리뷰 설명이 쉬워진다.

## 한 줄 정리

`service가 Pageable을 받아요`라는 냄새의 핵심은 pagination 존재가 아니라, Spring Data 타입이 유스케이스 계약을 대신했는지 여부다. 초심자 기본값은 service에서는 query/result 언어를 쓰고, 실제 `Pageable` 번역은 adapter/query repository 쪽에 두는 것이다.
