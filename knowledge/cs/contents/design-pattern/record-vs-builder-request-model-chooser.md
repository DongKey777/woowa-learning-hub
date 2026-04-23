# 요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까

> 한 줄 요약: 요청/조회 모델이 작고 뜻이 바로 보이면 `record`나 생성자로 두고, 이름 있는 정규화가 필요하면 정적 팩토리로 올리고, 선택 조합이 많아 호출부가 흐려지면 builder를 쓴다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)
> - [빌더 패턴 기초](./builder-pattern-basics.md)
> - [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
> - [Query Object and Search Criteria Pattern](./query-object-search-criteria-pattern.md)
> - [Builder vs Fluent Mutation Smell](./builder-vs-fluent-mutation-smell.md)

retrieval-anchor-keywords: record vs builder request model, request dto record or builder, query object record or builder, request object static factory chooser, request dto constructor or builder, small dto stay record, when to use builder for request dto, when to use static factory for query object, beginner request model chooser, beginner dto creation guide, record vs builder beginner, request record builder static factory, query criteria builder or record, 요청 모델 record builder 선택, 요청 dto builder 언제 쓰나, 작은 dto는 record로 두기, query object 정적 팩토리, 요청 객체 생성자 vs 빌더, request model primer, request query object primer

---

## 이 문서는 언제 읽으면 좋은가

아래 질문이 섞이면 이 chooser를 먼저 보면 된다.

- "`record`로 이미 만들 수 있는데 builder까지 붙여야 하나?"
- 검색 조건 객체가 조금 커졌는데 생성자, 정적 팩토리, builder 중 어디서 멈춰야 할지 모르겠다
- request DTO와 query object를 전부 `@Builder`로 만드는 팀 습관이 과한지 판단이 안 선다
- 검증이나 기본값이 생기면 곧바로 builder로 가야 한다고 느껴진다

핵심은 패턴 이름이 아니라 **호출부가 얼마나 쉽게 읽히는지**와 **생성 시점 규칙이 얼마나 커졌는지**다.

---

## 30초 선택 가이드

먼저 아래 세 줄만 보면 대부분 정리된다.

- 필드가 적고 한 줄 호출만으로 뜻이 보이면 `record`나 생성자로 둔다.
- 같은 타입이지만 **정규화, 기본값, 이름 있는 생성 의미**가 필요하면 정적 팩토리를 붙인다.
- 선택 필드가 많아 `null`, `true`, `false`가 늘고 호출부가 흐려지면 builder를 쓴다.

짧게 외우면 다음과 같다.

- **"작고 바로 읽힌다"**면 `record`
- **"이름 붙여 정리해야 한다"**면 정적 팩토리
- **"옵션 조합이 많아 읽기 어렵다"**면 builder

---

## 한눈에 구분

| 상황 | 기본 선택 | 왜 그 선택이 맞는가 | 예시 |
|---|---|---|---|
| 필드 2~4개, 모두 필수, 의미가 바로 보인다 | `record` / 생성자 | 가장 짧고 읽기 쉽다 | `LoginRequest(String email, String password)` |
| 필드는 아직 적지만 trimming, 기본값, 이름 있는 생성이 필요하다 | `record` + 정적 팩토리 | 생성 의미와 정규화를 한 곳에 모은다 | `OrderSearchRequest.of(keyword, page, size)` |
| 선택 필드가 많고 호출부에 `null`/flag가 섞인다 | builder | 어떤 값을 채웠는지 이름으로 드러난다 | `ProductQuery.builder().status(...).sellerId(...).build()` |
| builder가 너무 커져 화면 요구가 뒤섞였다 | builder 추가보다 객체 분리 먼저 검토 | "조립 방법" 문제가 아니라 "책임 혼합" 문제일 수 있다 | 관리자 검색용 / 정산 검색용 criteria 분리 |

한 문장으로 다시 정리하면:

- `record`는 **작은 입력 묶음**
- 정적 팩토리는 **이름 있는 생성 경계**
- builder는 **읽기 어려운 조립을 펼쳐 주는 도구**

---

## 먼저 잘라야 하는 오해

이 chooser는 "bean으로 만들까?"를 묻는 문서가 아니다.

- 여기서 비교하는 것은 **호출부가 request/query 모델을 어떻게 만들까**다
- `Service`, `Repository`, `Client` 같은 협력자 주입 문제는 [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md) 쪽 질문이다

즉 먼저 이렇게 자르면 된다.

- **협력자를 연결하는가?** DI/bean 쪽 질문
- **이번 호출의 입력을 조립하는가?** `record`/정적 팩토리/builder 질문

---

## 1. 가장 먼저 보는 기본값은 작은 `record`

작은 요청 모델은 대개 `record`로 충분하다.

```java
public record CancelOrderRequest(Long orderId, String reason) {
}
```

이 선택이 좋은 이유는 단순하다.

- 필드가 적다
- 모두 필수다
- 호출부에서 뜻이 바로 읽힌다
- 나중에 바인딩이나 테스트 코드도 짧다

```java
CancelOrderRequest request = new CancelOrderRequest(orderId, reason);
```

처음부터 builder를 붙이면 얻는 것보다 잃는 것이 많을 수 있다.

- 코드가 늘어난다
- 작은 DTO까지 "무거운 패턴"처럼 느껴진다
- 읽는 사람이 왜 builder가 필요한지 오히려 생각해야 한다

초보자 기준 첫 기본값은 보통 이쪽이다.

---

## 2. 규칙이 생겨도 곧바로 builder로 갈 필요는 없다

작은 요청 모델에 규칙이 생기면 먼저 **정적 팩토리 하나로 해결되는지** 본다.

예를 들어 검색 조건에서 빈 문자열 정리와 기본 페이지 크기만 필요할 수 있다.

```java
public record MemberSearchRequest(String keyword, int page, int size) {
    public static MemberSearchRequest of(String keyword, Integer page, Integer size) {
        String normalizedKeyword =
            keyword == null || keyword.isBlank() ? null : keyword.trim();

        return new MemberSearchRequest(
            normalizedKeyword,
            page == null ? 0 : Math.max(page, 0),
            size == null ? 20 : Math.min(Math.max(size, 1), 100)
        );
    }
}
```

여기서는 builder보다 정적 팩토리가 더 자연스럽다.

- 객체 모양은 아직 작다
- 생성 이름 `of(...)` 또는 `from(...)`이 의미를 준다
- 정규화와 기본값을 한 지점에 모을 수 있다
- 호출부는 여전히 짧다

```java
MemberSearchRequest request = MemberSearchRequest.of(keyword, page, size);
```

즉 **"규칙이 생겼다" = "builder로 가야 한다"**는 아니다.

---

## 3. builder는 호출부가 읽기 어려워졌을 때 꺼낸다

다음처럼 선택 필드가 많아지면 builder가 힘을 발한다.

```java
public record ProductQuery(
    String keyword,
    ProductStatus status,
    Long sellerId,
    Boolean discountedOnly,
    LocalDate fromDate,
    LocalDate toDate,
    String sortBy,
    int page,
    int size
) {
}
```

생성자로 만들면 이런 코드가 나오기 쉽다.

```java
ProductQuery query = new ProductQuery(
    keyword,
    status,
    sellerId,
    true,
    fromDate,
    toDate,
    "createdAt",
    0,
    50
);
```

이 시점의 문제는 검증 자체보다 **호출부 가독성**이다.

- 어떤 자리에 어떤 값이 들어가는지 헷갈린다
- `null`과 boolean flag가 의미를 숨긴다
- 화면별로 일부 필드만 채우는 코드가 많아진다

builder로 바꾸면 조립 의도가 다시 보인다.

```java
ProductQuery query = ProductQuery.builder()
    .keyword(keyword)
    .status(status)
    .sellerId(sellerId)
    .discountedOnly(true)
    .fromDate(fromDate)
    .toDate(toDate)
    .sortBy("createdAt")
    .page(0)
    .size(50)
    .build();
```

여기서 핵심은 builder가 "더 고급 패턴"이라서가 아니라, **생성자 호출이 이미 읽기 실패를 일으켰기 때문**이다.

---

## 한 예시를 세 단계로 보기

같은 query object도 요구가 커질수록 선택이 달라질 수 있다.

### 1단계: 처음엔 `record`

```java
public record CouponListRequest(Long memberId, int page) {
}
```

필드가 적고 모두 필수면 이걸로 끝이다.

### 2단계: 정규화가 붙으면 정적 팩토리

```java
public record CouponListRequest(Long memberId, String status, int page) {
    public static CouponListRequest from(Long memberId, String status, Integer page) {
        return new CouponListRequest(
            memberId,
            status == null || status.isBlank() ? "ACTIVE" : status.trim(),
            page == null ? 0 : Math.max(page, 0)
        );
    }
}
```

필드는 아직 작지만 생성 규칙을 숨기고 싶다면 여기까지면 충분하다.

### 3단계: 선택 조합이 많아지면 builder

```java
CouponQuery query = CouponQuery.builder()
    .memberId(memberId)
    .status(status)
    .channel(channel)
    .expiresBefore(expiresBefore)
    .includeUsed(false)
    .page(0)
    .size(20)
    .build();
```

여기서는 "정규화"보다 "조립 가독성"이 더 큰 문제다.

---

## 자주 헷갈리는 질문

- **"필드가 4개만 넘어가면 무조건 builder인가요?"**  
  아니다. 필드 수보다 호출부가 한눈에 읽히는지가 더 중요하다. 4~5개여도 모두 필수이고 의미가 분명하면 `record`가 더 낫다.
- **"검증이 있으면 record를 못 쓰나요?"**  
  아니다. 작은 모델이면 `record`에 compact constructor나 정적 팩토리를 붙여도 된다. 검증이 있다는 이유만으로 builder가 필요한 것은 아니다.
- **"`@Builder`를 붙이면 나중에 편하니 그냥 기본값으로 쓰면 안 되나요?"**  
  보통은 과하다. 작은 요청 DTO까지 전부 builder로 시작하면 문서와 코드가 함께 무거워진다.
- **"query object는 원래 복잡하니 builder가 기본 아닌가요?"**  
  아니다. 작은 검색 조건은 `record` + 정적 팩토리로도 충분하다. 정말 옵션 조합이 많아질 때 builder를 꺼내면 된다.

---

## 코드 리뷰에서 보는 빠른 체크포인트

- 생성자 호출을 읽을 때 "세 번째 인자가 뭐였지?"가 바로 떠오르면 builder 후보다.
- 호출부가 짧고 모두 필수인데도 builder를 썼다면 과설계 신호일 수 있다.
- 기본값, trimming, page-size 보정 같은 규칙이 흩어졌다면 정적 팩토리 후보다.
- builder가 12개 필드를 다 받기 시작하면 객체를 둘로 나눌지 먼저 본다.

---

## 더 깊이 가려면

- [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md) — request/query 모델 생성과 bean wiring을 먼저 분리한다
- [빌더 패턴 기초](./builder-pattern-basics.md) — builder가 왜 필요한지, 언제 과한지 더 짧게 잡는다
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md) — 이름 있는 생성이 왜 builder와 다른지 이어서 본다
- [Query Object and Search Criteria Pattern](./query-object-search-criteria-pattern.md) — request model이 query object로 커질 때 read contract 관점을 이어서 본다

---

## 한 줄 정리

요청/조회 모델은 먼저 작은 `record`로 시작하고, 이름 있는 정규화가 필요하면 정적 팩토리를 붙이고, 선택 조합 때문에 호출부가 읽기 어려워질 때 builder로 올리면 된다.
