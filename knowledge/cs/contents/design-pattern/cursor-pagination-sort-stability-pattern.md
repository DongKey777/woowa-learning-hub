# Cursor Pagination and Sort Stability Pattern

> 한 줄 요약: cursor pagination은 offset보다 drift에 강하지만, 정렬 키가 안정적이지 않으면 중복/누락이 생기므로 sort stability와 tie-breaker 설계가 핵심이다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Query Object and Search Criteria Pattern](./query-object-search-criteria-pattern.md)
> - [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)

retrieval-anchor-keywords: cursor pagination, seek pagination, stable ordering, pagination tie breaker, cursor schema version, normalized query fingerprint, mutable sort key drift, cutover cursor invalidation, pagination parity sampling, two page continuity check, legacy cursor compatibility, cursor version verdict, projection replacement pagination, read model migration pagination parity, cursor verdict pair, continuity outcome, pagination parity packet schema

---

## 핵심 개념

read model에서 목록 조회가 커지면 offset pagination은 금방 흔들린다.

- 새 데이터 삽입
- 중간 삭제
- 정렬 기준 변경
- 대량 backfill

cursor pagination은 이런 drift에 더 강하지만, 아무 sort에나 붙인다고 안전해지지는 않는다.  
핵심은 **stable ordering**이다.

### Retrieval Anchors

- `cursor pagination`
- `sort stability`
- `stable ordering key`
- `pagination tie breaker`
- `cursor drift`
- `seek pagination`
- `pagination parity sampling`
- `cursor continuity check`

---

## 깊이 들어가기

### 1. cursor는 정렬 규칙의 압축 표현이다

cursor는 단순 token이 아니라 "이 정렬 기준에서 여기까지 봤다"는 의미다.

그래서 다음이 바뀌면 cursor 의미도 바뀐다.

- sort key
- direction
- filter canonicalization
- tie-breaker

### 2. tie-breaker가 없으면 같은 값 묶음에서 중복/누락이 난다

예를 들어 `createdAt DESC`만 쓰면 같은 timestamp를 가진 row들이 흔들릴 수 있다.

보통은 다음처럼 stable pair를 쓴다.

- `createdAt DESC, id DESC`
- `score DESC, id DESC`

즉 마지막 tie-breaker는 유일하고 monotonic한 값이 좋다.

### 3. cursor pagination도 read model freshness 영향을 받는다

projection lag나 rebuild 중에는 ordering이 바뀔 수 있다.

- 늦게 도착한 projection row
- backfill로 뒤늦게 채워진 row
- cutover 직후 다른 sort semantics

그래서 cursor safety는 read model 운영 상태와도 연결된다.

### 4. sort stability는 API 계약이다

사용자가 같은 query+cursor를 다시 보내면 일관된 의미가 유지돼야 한다.

따라서 다음이 고정돼야 한다.

- sort default
- supported sort key set
- cursor schema version
- canonicalized filter set

### 5. mutable sort key는 특히 조심해야 한다

자주 바뀌는 score, updatedAt, rank는 paging drift를 만들기 쉽다.

이때는:

- stronger tie-breaker
- snapshot time cutoff
- requery policy

같은 보완 장치가 필요할 수 있다.

### 6. cursor는 마지막 row 값만이 아니라 query contract와 묶여야 한다

실무에서 자주 생기는 실수는 cursor를 `(lastSeenCreatedAt, lastSeenId)` 같은 위치 정보로만 보는 것이다.

하지만 실제로는 다음이 같아야 같은 cursor다.

- normalized filter set
- sort key + direction
- page size cap
- collation / null ordering 가정
- cursor schema version

즉 cursor는 "여기까지 읽었다"가 아니라 **"이 읽기 계약에서 여기까지 읽었다"**에 가깝다.

### 7. stable ordering은 DB 정렬식만이 아니라 API 재시도 의미까지 포함한다

정렬이 안정적이라는 말은 단순히 SQL `ORDER BY`가 있다는 뜻이 아니다.

- 같은 요청을 재시도해도 다음 페이지 의미가 유지되고
- canary / dual-read 비교에서도 같은 순서를 기대할 수 있고
- cutover 전후에도 cursor 무효화 조건이 명확해야 한다

특히 문자열 정렬, null 처리, locale/collation 차이는 new read model에서 은근히 달라질 수 있다.  
row 집합은 같아도 순서가 달라지면 사용자 입장에서는 다른 페이지가 된다.

### 8. mutable sort key를 쓰려면 drift 완화 전략을 함께 계약해야 한다

`updatedAt`, `score`, `rank` 같은 값은 페이지 사이에 바뀔 수 있다.

이때는 "cursor를 쓴다"만으로 부족하고, 보통 다음 중 하나를 같이 고른다.

- snapshot cutoff를 함께 encode한다
- mutable key 뒤에 stronger tie-breaker를 둔다
- drift 가능성을 문서화하고 재조회 정책을 둔다
- strict list에는 immutable order로 제한한다

즉 mutable sort는 기능 옵션이 아니라 consistency budget 문제다.

### 9. cutover 전에는 기존 cursor를 얼마나 신뢰할지 먼저 정해야 한다

old/new read model이 다음 중 하나라도 다르면 예전 cursor 재사용은 위험하다.

- 기본 sort
- tie-breaker
- 문자열 collation
- null ordering
- 늦게 도착한 row의 가시성

그래서 cutover 정책은 보통 셋 중 하나로 간다.

- 기존 cursor 전면 무효화
- cursor schema version 상승
- dual-read 검증을 통과한 endpoint만 cursor 연속 사용 허용

### 10. 목록 parity는 "첫 페이지가 비슷하다"보다 "다음 페이지까지 이어진다"를 봐야 한다

cutover canary에서 first-page 결과만 비교하면 놓치는 문제가 많다.

- 첫 페이지 key 집합은 같지만 next cursor encoding이 달라 둘째 페이지부터 어긋남
- tie-breaker 경계 row가 page size마다 다르게 잘림
- mutable sort key가 canary 윈도우 동안 재배치됨

그래서 sampled dual-read는 같은 normalized query에 대해 최소한 다음 차원을 같이 본다.

| 샘플 지표 | 무엇을 비교하는가 | 왜 필요한가 |
|---|---|---|
| first-page key mismatch rate | 첫 페이지 key 집합과 순서 | 초기 결과 노출 차이 감지 |
| next-cursor emission mismatch rate | old/new가 발급한 cursor version, verdict, rejection reason | cursor contract drift 감지 |
| second-page continuity mismatch rate | 발급된 cursor로 읽은 둘째 페이지 key 집합과 순서 | tie-breaker 경계 문제 감지 |
| duplicate-or-gap sample rate | page 1 + page 2 union에서 중복/누락 발생 여부 | 사용자 체감 pagination bug 감지 |

핵심은 page 1이 같은지보다 **page 1 -> next cursor -> page 2**가 같은 의미로 이어지는지다.

이때 sample event는 [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)의 `cursor_verdict_pair`와 `page_parity.continuity_outcome`으로 고정해 두는 편이 좋다. 그래야 first-page mismatch, verdict drift, second-page order drift를 같은 표본 언어로 집계할 수 있다.

이 기준을 read-model replacement 운영 packet으로 더 좁히면 [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)처럼 stable sort audit, legacy cursor verdict, rollback 시 cursor 정책 정리까지 같이 적는 편이 해석이 선명하다.

### 11. cursor-version parity check는 호환성 정책이 일관되게 관찰되는지 봐야 한다

version bump가 있다고 해서 항상 실패는 아니다. 중요한 건 어떤 정책을 채택했는지 샘플링에서 명확히 드러나는가다.

- legacy cursor를 그대로 받아 같은 의미의 다음 페이지를 돌려준다
- legacy cursor를 명시적으로 거절하고 새 version으로 다시 시작하게 한다
- 일부 sort/filter 조합만 호환하고 나머지는 막는다

운영적으로는 각 샘플에 대해 다음을 남기는 편이 좋다.

- normalized query fingerprint
- page size bucket
- requested cursor version
- `ACCEPTED` / `REISSUED` / `REJECTED` verdict
- rejection reason code
- first-page parity와 second-page continuity 결과

이렇게 해야 mismatch가 데이터 차이인지, 의도된 version cut인지, 잘못된 legacy acceptance인지 분리된다.  
특히 `legacy accepted but second-page mismatch`는 가장 위험한 조합이다.

---

## 실전 시나리오

### 시나리오 1: 주문 목록

`createdAt DESC, orderId DESC`로 cursor를 구성하면 같은 초에 생성된 주문도 안정적으로 넘길 수 있다.

### 시나리오 2: 추천 점수 목록

`score DESC`만으로는 흔들리므로 `score DESC, itemId DESC` 같은 tie-breaker가 필요하다.

### 시나리오 3: projection cutover

old/new projection의 sort semantics가 다르면 cursor를 그대로 재사용하면 안 된다.  
cursor schema version 또는 cutover invalidation이 필요하다.

### 시나리오 4: 관리자 검색 필터 변경

기본 sort를 `createdAt DESC`에서 `createdAt DESC, orderId DESC`로 강화하거나, keyword blank 처리 규칙을 바꿨다면 old cursor를 그대로 받지 않는 편이 안전하다.

같은 token 문자열이어도:

- normalized query fingerprint가 달라지고
- 반환 순서 계약이 달라지고
- 다음 페이지의 중복/누락 가능성이 달라진다

### 시나리오 5: 검색 cutover canary의 2-page continuity 샘플

검색 projection을 old/new dual-read로 비교할 때 first page만 맞는다고 승격하면 위험하다.

- `size=20`, `sort=createdAt,DESC` 샘플은 첫 페이지가 같지만 둘째 페이지에서 경계 row가 어긋날 수 있고
- old cursor `v1`을 new projection이 받아 주더라도 next cursor verdict가 달라질 수 있고
- 이 차이는 row count parity 대시보드에는 잘 드러나지 않는다

그래서 canary에서는 endpoint별로 `first page parity`, `second-page continuity`, `cursor version verdict`를 함께 수집하는 편이 안전하다.

---

## 코드로 보기

```java
public record OrderCursor(
    int version,
    String queryFingerprint,
    Instant createdAt,
    String orderId
) {}
```

```sql
SELECT *
FROM order_read_model
WHERE (created_at, order_id) < (:createdAt, :orderId)
ORDER BY created_at DESC, order_id DESC
LIMIT :pageSize
```

```java
// cursor는 sort key + tie-breaker + normalized query contract를 함께 encode해야 한다.
public boolean matches(OrderCursor cursor, OrderSearchCriteria criteria) {
    return cursor.version() == 2
        && cursor.queryFingerprint().equals(criteria.normalized().fingerprint());
}
```

```java
public enum CursorVerdict {
    ACCEPTED,
    REISSUED,
    REJECTED
}

public record PaginationParitySample(
    String queryFingerprint,
    int pageSize,
    int requestedCursorVersion,
    CursorVerdict cursorVerdict,
    boolean firstPageMatches,
    boolean secondPageMatches
) {}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| offset pagination | 단순하다 | drift와 큰 offset 비용에 약하다 | 작은 내부 목록 |
| cursor pagination | 큰 목록과 drift에 강하다 | sort stability 설계가 필요하다 | 사용자 목록, 피드, 운영 검색 |
| first-page only parity check | 비용이 낮다 | next-cursor drift를 놓친다 | 초기 shadow verify |
| unstable cursor design | 구현이 빠르다 | 중복/누락/재조회 혼란이 생긴다 | 피하는 편이 좋다 |
| versioned cursor contract | cutover와 비교 검증에 유리하다 | cursor payload와 invalidation 정책이 늘어난다 | read model 교체 가능성이 있는 목록 |

판단 기준은 다음과 같다.

- 같은 값 묶음을 깨는 tie-breaker를 반드시 둔다
- cursor는 filter/sort canonicalization과 함께 설계한다
- cutover/rebuild 시 cursor invalidation 정책을 고려한다
- 샘플링은 first-page parity만이 아니라 second-page continuity와 cursor verdict를 같이 본다
- mutable sort key는 cutoff나 재조회 정책까지 같이 설계한다

---

## 꼬리질문

> Q: cursor pagination이면 항상 중복/누락이 사라지나요?
> 의도: transport 형태와 ordering stability를 구분하는지 본다.
> 핵심: 아니다. sort key와 tie-breaker가 안정적이어야 한다.

> Q: `updatedAt`으로 정렬하면 왜 위험한가요?
> 의도: mutable sort key 문제를 이해하는지 본다.
> 핵심: 페이지 사이에 값이 바뀌며 순서가 흔들릴 수 있기 때문이다.

> Q: cutover 후에도 예전 cursor를 계속 써도 되나요?
> 의도: cursor schema와 sort contract를 같이 보는지 본다.
> 핵심: 보통 조심해야 한다. sort semantics가 바뀌면 invalidation이나 versioning이 필요하다.

> Q: first page만 같으면 pagination cutover는 안전한가요?
> 의도: 결과 집합 parity와 next-page continuity를 구분하는지 본다.
> 핵심: 아니다. 둘째 페이지까지 이어지는 cursor semantics를 같이 봐야 한다.

## 한 줄 정리

Cursor pagination의 핵심은 token 자체보다 stable ordering과 tie-breaker이며, read model 운영 변화까지 고려해야 중복과 누락을 줄일 수 있다.
