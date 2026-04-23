# Dual-Read Pagination Parity Sample Packet Schema

> 한 줄 요약: dual-read pagination check는 normalized query bucket, baseline/candidate cursor verdict, `page1 -> page2` continuity outcome을 한 packet으로 남겨야 canary, cutover, rollback이 같은 증거 언어를 쓴다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Normalization Version Rollout Playbook](./normalization-version-rollout-playbook.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Projection Canary Cohort Selection](./projection-canary-cohort-selection.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)
> - [Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: dual read pagination parity packet, pagination parity sample packet, canonical compare packet, fingerprint bucket, query fingerprint coverage, page size bucket, cursor verdict pair, continuity outcome, page chain parity metrics, duplicate gap outcome, order drift outcome, restart expected outcome, pagination observability schema, projection cutover packet, cursor parity metrics, pagination canary packet, page1 page2 continuity packet, pagination parity bucket, query fingerprint bucket selection, canary cohort bucket, strict path bucket, representative bucket

---

## 핵심 개념

pagination cutover 문서는 보통 각자 필요한 샘플 필드만 적는다.

- normalization 문서는 query fingerprint를 강조하고
- cursor 문서는 verdict와 continuity를 강조하고
- canary 문서는 bucket coverage와 sample floor를 강조한다

이렇게 되면 같은 dual-read sample이어도 문서마다 packet shape와 metric 이름이 달라져서, 운영자가 `이 mismatch가 input drift인지`, `cursor policy drift인지`, `진짜 continuity break인지`를 한 번에 읽기 어렵다.

이 문서는 dual-read pagination verify에서 재사용할 **canonical packet schema**를 정의한다. 이 packet은 최소한 세 질문에 같은 답을 주어야 한다.

1. 이 sample은 어떤 **fingerprint bucket**에 속하는가
2. baseline/candidate가 어떤 **cursor verdict**를 냈는가
3. `page1 -> page2` chain은 어떤 **continuity outcome**으로 끝났는가

### Retrieval Anchors

- `dual read pagination parity packet`
- `fingerprint bucket`
- `cursor verdict pair`
- `continuity outcome`
- `page chain parity metrics`
- `pagination observability schema`
- `projection cutover packet`

---

## 깊이 들어가기

### 1. packet은 로그 줄이 아니라 "한 chain의 판정 단위"여야 한다

이 packet의 최소 단위는 "같은 normalized query로 baseline/candidate를 읽고, 필요하면 page 2까지 따라간 한 번의 chain"이다.

즉 packet 하나는 보통 아래를 함께 묶는다.

- 동일 endpoint
- 동일 actor/query scope
- 동일 page-size bucket
- 동일 requested cursor version
- baseline path와 candidate path의 verdict
- `page1 -> next cursor -> page2` 결과

page 1만 기록하고 page 2를 다른 이벤트로 남기면 continuity outcome을 나중에 다시 재조립해야 해서, duplicate/gap 해석이 자주 틀어진다.

### 2. identity / routing 필드는 sample의 "운영 세계"를 고정한다

| 필드 | 의미 | 왜 필요한가 |
|---|---|---|
| `sample_id` | 한 chain 전체를 식별하는 고유 ID | page 1과 page 2 관측을 같은 sample로 묶는다 |
| `observed_at` | sample 수집 시각 | canary stage와 lag window를 맞춰 본다 |
| `endpoint_id` | 어떤 list/search endpoint인지 | 다른 목록 contract와 섞이지 않게 한다 |
| `compare_mode` | `SHADOW`, `CANARY`, `PRIMARY_VERIFY`, `ROLLBACK_VERIFY` | stage별 허용 outcome을 다르게 해석한다 |
| `chain_route` | `PRIMARY_PRIMARY`, `FALLBACK_REISSUE`, `FALLBACK_PINNED`, `WRITE_MODEL_FALLBACK` 등 | fallback chain과 canonical chain을 분리한다 |
| `actor_scope` | `self`, `tenant`, `global` 등 | strict list와 일반 search를 같은 표본으로 보지 않게 한다 |

`compare_mode`와 `chain_route`가 빠지면 `REISSUE`가 의도된 restart인지, 아니면 drift인지 구분이 안 된다.

### 3. query shape는 baseline/candidate 둘 다 남기되, rollup은 one canonical bucket으로 모은다

| 필드 | 의미 | 왜 필요한가 |
|---|---|---|
| `baseline_shape.normalization_version` | baseline query contract version | version drift 구분 |
| `candidate_shape.normalization_version` | candidate query contract version | rollout/rollback 해석 |
| `baseline_shape.query_fingerprint` | baseline normalized query fingerprint | input parity 원인 추적 |
| `candidate_shape.query_fingerprint` | candidate normalized query fingerprint | same |
| `baseline_shape.sort_family` | 예: `createdAt:DESC:id` | sort semantics drift 추적 |
| `candidate_shape.sort_family` | same | same |
| `baseline_shape.page_size_bucket` | 예: `20`, `50`, `100+` | page boundary 문제를 size별로 본다 |
| `candidate_shape.page_size_bucket` | same | same |
| `baseline_shape.requested_cursor_version` | 요청에 들어온 cursor version | legacy world 해석 |
| `candidate_shape.requested_cursor_version` | same | same |
| `fingerprint_bucket` | coverage와 mismatch rollup에 쓰는 canonical bucket key | 문서와 대시보드가 같은 집계 키를 쓰게 한다 |

`fingerprint_bucket`는 raw hash 하나로 끝내지 않는 편이 낫다.  
안전한 기본값은 아래처럼 **해석에 필요한 축을 함께 넣은 문자열 bucket**이다.

`norm:{baseline}->{candidate}|fp:{baseline_fp}->{candidate_fp}|sort:{sort_family}|size:{page_size_bucket}`

baseline/candidate fingerprint가 같다면 `a->a`처럼 남고, drift면 `a->b`처럼 남는다.  
이렇게 해야 coverage와 drift를 같은 키 체계로 읽을 수 있다.

### 4. cursor observation은 양쪽 verdict와 emitted version을 모두 남겨야 한다

| 필드 | 의미 | 왜 필요한가 |
|---|---|---|
| `baseline_cursor.verdict` | baseline path verdict (`ACCEPT`, `REISSUE`, `REJECT`) | baseline policy 확인 |
| `candidate_cursor.verdict` | candidate path verdict | drift 또는 intended change 확인 |
| `baseline_cursor.emitted_version` | baseline이 응답에 실어 준 cursor version | reissue 결과 추적 |
| `candidate_cursor.emitted_version` | candidate emitted version | same |
| `baseline_cursor.reason_code` | baseline reject/reissue reason code | client-visible drift 설명 |
| `candidate_cursor.reason_code` | candidate reason code | same |
| `cursor_verdict_pair` | 예: `ACCEPT->REISSUE` | metric rollup과 alert 기준의 핵심 축 |

이 문서의 canonical verdict 토큰은 `ACCEPT`, `REISSUE`, `REJECT`다.  
기존 문서나 코드가 `ACCEPTED`, `REISSUED`, `REJECTED`를 쓰더라도 metric layer에서는 위 세 값으로 normalize하는 편이 좋다.

### 5. continuity outcome은 page 결과 booleans와 별도 enum으로 남긴다

page-level booleans는 root cause를 설명하고, `continuity_outcome`은 rollup과 alert를 단순화한다.

| 필드 | 의미 | 왜 필요한가 |
|---|---|---|
| `page_parity.first_page_key_match` | page 1 key set 일치 여부 | 초기 결과 집합 drift 탐지 |
| `page_parity.first_page_order_match` | page 1 순서 일치 여부 | sort/collation drift 탐지 |
| `page_parity.second_page_key_match` | page 2 key set 일치 여부 | next-page parity 확인 |
| `page_parity.second_page_order_match` | page 2 순서 일치 여부 | tie-breaker 또는 mutable sort drift 탐지 |
| `page_parity.duplicate_detected` | `page1 ∪ page2`에서 duplicate 발생 | pagination bug 직접 신호 |
| `page_parity.gap_detected` | union에서 gap 발생 | same |
| `page_parity.continuity_outcome` | canonical outcome enum | 대시보드와 승격 gate 단순화 |

canonical `continuity_outcome`은 아래 값을 쓴다.

| 값 | 뜻 | 기본 해석 |
|---|---|---|
| `PASS` | page 1, page 2, verdict가 기대와 일치 | green |
| `RESTART_EXPECTED` | `REISSUE` 또는 `REJECT`가 의도된 정책이고 restart가 정상이었음 | cursor-policy green, continuity pass와는 별도 |
| `VERDICT_DRIFT` | verdict pair가 예상 policy와 다름 | cursor policy regression |
| `ORDER_DRIFT` | key set은 같지만 order semantics가 흔들림 | stable sort audit failure |
| `DUPLICATE_OR_GAP` | union에서 duplicate 또는 gap 발견 | high severity pagination break |
| `INPUT_DRIFT` | normalized contract가 달라 bucket이 갈라짐 | normalization 또는 contract regression |
| `UNKNOWN` | sample이 불완전해 판정 불가 | metric 누락을 숨기지 않음 |

`DUPLICATE`와 `GAP`은 booleans로 따로 보존하고, rollup outcome은 `DUPLICATE_OR_GAP`로 묶는 편이 dashboard 해석이 쉽다.  
세부 triage는 booleans와 row diff에서 내려가면 된다.

### 6. outcome precedence를 고정하면 문서마다 다른 counting을 막을 수 있다

하나의 sample에 여러 신호가 함께 나올 수 있으므로 precedence가 필요하다.  
안전한 기본값은 아래와 같다.

1. query contract가 달라졌으면 `INPUT_DRIFT`
2. verdict pair가 예상 policy와 다르면 `VERDICT_DRIFT`
3. 정책상 restart가 의도됐다면 `RESTART_EXPECTED`
4. duplicate 또는 gap이 있으면 `DUPLICATE_OR_GAP`
5. key set은 같고 order만 다르면 `ORDER_DRIFT`
6. page 1과 page 2가 기대대로 이어지면 `PASS`
7. 나머지는 `UNKNOWN`

핵심은 `REISSUE`를 자동 failure로 세지 않는 대신, `PASS`와는 분리해서 카운트하는 것이다.

### 7. metric rollup도 packet에서 바로 파생되게 정의한다

| Rollup metric | 계산 기준 | 왜 필요한가 |
|---|---|---|
| `fingerprint_bucket_coverage` | `count(distinct fingerprint_bucket)` | stage가 대표 query shape를 충분히 봤는지 확인 |
| `cursor_verdict_pair_rate` | `group by cursor_verdict_pair` | legacy acceptance/reissue/reject drift 감지 |
| `continuity_pass_rate` | `continuity_outcome = PASS` 비율 | strict continuity green signal |
| `restart_expected_rate` | `continuity_outcome = RESTART_EXPECTED` 비율 | restart-based migration 상태 확인 |
| `verdict_drift_rate` | `continuity_outcome = VERDICT_DRIFT` 비율 | policy regression alert |
| `duplicate_or_gap_rate` | `duplicate_detected || gap_detected` 비율 | 가장 직접적인 pagination correctness metric |
| `order_drift_rate` | `continuity_outcome = ORDER_DRIFT` 비율 | sort audit failure 노출 |
| `unknown_outcome_rate` | `continuity_outcome = UNKNOWN` 비율 | observability blind spot 확인 |

stage 해석은 다를 수 있지만, metric 이름은 packet에서 고정하는 편이 좋다.  
예를 들어 `CANARY`에서는 `RESTART_EXPECTED`가 허용될 수 있어도, `PRIMARY_VERIFY`에서는 별도 approval 없이는 green으로 섞지 않는 식이다.

이 canonical packet을 실제 projection canary stage의 quota와 stop signal로 옮길 때는 [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)처럼 legacy reuse allowlist, requested/emitted version matrix, 2-page chain floor를 추가로 고정해 두는 편이 좋다.

이 rollup은 [Projection Canary Cohort Selection](./projection-canary-cohort-selection.md)에서 말하는 `LOW_RISK_SEED`, `REP_CORE`, `STRICT_SENTINEL`, `TAIL_SENTINEL` bucket selection의 입력으로 그대로 재사용하는 편이 좋다.

### 8. related docs는 packet의 서로 다른 단면만 참조해야 한다

이 schema를 기준점으로 두면 문서 역할이 분리된다.

- [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)은 `baseline/candidate query_fingerprint`, `fingerprint_bucket`, `page_size_bucket`을 해석한다.
- [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)은 `cursor_verdict_pair`, `second_page_order_match`, `continuity_outcome`을 본다.
- [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)은 full packet을 cutover gate로 쓴다.
- [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)은 `chain_route`와 `RESTART_EXPECTED` 또는 `VERDICT_DRIFT` 해석을 본다.
- [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)은 `fingerprint_bucket_coverage`, `cursor_verdict_pair_rate`, `duplicate_or_gap_rate`를 sample floor와 stop trigger에 연결한다.

즉 각 문서는 자기 concern을 설명하되, packet shape 자체는 여기서 재사용하는 편이 drift를 줄인다.

### 9. packet에서 빠지면 안 되는 축이 몇 개 있다

다음 omission은 운영 해석을 거의 항상 망친다.

- `page_size_bucket` 없이 continuity mismatch만 집계
- `cursor_verdict_pair` 없이 second-page mismatch만 집계
- `chain_route` 없이 fallback chain과 canonical chain을 합산
- `UNKNOWN` bucket 없이 failed compare를 조용히 drop
- baseline/candidate reason code 없이 `REJECT`만 기록

이 다섯 개가 빠지면 "왜 틀렸는지"보다 "뭔가 틀린 것 같다"만 남는다.

### 10. 실전 packet 예시는 작아 보여도 세 축을 모두 담아야 한다

시나리오: 검색 projection canary에서 `createdAt DESC` 목록을 `size=20`으로 비교한다고 하자.

- baseline/candidate fingerprint가 같고
- baseline verdict는 `ACCEPT`
- candidate verdict는 `REISSUE`
- page 1 rows는 같지만 continuity는 restart 기반으로 바뀜

이 sample은 `first_page_match=true`라도 `PASS`가 아니라 `RESTART_EXPECTED` 또는 `VERDICT_DRIFT`로 남아야 한다.  
그래야 팀이 "row는 같으니 safe"라고 잘못 승격하지 않는다.

---

## 코드로 보기

```java
public enum CursorVerdict {
    ACCEPT,
    REISSUE,
    REJECT
}

public enum ContinuityOutcome {
    PASS,
    RESTART_EXPECTED,
    VERDICT_DRIFT,
    ORDER_DRIFT,
    DUPLICATE_OR_GAP,
    INPUT_DRIFT,
    UNKNOWN
}

public record QueryShape(
    int normalizationVersion,
    String queryFingerprint,
    String sortFamily,
    String pageSizeBucket,
    int requestedCursorVersion
) {}

public record CursorObservation(
    CursorVerdict verdict,
    Integer emittedVersion,
    String reasonCode
) {}

public record PageParityObservation(
    boolean firstPageKeyMatch,
    boolean firstPageOrderMatch,
    boolean secondPageKeyMatch,
    boolean secondPageOrderMatch,
    boolean duplicateDetected,
    boolean gapDetected,
    ContinuityOutcome continuityOutcome
) {}

public record PaginationParityPacket(
    String sampleId,
    Instant observedAt,
    String endpointId,
    String compareMode,
    String chainRoute,
    String actorScope,
    QueryShape baselineShape,
    QueryShape candidateShape,
    String fingerprintBucket,
    CursorObservation baselineCursor,
    CursorObservation candidateCursor,
    PageParityObservation pageParity
) {
    public String cursorVerdictPair() {
        return baselineCursor.verdict() + "->" + candidateCursor.verdict();
    }
}
```

```java
public ContinuityOutcome classify(PaginationParityPacket packet, String expectedVerdictPair) {
    if (!packet.baselineShape().queryFingerprint().equals(packet.candidateShape().queryFingerprint())) {
        return ContinuityOutcome.INPUT_DRIFT;
    }
    if (!packet.cursorVerdictPair().equals(expectedVerdictPair)) {
        return ContinuityOutcome.VERDICT_DRIFT;
    }
    if (packet.candidateCursor().verdict() != CursorVerdict.ACCEPT) {
        return ContinuityOutcome.RESTART_EXPECTED;
    }
    if (packet.pageParity().duplicateDetected() || packet.pageParity().gapDetected()) {
        return ContinuityOutcome.DUPLICATE_OR_GAP;
    }
    if (!packet.pageParity().firstPageOrderMatch() || !packet.pageParity().secondPageOrderMatch()) {
        return ContinuityOutcome.ORDER_DRIFT;
    }
    if (packet.pageParity().firstPageKeyMatch() && packet.pageParity().secondPageKeyMatch()) {
        return ContinuityOutcome.PASS;
    }
    return ContinuityOutcome.UNKNOWN;
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| doc마다 ad-hoc sample field 사용 | 각 문서가 지금 필요한 설명은 빠르다 | dashboard, canary, rollback 용어가 갈라진다 | 피하는 편이 좋다 |
| canonical packet + doc별 단면 해석 | field와 drift 해석이 통일된다 | 처음엔 field 수가 많아 보인다 | pagination cutover 운영 문서 전반 |
| `REISSUE`를 전부 failure로 집계 | rule이 단순하다 | intended restart migration을 과대경보한다 | 거의 권장하지 않음 |
| `RESTART_EXPECTED`를 `PASS`와 분리 | cursor 정책 변화와 continuity green을 구분한다 | dashboard가 한 축 더 필요하다 | version rollout, strict pagination fallback |
| `UNKNOWN` sample 보존 | blind spot을 숨기지 않는다 | metric이 덜 예뻐 보인다 | 운영 신뢰성을 우선할 때 |

## 꼬리질문

> Q: first page 결과만 같으면 `PASS`로 쳐도 되나요?
> 의도: packet 단위가 page chain인지 보는 질문.
> 핵심: 아니다. cursor verdict와 second-page continuity가 같이 남아야 한다.

> Q: `REISSUE`는 항상 실패인가요?
> 의도: cursor policy change와 correctness bug를 구분하는지 본다.
> 핵심: 아니다. 의도된 restart면 `RESTART_EXPECTED`로 분리해서 센다.

> Q: duplicate와 gap을 왜 boolean과 outcome 둘 다 남기나요?
> 의도: rollup과 triage 레이어를 분리하는지 본다.
> 핵심: booleans는 root cause drilldown용이고, outcome은 승격과 알림용 집계 축이다.

## 한 줄 정리

dual-read pagination parity는 query fingerprint bucket, cursor verdict pair, continuity outcome을 한 packet으로 고정할 때만 canary, cutover, rollback이 같은 증거 언어를 쓴다.
