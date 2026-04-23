# Cursor and Pagination Parity During Read-Model Migration

> 한 줄 요약: read-model migration에서 목록 endpoint cutover는 first-page 결과 비교만으로 충분하지 않고, stable sort 계약, legacy cursor verdict, next-page continuity를 함께 고정해야 projection replacement가 안전하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)
> - [Cursor Rollback Packet](./cursor-rollback-packet.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)
> - [Normalization Version Rollout Playbook](./normalization-version-rollout-playbook.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: read model migration pagination parity, projection replacement pagination, list endpoint cutover, cursor invalidation policy, legacy cursor verdict, next page parity, two page continuity, stable sort parity, tie breaker audit, null ordering parity, collation parity, cursor accept reissue reject, pagination rollback trigger, cursor schema migration, projection replacement sort stability, normalization version rollout, reason code compatibility, cache namespace bump, pagination parity sample packet, fingerprint bucket, continuity outcome, cursor rollback packet, rollback cursor ttl, rollback restart reason code

---

## 핵심 개념

상세 endpoint migration은 "같은 id를 조회했을 때 값이 같은가"로 설명되기 쉽다.  
하지만 목록 endpoint는 결과 집합뿐 아니라 **페이지를 넘기는 계약**까지 같이 옮겨야 한다.

- 첫 페이지 key 집합
- stable sort + tie-breaker
- next cursor 발급 방식
- legacy cursor 처리 정책
- page 1 -> cursor -> page 2 continuity
- duplicate/gap 없는지

이 중 하나라도 바뀌면 projection replacement는 데이터는 맞아도 사용자 경험은 달라질 수 있다.

### Retrieval Anchors

- `read model migration pagination parity`
- `projection replacement pagination`
- `list endpoint cutover`
- `cursor invalidation policy`
- `legacy cursor verdict`
- `next page parity`
- `stable sort parity`
- `tie breaker audit`
- `null ordering parity`
- `cursor accept reissue reject`

---

## 깊이 들어가기

### 1. 목록 cutover는 projection 교체가 아니라 page contract 교체다

old/new projection이 같은 row를 담고 있어도 다음이 다르면 cutover 실패다.

- 기본 sort가 다름
- tie-breaker 유무가 다름
- null ordering이 다름
- collation이 다름
- page size cap이 다름
- legacy cursor를 받아들이는 기준이 다름

즉 list endpoint cutover의 비교 단위는 `rows only`가 아니라 `normalized query + sort + cursor contract`다.

### 2. stable sort parity는 `ORDER BY`가 있다는 사실보다 더 강한 체크가 필요하다

projection replacement 전후에 최소한 아래를 표로 맞춰 봐야 한다.

| 항목 | old projection | new projection | 왜 보나 |
|---|---|---|---|
| default sort | 예: `createdAt DESC, id DESC` | 예: `createdAt DESC, id DESC` | 기본 정렬 drift 감지 |
| tie-breaker | 유일키 포함 여부 | 유일키 포함 여부 | page boundary 중복/누락 방지 |
| null ordering | `NULLS LAST` 또는 암묵 규칙 | 실제 동작 | 상단 노출 순서 drift 감지 |
| collation / locale | DB/인덱스별 비교 규칙 | DB/인덱스별 비교 규칙 | 문자열 검색/정렬 순서 drift 감지 |
| mutable sort key | `updatedAt`, `score` 여부 | 동일/변경 | page 사이 재배치 위험 감지 |
| visibility cutoff | watermark/snapshot 기준 | watermark/snapshot 기준 | 늦게 도착한 row로 인한 연속성 붕괴 방지 |

핵심은 "정렬 컬럼 이름이 같다"가 아니라 **같은 입력을 같은 순서 의미로 내보내는가**다.

### 3. cursor 정책은 `ACCEPT` / `REISSUE` / `REJECT` 셋 중 하나로 고정해야 한다

cutover 당일에 가장 위험한 질문은 "예전 cursor를 새 projection이 그냥 받아도 되나?"다.  
이건 런타임에서 즉흥적으로 판단할 문제가 아니다.

| 정책 | 의미 | 언제 쓰나 | 주의점 |
|---|---|---|---|
| `ACCEPT` | legacy cursor를 그대로 읽어 다음 페이지를 제공 | sort/filter/null ordering/collation 계약이 완전히 같을 때 | 가장 좁게 허용해야 한다 |
| `REISSUE` | legacy cursor는 받아들이되, 첫 응답에서 새 version cursor를 다시 발급 | page 1 재시작은 허용되지만 직접 continuity는 보장 못 할 때 | 사용자가 중복 row를 보지 않도록 재시작 의미를 명시해야 한다 |
| `REJECT` | legacy cursor를 명시적으로 거절하고 새 검색을 요구 | sort contract나 index semantics가 바뀌었을 때 | rejection reason code와 클라이언트 재시작 경로가 필요하다 |

기본값은 대개 `REJECT` 또는 제한적 `REISSUE`가 더 안전하다.  
`ACCEPT`는 "안전하다고 증명된 일부 endpoint/sort 조합"에만 남겨 두는 편이 낫다.
특히 normalization version도 같이 바뀌는 cutover라면, [Normalization Version Rollout Playbook](./normalization-version-rollout-playbook.md)처럼 cache namespace와 public reason-code compatibility까지 같은 rollout packet으로 묶어 두지 않으면 `legacy cursor reject`가 client 입장에서는 임의의 API drift처럼 보일 수 있다.

### 4. next-page parity는 2-page chain을 최소 단위로 본다

목록 cutover에서 first-page parity만 보면 놓치는 문제가 많다.

- page 1은 같지만 page 2 경계 row가 다름
- legacy cursor는 decode되지만 second-page ordering이 달라짐
- page size bucket에 따라 중복/누락이 다르게 나타남
- mutable sort key가 between-page 동안 재정렬됨

그래서 sampled dual-read는 최소한 아래 단위를 같이 남긴다.

1. 같은 normalized query로 old/new page 1 조회
2. 각 path가 발급한 next cursor verdict 기록
3. 발급된 cursor로 page 2 조회
4. `page1 ∪ page2` union에서 duplicate/gap 여부 검사

"목록이 비슷하다"가 아니라 `page1 -> next cursor -> page2`가 같은 의미로 이어져야 parity pass다.

### 5. 비교 샘플은 query fingerprint와 page-size bucket이 함께 있어야 해석 가능하다

다음 정보를 안 남기면 mismatch 원인을 운영적으로 설명하기 어렵다.

- normalized query fingerprint
- sort key + direction
- page size bucket (`20`, `50`, `100` 등)
- requested cursor version
- cursor verdict (`ACCEPTED`, `REISSUED`, `REJECTED`)
- first-page key/order mismatch
- second-page continuity mismatch
- duplicate/gap 여부
- stable sort audit result
- rejection reason code

field 이름도 문서마다 새로 만들기보다 [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)의 `fingerprint_bucket`, `cursor_verdict_pair`, `continuity_outcome`을 재사용하는 편이 좋다. 그래야 canary threshold, cutover gate, rollback packet이 같은 sample count를 본다.

stage별로 legacy cursor reuse allowlist, requested/emitted cursor version matrix, `page1 -> page2` 2-page chain floor를 더 구체적으로 운영하려면 [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)처럼 pagination-specific sampling 계약을 따로 두는 편이 안전하다.

특히 `legacy accepted but second-page mismatch`는 가장 위험한 샘플이다.  
겉으로는 호환돼 보이지만 실제로는 cutover 후 페이지 누락/중복 bug를 만든다.

### 6. stable sort audit은 코드 리뷰 체크리스트가 아니라 canary gate에 들어가야 한다

projection replacement는 구현 리뷰만 통과해서는 부족하다.  
운영 gate에 다음 확인이 들어가야 한다.

- supported sort set이 old/new에서 완전히 동일한가
- default sort와 direction이 동일한가
- tie-breaker가 빠진 sort 조합은 없는가
- null ordering/collation이 실제 저장소 동작에서 같은가
- mutable sort key는 snapshot cutoff 또는 재조회 정책을 갖는가
- strict list는 immutable 또는 stronger tie-breaker로 제한됐는가

이 검사가 없으면 canary mismatch를 "왜 그런지 모르지만 몇 건 다르다" 수준으로만 해석하게 된다.

### 7. 목록 fallback도 first page와 next page를 분리해 적어야 한다

list endpoint fallback은 상세 fallback보다 더 조심해야 한다.

- first page만 old projection fallback 허용
- page 2 이후는 legacy cursor 혼합을 막기 위해 `REJECT`
- strict actor-owned list만 fallback 허용
- compare 샘플은 fallback과 별도로 저장

즉 "목록도 old path로 돌린다"가 아니라 **어느 page depth까지, 어떤 cursor policy와 함께** fallback하는지 계약해야 한다.  
이 부분을 안 적으면 old/new cursor가 섞여 rollback path조차 불안정해진다.

### 8. projection replacement 승인 질문은 단순해 보여도 꽤 구체적이어야 한다

cutover 직전에는 최소한 다음 질문이 yes/no로 답돼야 한다.

1. old/new가 같은 normalized query contract를 쓰는가
2. default sort, tie-breaker, null ordering, collation이 같은가
3. legacy cursor policy는 `ACCEPT` / `REISSUE` / `REJECT` 중 무엇인가
4. sampled dual-read가 page 1뿐 아니라 page 2 continuity까지 확인했는가
5. duplicate/gap sample rate와 next-cursor mismatch rate 임계치가 있는가
6. fallback은 first page와 later page에서 같은가, 다른가
7. rollback 시 old cursor와 new cursor를 어떻게 정리하는가

이 체크리스트가 없으면 cutover 중 발견된 mismatch를 "projection 데이터가 틀렸다"와 "pagination contract를 바꿨다"로 구분하지 못한다.

### 9. projection replacement의 rollback은 cursor 세계를 되돌리는 절차까지 포함해야 한다

데이터 path만 old로 되돌려도 cursor 계약을 같이 정리하지 않으면 혼란이 남는다.

- new cursor를 발급한 뒤 old path로 rollback하는 경우
- old cursor를 일부 허용하던 정책을 중단하는 경우
- mobile/web client 캐시에 오래 남은 cursor가 재사용되는 경우

그래서 [Cursor Rollback Packet](./cursor-rollback-packet.md)에는 보통 다음이 들어간다.

- 허용 cursor version 집합
- reject/reissue reason code
- old path 복귀 시 유지할 sort contract
- client restart message 또는 silent restart 여부
- cursor cache TTL 정리 기준

rollback은 "스위치를 되돌렸다"가 아니라 **어느 cursor 세계를 다시 canonical로 볼지**를 재선언하는 일이다.

### 10. 가장 흔한 실패는 정렬 semantics가 살짝 달라졌는데 `ACCEPT`로 남겨 두는 것이다

실무에서 사고는 보통 큰 schema break보다 미묘한 drift에서 난다.

- `createdAt DESC`는 같지만 tie-breaker가 빠짐
- 검색 인덱스가 null 값을 다른 쪽 끝으로 보냄
- 문자열 정렬 규칙이 달라 이름 순서가 바뀜
- `updatedAt` 정렬인데 snapshot cutoff가 없음

이 상황에서 legacy cursor를 `ACCEPT`하면 첫 페이지는 멀쩡해 보여도 다음 페이지부터 중복/누락이 터진다.  
그러므로 "의미가 조금 달라졌지만 웬만하면 호환"은 list cutover에서 가장 위험한 사고 방식이다.

---

## 실전 시나리오

### 시나리오 1: 주문 검색 인덱스를 Elasticsearch 기반 projection으로 교체

row 수와 page 1 결과는 거의 같아도 문자열 collation과 null ordering이 달라 상단 20개가 흔들릴 수 있다.

- stable sort audit에서 locale/collation 차이를 먼저 기록
- legacy cursor는 `REJECT`
- canary는 `size=20/50` 2-page chain 샘플을 따로 본다

### 시나리오 2: 최근 활동 목록을 `updatedAt` 기반 projection으로 재구축

`updatedAt DESC`는 page 사이에 값이 바뀌기 쉬워 continuity가 약하다.

- `updatedAt DESC, id DESC`로 tie-breaker 강화
- snapshot cutoff 또는 requery policy 동반
- actor-owned strict list는 fallback을 first page까지만 허용

### 시나리오 3: old cursor를 받되 new cursor로 재발급하는 점진 전환

mobile client 업데이트가 느려 legacy cursor를 당장 끊을 수 없다고 해 보자.

- old cursor decode는 허용
- response에는 `REISSUED` verdict와 새 version cursor를 포함
- second-page parity가 불안정한 sort/filter 조합은 여전히 `REJECT`
- reissue 허용 범위는 query fingerprint별 allowlist로 제한

핵심은 "부분 호환"을 지원하더라도 전면 호환처럼 보이게 두지 않는 것이다.

---

## 코드로 보기

### cursor verdict packet

```java
public enum LegacyCursorVerdict {
    ACCEPT,
    REISSUE,
    REJECT
}

public record ListCutoverSample(
    String queryFingerprint,
    String sortKey,
    String sortDirection,
    int pageSize,
    int requestedCursorVersion,
    LegacyCursorVerdict legacyCursorVerdict,
    boolean firstPageMatches,
    boolean secondPageMatches,
    boolean duplicateDetected,
    boolean gapDetected,
    String rejectionReasonCode
) {}
```

### stable sort compatibility

```java
public record SortContract(
    String sortKey,
    String direction,
    String tieBreakerKey,
    String nullOrdering,
    String collation
) {
    public boolean isCompatibleWith(SortContract other) {
        return sortKey.equals(other.sortKey)
            && direction.equals(other.direction)
            && tieBreakerKey.equals(other.tieBreakerKey)
            && nullOrdering.equals(other.nullOrdering)
            && collation.equals(other.collation);
    }
}
```

### next-page parity decision

```java
public boolean passesListCutover(ListCutoverSample sample) {
    if (sample.legacyCursorVerdict() == LegacyCursorVerdict.ACCEPT
        && !sample.secondPageMatches()) {
        return false;
    }
    return sample.firstPageMatches()
        && !sample.duplicateDetected()
        && !sample.gapDetected();
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| legacy cursor 전면 `ACCEPT` | 사용자 재시작이 적다 | 미묘한 sort drift를 숨긴다 | sort/collation/null ordering까지 완전히 같은 경우에만 |
| legacy cursor `REISSUE` | 점진 전환이 가능하다 | page continuity 의미가 재시작 중심으로 바뀐다 | client 업데이트 지연을 흡수해야 할 때 |
| legacy cursor `REJECT` | 계약이 명확하고 안전하다 | 사용자가 목록을 다시 시작해야 한다 | projection semantics가 달라졌을 때 기본값 |
| first-page만 비교 | 비용이 낮다 | next-page bug를 놓친다 | shadow smoke 단계 |
| 2-page chain + stable sort audit | cutover 해석이 선명하다 | 계측과 비교 비용이 늘어난다 | 사용자 영향이 큰 목록, 검색, 피드 |

판단 기준은 다음과 같다.

- legacy cursor 호환성보다 stable sort parity를 먼저 증명한다
- `ACCEPT`는 allowlist 방식으로 최소화한다
- canary sample은 page-size bucket과 query fingerprint coverage를 같이 본다
- rollback packet에도 cursor version 정책을 넣는다
- list fallback은 page depth와 cursor policy를 분리해서 적는다

---

## 꼬리질문

> Q: old/new 첫 페이지 key 집합이 같으면 cutover해도 되나요?
> 의도: first-page parity와 next-page continuity를 구분하는지 본다.
> 핵심: 아니다. cursor verdict와 둘째 페이지 연속성까지 확인해야 한다.

> Q: tie-breaker만 추가했는데 legacy cursor를 그대로 받아도 되나요?
> 의도: 정렬 semantics 변경이 cursor 의미를 바꾼다는 점을 이해하는지 본다.
> 핵심: 보통 조심해야 한다. tie-breaker 추가 자체가 cursor contract 변화다.

> Q: legacy cursor를 거절하면 UX가 나빠지지 않나요?
> 의도: 안전한 invalidation과 무리한 compatibility를 비교하는지 본다.
> 핵심: 약간의 재시작 UX보다 중복/누락 bug가 더 위험한 경우가 많다.

> Q: 목록 fallback을 old projection으로 두면 continuity도 자동으로 안전한가요?
> 의도: fallback path와 cursor 혼합 문제를 보는지 본다.
> 핵심: 아니다. 어느 page depth에서 어떤 cursor만 허용하는지 따로 계약해야 한다.

## 한 줄 정리

Read-model migration에서 목록 endpoint cutover는 first-page 결과 비교가 아니라 stable sort, legacy cursor verdict, next-page continuity를 함께 검증하는 pagination contract migration이다.
