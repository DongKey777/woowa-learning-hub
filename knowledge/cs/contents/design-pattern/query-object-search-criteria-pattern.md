# Query Object and Search Criteria Pattern

> 한 줄 요약: Query Object는 복잡한 조회 파라미터를 하나의 읽기 계약으로 모아 Query Service와 Read Repository 경계를 선명하게 하고, 화면별 검색 요구가 repository 메서드 폭발로 번지는 것을 막아 준다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Specification vs Query Service Boundary](./specification-vs-query-service-boundary.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Specification Pattern](./specification-pattern.md)
> - [Command Handler Pattern](./command-handler-pattern.md)

---

## 핵심 개념

관리자 검색이나 리스트 화면이 커지면 이런 시점이 온다.

- 파라미터가 10개 넘게 늘어난다
- repository 메서드 이름이 길어진다
- controller마다 필터 조합이 조금씩 달라진다

이때 자주 쓰는 읽기 패턴이 Query Object 또는 Search Criteria 객체다.

- 날짜 범위
- 상태 목록
- 정렬 기준
- 페이징
- 키워드
- 화면 전용 필터

핵심은 이걸 도메인 엔티티가 아니라 **read contract**로 다룬다는 점이다.

### Retrieval Anchors

- `query object`
- `search criteria pattern`
- `read query contract`
- `search condition object`
- `query parameter object`
- `admin search model`
- `search normalization`
- `cursor pagination`

---

## 깊이 들어가기

### 1. Query Object는 write command의 반대편 읽기 계약에 가깝다

Command가 쓰기 유스케이스 입력을 캡슐화한다면, Query Object는 읽기 유스케이스 입력을 캡슐화한다.

- `PlaceOrderCommand`
- `OrderSearchCriteria`

둘 다 입력을 모으지만 목적은 다르다.

- command: 상태 변경
- query object: 조회 조건과 표현 요구

### 2. repository method explosion을 막는 데 효과적이다

이런 구조는 금방 한계가 온다.

- `findByStatusAndDateRange`
- `findByStatusAndDateRangeAndKeyword`
- `findByStatusAndDateRangeAndKeywordAndSeller`

Query Object로 바꾸면 공개 계약이 더 안정적이다.

- `search(OrderSearchCriteria criteria)`

### 3. Query Object는 domain specification과 섞이면 안 된다

검색 조건 객체는 보통 화면/운영 요구를 반영한다.

- 정렬
- 페이지 크기
- 탭 선택
- 표시용 필터

이걸 도메인 명세와 같은 계층으로 올리면 의미가 섞인다.  
Query Object는 read side 경계에 두는 편이 자연스럽다.

### 4. criteria object는 validation과 normalization을 가질 수 있다

아주 단순 DTO로 끝낼 수도 있지만, 다음 정도는 가질 수 있다.

- 빈 문자열 -> null 정규화
- 잘못된 페이지 크기 보정
- 정렬 기본값 적용
- 상호배타 필터 검증

즉 읽기 계약의 위생을 유지하는 최소 책임을 줄 수 있다.

### 5. Query Object가 너무 범용이면 다시 `AnythingSearchCriteria`가 된다

반대로 모든 화면을 하나의 거대한 criteria object로 묶어도 smell이다.

- 주문 검색용
- 정산 검색용
- 대시보드 집계용

읽기 목적이 다르면 Query Object도 분리하는 편이 더 낫다.

---

## 실전 시나리오

### 시나리오 1: 관리자 주문 검색

상태, 기간, 결제수단, 회원 등급, 정렬, 페이지 크기를 하나의 `OrderSearchCriteria`로 모아 Query Service에 넘길 수 있다.

### 시나리오 2: 정산 대상 조회

정산 대상은 주문 검색과 비슷해 보여도 기준이 다를 수 있다.  
별도 `SettlementCandidateCriteria`가 더 자연스럽다.

### 시나리오 3: 검색 API 계약 진화

새 필터가 추가되어도 메서드 시그니처를 연쇄적으로 바꾸기보다 criteria 객체만 확장하면 된다.

---

## 코드로 보기

### query object

```java
public record OrderSearchCriteria(
    List<OrderStatus> statuses,
    LocalDate fromDate,
    LocalDate toDate,
    String keyword,
    String sortBy,
    int page,
    int size
) {
    public OrderSearchCriteria normalized() {
        return new OrderSearchCriteria(
            statuses,
            fromDate,
            toDate,
            keyword == null || keyword.isBlank() ? null : keyword.trim(),
            sortBy == null ? "createdAt" : sortBy,
            Math.max(page, 0),
            Math.min(Math.max(size, 1), 100)
        );
    }
}
```

### query service

```java
public class OrderQueryService {
    public Page<OrderSearchView> search(OrderSearchCriteria criteria) {
        return orderReadRepository.search(criteria.normalized());
    }
}
```

### repository boundary

```java
public interface OrderReadRepository {
    Page<OrderSearchView> search(OrderSearchCriteria criteria);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 긴 메서드 파라미터 목록 | 처음엔 단순하다 | 조건이 늘수록 유지보수가 어렵다 | 필터가 거의 없는 간단 조회 |
| Query Object | 조회 계약이 선명하고 확장 가능하다 | 객체 수가 늘어난다 | 검색 조건과 정렬/페이지가 복잡할 때 |
| 거대 범용 Criteria | 재사용이 많아 보인다 | 목적이 섞여 다시 비대해진다 | 보통 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- 읽기 계약이 복잡해지면 Query Object
- 도메인 규칙 조건과 화면 검색 조건은 분리
- 목적이 다른 검색은 criteria도 분리

---

## 꼬리질문

> Q: Query Object와 Specification은 같은 건가요?
> 의도: 읽기 계약과 도메인 조건을 구분하는지 본다.
> 핵심: 아니다. Query Object는 조회 계약, Specification은 도메인 조건 표현에 더 가깝다.

> Q: Query Object는 그냥 DTO 아닌가요?
> 의도: 얇은 계약 객체의 의미를 보는 질문이다.
> 핵심: 맞다. 다만 읽기 경계에서 정규화와 계약 진화 지점을 제공하는 점이 중요하다.

> Q: 화면마다 criteria를 따로 만들면 너무 많아지지 않나요?
> 의도: 과분리와 과공유 사이 균형을 보는 질문이다.
> 핵심: 목적이 크게 다르면 분리하고, 진짜 공유되는 read contract만 재사용하는 편이 낫다.

## 한 줄 정리

Query Object는 복잡한 검색 파라미터를 읽기 계약으로 모아 Query Service와 Read Repository 경계를 선명하게 하고, repository 메서드 폭발을 줄여 주는 패턴이다.
