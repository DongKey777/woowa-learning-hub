# Search Normalization and Query Pattern

> 한 줄 요약: 검색 API는 조건을 받는 것보다 조건을 정규화하는 것이 더 중요할 때가 많고, Query Object 앞단의 normalization 규칙이 없으면 같은 의미의 질의가 서로 다른 결과와 캐시 키를 만들기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Query Object and Search Criteria Pattern](./query-object-search-criteria-pattern.md)
> - [Specification vs Query Service Boundary](./specification-vs-query-service-boundary.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Normalization Version Rollout Playbook](./normalization-version-rollout-playbook.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)

retrieval-anchor-keywords: search normalization, query normalization, criteria canonicalization, normalized filter set, normalized sort contract, query fingerprint, dual read parity input, cursor comparability, normalized query fingerprint bucket, input parity sample key, normalization drift rate, cursor version bucket, normalization version rollout, cache namespace bump, reason code compatibility, pagination parity packet schema, fingerprint bucket coverage

---

## 핵심 개념

검색 조건이 많아질수록 단순 DTO 전달만으로는 부족하다.

- 빈 문자열과 null
- 날짜 범위 뒤집힘
- 대소문자/trim 차이
- 중복 status 조건
- 정렬 기본값 부재

이런 차이가 그대로 query layer로 내려가면 같은 의미의 요청도 서로 다른 결과, 다른 캐시 키, 다른 SQL로 이어질 수 있다.

Search normalization 패턴은 Query Object를 **실행 가능한 읽기 계약으로 표준화하는 단계**다.

### Retrieval Anchors

- `search normalization`
- `query normalization`
- `criteria canonicalization`
- `query contract normalization`
- `search defaulting`
- `normalized search criteria`
- `normalized query fingerprint`
- `input parity sample key`

---

## 깊이 들어가기

### 1. normalization은 validation과 다르다

validation은 잘못된 요청을 막는다.  
normalization은 **의미상 같은 요청을 같은 형태로 정리**한다.

- `"  paid "` -> `"paid"`
- `[]` -> `null`
- `from > to` -> swap 또는 reject
- missing sort -> default sort

### 2. canonical form이 있어야 캐시와 비교가 안정된다

검색 결과 캐시, query fingerprint, audit log를 쓰면 canonical form이 특히 중요하다.

- `status=PAID&status=SHIPPED`
- `status=SHIPPED&status=PAID`

의미는 같아도 normalization이 없으면 서로 다른 질의로 취급된다.

### 3. normalization 규칙은 read contract의 일부다

이 규칙을 controller마다 따로 두면 drift가 난다.

- 어떤 API는 blank를 null로 보고
- 어떤 API는 blank를 keyword로 보고
- 어떤 API는 sort default가 다름

그래서 Query Object 또는 Query Service 경계에서 한 번 모아 두는 편이 낫다.

### 4. normalization은 결과 의미를 바꾸지 않는 선에서만 해야 한다

지나친 normalization은 오히려 surprise를 만든다.

- 사용자가 명시한 sort를 임의 변경
- 잘못된 범위를 몰래 swap
- unknown filter를 silently drop

규칙은 예측 가능해야 하고, 보정과 거절의 경계를 문서화하는 편이 좋다.

### 5. normalization은 pagination 안정성과도 연결된다

sort/default/filter canonicalization이 없으면 cursor pagination 결과가 흔들릴 수 있다.

- 같은 cursor인데 다른 sort default
- 같은 keyword인데 trim 여부 다름

즉 normalization은 cursor 안정성의 전제 조건이기도 하다.

### 6. normalization 결과물은 "읽기 계약 스냅샷"으로 남아야 한다

실전에서 중요한 건 raw request를 예쁘게 다듬는 것보다, **정규화 결과를 다른 read-side 단계가 재사용할 수 있게 만드는 것**이다.

- normalized filter set
- normalized sort key + direction
- page size cap
- reject된 필드와 보정된 필드
- query fingerprint

이걸 명시하지 않으면 같은 요청을:

- 캐시 키는 A 방식으로 만들고
- cursor 검증은 B 방식으로 하고
- dual-read 비교는 C 방식으로 하면

서로 다른 의미 체계가 생긴다.  
즉 normalization은 controller 유틸이 아니라 read contract의 기준점이어야 한다.

### 7. 보정 규칙과 거절 규칙을 분리해야 cutover 때 해석이 선명하다

예를 들어 `from > to`를 자동 swap할지, 에러로 거절할지는 단순 UX 취향 문제가 아니다.

- old read model은 swap
- new read model은 reject

이렇게 되면 dual-read parity에서 차이가 "데이터 차이"인지 "입력 해석 차이"인지 분간이 안 된다.

그래서 다음을 문서화하는 편이 좋다.

- silent correction 허용 항목
- 반드시 reject해야 하는 항목
- 기본값이 들어가는 필드
- unknown filter/sort 처리 정책

cutover나 A/B 비교 전에 이 계약이 고정돼 있어야 결과 비교가 의미를 가진다.

### 8. normalization은 sort stability의 선행 조건이다

cursor pagination은 보통 정렬 안정성 문제로 설명되지만, 그 앞단에 query normalization이 먼저 있다.

- `sort=createdAt` 와 `sort=created_at`
- `direction=desc` 와 누락된 direction
- `status=PAID&status=SHIPPED` 와 순서가 뒤집힌 요청

이 차이를 먼저 canonical form으로 고정하지 않으면, tie-breaker를 잘 설계해도 cursor 비교와 재시도가 흔들린다.

정리하면:

1. raw request를 normalized contract로 만든다
2. 그 contract 위에서 stable sort와 cursor를 설계한다
3. 그 contract 그대로 dual-read / cutover parity를 검증한다

### 9. parity 샘플링은 raw query string이 아니라 normalized contract를 키로 묶어야 한다

dual-read 샘플을 raw URL 그대로 집계하면 의미 없는 mismatch가 섞이기 쉽다.

- parameter order만 다른 요청
- blank와 null 표현만 다른 요청
- alias sort name만 다른 요청
- 중복 filter 순서만 다른 요청

그래서 sampling key는 보통 다음처럼 잡는다.

- normalized query fingerprint
- sort family + direction
- page size bucket
- cursor version
- normalization outcome (`ACCEPTED` / `CORRECTED` / `REJECTED`)

이때 bucket 이름과 field 축은 [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)의 `baseline/candidate query_fingerprint`, `fingerprint_bucket`, `page_size_bucket`, `requested_cursor_version` 조합에 맞춰 두는 편이 좋다. 그래야 normalization drift 대시보드와 pagination continuity 대시보드가 같은 sample key를 공유한다.

이렇게 해야 같은 의미 요청을 한 버킷으로 보고, 실제 input drift만 따로 해석할 수 있다.

| 샘플 지표 | 무엇을 보는가 | 왜 필요한가 |
|---|---|---|
| fingerprint mismatch rate | old/new normalizer가 서로 다른 fingerprint를 만든 비율 | 입력 해석 drift 조기 감지 |
| correction parity mismatch rate | 한쪽은 자동 보정, 다른 쪽은 reject/accept한 비율 | silent correction 차이 분리 |
| rejection reason parity rate | invalid input에 대한 reason code 일치 여부 | API 계약 일관성 확인 |
| cursor comparability sample rate | 같은 normalized contract에서 cursor match verdict가 같은지 | pagination 호환성 확인 |

### 10. normalization version이 바뀌면 cursor와 parity 해석도 같이 버전 관리해야 한다

다음 규칙이 바뀌면 query fingerprint도 사실상 새 계약이 된다.

- blank keyword 처리
- unknown filter reject/drop 정책
- 기본 sort와 direction
- page size cap

이때는 "raw query가 같으니 같은 비교 샘플"이라고 보면 안 된다.  
운영 문서에는 최소한 다음이 같이 남아야 한다.

- normalization version
- normalized query fingerprint
- expected cursor version
- cache key namespace
- old/new verdict와 reason code

즉 normalization 변경은 controller 유틸 수정이 아니라, cursor/cache/dual-read 해석 기준을 함께 바꾸는 contract versioning 문제다.
실제 cutover 절차를 더 좁혀 보면 [Normalization Version Rollout Playbook](./normalization-version-rollout-playbook.md)처럼 cache namespace bump, legacy cursor verdict, public reason-code compatibility를 한 packet으로 같이 적는 편이 운영 해석이 선명하다.

---

## 실전 시나리오

### 시나리오 1: 관리자 주문 검색

keyword blank, status 중복, 정렬 누락을 정규화해 같은 의미의 검색이 같은 결과로 이어지게 할 수 있다.

### 시나리오 2: 검색 결과 캐시

normalized criteria를 key로 써야 캐시 hit가 안정된다.

### 시나리오 3: dual-read 비교

old/new read model 비교 시에도 입력 criteria가 canonical form이어야 parity 차이를 제대로 해석할 수 있다.

### 시나리오 4: 검색 API cutover

검색 인덱스를 새 projection으로 바꾸는 동안 old/new를 동시에 비교한다면, raw query string이 아니라 normalized criteria를 comparison input으로 써야 한다.

- old/new 모두 같은 기본 sort를 적용했는지
- blank/unknown filter 해석이 같은지
- cursor 발급 전 normalized fingerprint가 같은지

이 전제가 깨지면 비교 실패 원인이 projection 차이인지, 입력 해석 차이인지 흐려진다.

### 시나리오 5: 검색 canary의 입력 해석 버킷

`status=PAID&status=SHIPPED`와 `status=SHIPPED&status=PAID`를 raw URL 기준으로 따로 집계하면 parity 대시보드가 noisy해진다.

- 둘 다 같은 normalized fingerprint로 묶고
- page size와 cursor version을 별도 버킷으로 나누고
- `CORRECTED` / `REJECTED` verdict를 함께 보면

실제 projection mismatch와 input normalization drift를 분리해서 해석하기 쉬워진다.

---

## 코드로 보기

```java
public record OrderSearchCriteria(
    List<OrderStatus> statuses,
    String keyword,
    String sortBy,
    SortDirection direction,
    Integer size
) {
    public OrderSearchCriteria normalized() {
        List<OrderStatus> normalizedStatuses = statuses == null ? null : statuses.stream().distinct().sorted().toList();
        String normalizedKeyword = keyword == null || keyword.isBlank() ? null : keyword.trim().toLowerCase();
        String normalizedSort = sortBy == null ? "createdAt" : sortBy;
        SortDirection normalizedDirection = direction == null ? SortDirection.DESC : direction;
        Integer normalizedSize = size == null ? 50 : Math.min(Math.max(size, 1), 100);
        return new OrderSearchCriteria(
            normalizedStatuses,
            normalizedKeyword,
            normalizedSort,
            normalizedDirection,
            normalizedSize
        );
    }

    public String fingerprint() {
        OrderSearchCriteria normalized = normalized();
        return normalized.statuses + "|" + normalized.keyword + "|" + normalized.sortBy + "|" + normalized.direction + "|" + normalized.size;
    }
}
```

```java
// cursor, cache, dual-read compare는 모두 normalized fingerprint를 같은 기준으로 써야 한다.
```

```java
public record SearchParitySampleKey(
    String queryFingerprint,
    String sortBy,
    SortDirection direction,
    int pageSizeBucket,
    int normalizationVersion,
    int cursorVersion
) {}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| raw query 그대로 사용 | 구현이 빠르다 | 같은 의미 질의가 흔들린다 | 간단한 내부 검색 |
| query normalization | 결과/캐시/비교가 안정된다 | canonicalization 규칙 관리가 필요하다 | 필터가 많고 운영 중요도가 높은 검색 |
| raw query string 기준 샘플링 | 구현이 빠르다 | parameter-order noise와 false mismatch가 많다 | 임시 탐색용 로그 |
| 과도한 자동 보정 | 사용자는 편해 보인다 | surprise와 silent semantic change가 생긴다 | 보통 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- canonical form이 필요한 검색에는 normalization을 둔다
- 보정 가능한 것과 거절해야 할 것을 구분한다
- controller별 drift를 막기 위해 중앙화한다
- fingerprint를 cache/cursor/dual-read가 함께 쓰도록 맞춘다
- parity 샘플 버킷은 normalized fingerprint + page size + cursor version으로 고정한다

---

## 꼬리질문

> Q: normalization은 validation과 같은 건가요?
> 의도: reject와 canonicalization의 차이를 보는 질문이다.
> 핵심: 아니다. validation은 막고, normalization은 같은 의미를 같은 입력으로 정리한다.

> Q: 잘못된 범위를 자동으로 고쳐도 되나요?
> 의도: silent correction의 위험을 보는 질문이다.
> 핵심: 경우에 따라 가능하지만 surprise가 크면 reject가 더 낫다.

> Q: 캐시 안 쓰면 normalization이 필요 없나요?
> 의도: normalization의 역할을 캐시에만 한정하지 않는지 본다.
> 핵심: 아니다. 결과 일관성, dual-read 비교, pagination 안정성에도 필요하다.

> Q: raw query string 기준으로 parity 샘플을 묶어도 되나요?
> 의도: transport 표현과 normalized contract를 구분하는지 본다.
> 핵심: 보통 아니다. 의미상 같은 요청은 normalized fingerprint 기준으로 묶는 편이 낫다.

## 한 줄 정리

Search normalization은 Query Object를 canonical form으로 정리해 검색 결과, 캐시, pagination, 비교 검증을 더 안정적으로 만드는 읽기 계약 패턴이다.
