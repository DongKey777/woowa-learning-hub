# Normalization Version Rollout Playbook

> 한 줄 요약: normalization version 변경은 검색 유틸 수정이 아니라 read contract cutover이므로, cache namespace bump, cursor invalidation verdict, API reason-code compatibility를 하나의 rollout packet으로 같이 움직여야 안전하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [System Design: Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: normalization version rollout, normalization cutover, search normalization migration, cache namespace bump, normalized query fingerprint version, cursor invalidation playbook, cursor reissue reject, legacy cursor cutoff, reason code compatibility, api reason code parity, normalization rollback plan, cutover packet, normalization canary parity, pagination parity packet schema, fingerprint bucket, continuity outcome

---

## 핵심 개념

정규화 규칙이 바뀌면 보통 다음도 함께 바뀐다.

- normalized query fingerprint
- cache key namespace
- cursor 의미와 허용 범위
- invalid input의 reject/reason code
- dual-read parity 해석 기준

즉 `trim 규칙 하나 바꿨다`, `unknown filter를 drop 대신 reject로 바꿨다`, `default sort를 추가했다` 같은 변경은 controller util refactor가 아니다.  
이건 **검색 API가 같은 입력을 해석하는 기준을 새 버전으로 올리는 cutover**다.

Normalization Version Rollout Playbook은 그 전환을 다음 네 축으로 동시에 다룬다.

1. cache namespace를 어떻게 분리할지
2. legacy cursor를 `ACCEPT` / `REISSUE` / `REJECT` 중 무엇으로 처리할지
3. API reason code를 외부 계약상 어떻게 유지하거나 매핑할지
4. canary와 rollback에서 무엇을 parity packet으로 기록할지

### Retrieval Anchors

- `normalization version rollout`
- `cache namespace bump`
- `cursor invalidation playbook`
- `reason code compatibility`
- `normalized query fingerprint version`
- `legacy cursor cutoff`
- `api reason code parity`
- `normalization rollback plan`
- `normalization canary parity`

---

## 깊이 들어가기

### 1. normalization version bump는 semantic no-op이 아닐 때 선언한다

다음이 바뀌면 normalization version을 올리는 편이 안전하다.

- blank와 `null` 해석
- unknown filter/sort의 drop vs reject 정책
- default sort, default direction
- page size cap
- locale/collation에 영향을 주는 canonicalization
- correction vs rejection 경계

반대로 내부 구현만 바뀌고 canonical output, fingerprint, reject semantics가 그대로면 버전 분리 없이 유지할 수 있다.  
핵심은 코드 diff가 아니라 **동일 raw request가 같은 normalized contract로 남는가**다.

### 2. rollout 단위는 `normalization version packet`이어야 한다

정규화 버전을 올릴 때는 최소한 아래 필드를 한 패킷으로 묶어 문서화하는 편이 좋다.

| 필드 | 왜 필요한가 |
|---|---|
| `normalization_version` | 입력 해석 기준의 주 버전 식별자 |
| `query_fingerprint_salt` | old/new fingerprint 충돌 방지 |
| `cache_namespace` | old/new cache line 분리 |
| `cursor_version_policy` | legacy cursor를 어떻게 자를지 결정 |
| `reason_code_mapping` | 외부 API 계약과 내부 판정의 차이 정리 |
| `parity_bucket_dimensions` | canary에서 무엇을 같은 표본으로 볼지 고정 |
| `rollback_target_version` | 되돌릴 canonical world 선언 |

이 묶음이 없으면 팀마다:

- 캐시는 `v3`로 올렸는데
- cursor는 예전 걸 받고
- reason code는 새 이름으로 바꾸고
- canary는 raw query 기준으로 비교하는

식의 비대칭 cutover가 생긴다.

### 3. cache namespace bump는 선택이 아니라 기본값에 가깝다

normalization version이 바뀌면 같은 raw query가 다른 fingerprint를 만들 수 있다.  
이때 cache namespace를 나누지 않으면 가장 먼저 해석이 꼬인다.

| 상황 | cache namespace를 분리해야 하는 이유 |
|---|---|
| blank -> `null` 정책 변경 | 같은 URL이 이전과 다른 cache key에 묶여야 한다 |
| unknown filter reject 도입 | old cache에는 성공 응답, new path에는 4xx가 섞일 수 있다 |
| default sort 추가 | cached page 1 자체가 다른 ordering 의미를 가질 수 있다 |
| page size cap 조정 | 같은 요청이라도 cursor/cache alignment가 깨질 수 있다 |

안전한 기본값은 다음에 가깝다.

- read cache prefix를 `search:v2:` -> `search:v3:`로 분리
- compare/shadow 단계에서는 old/new namespace를 동시에 관찰
- new namespace는 canary 동안 warm-up하되 old hit를 재사용하지 않음
- rollback 시 다시 canonical namespace를 명시적으로 되돌림

핵심은 **cache reuse보다 semantic contamination 방지**가 우선이라는 점이다.

### 4. cursor invalidation은 normalization drift가 있으면 보수적으로 본다

정규화 버전이 바뀌었는데도 legacy cursor를 그대로 받으면, cursor가 기대하는 query contract와 현재 contract가 어긋날 수 있다.

| 변화 종류 | 권장 cursor verdict | 이유 |
|---|---|---|
| canonical output 완전 동일 | 제한적 `ACCEPT` 가능 | cursor가 기대하는 sort/filter 의미가 유지된다 |
| default sort 추가, page size cap 조정 | 보통 `REISSUE` | 첫 응답은 재시작시킬 수 있어도 continuity는 새 기준으로 다시 잡아야 한다 |
| unknown filter drop -> reject, blank -> null, correction -> reject | 기본 `REJECT` | cursor를 발급한 입력 세계와 현재 세계가 다르다 |
| filter alias 제거, collation 변경 | 기본 `REJECT` | same row set을 보장하기 어렵다 |

`ACCEPT`는 "decode가 된다"가 아니라 **동일 normalized contract가 증명된다**는 뜻이어야 한다.  
애매하면 `REISSUE`나 `REJECT`가 더 안전하다.

### 5. reason code compatibility는 cursor verdict와 별도 축으로 관리한다

운영 중 흔한 실수는 새 normalizer가 더 정교해졌다는 이유로 reason code까지 같이 갈아엎는 것이다.  
하지만 client는 cursor invalidation보다 reason code 안정성에 더 민감할 수 있다.

예를 들어 내부 판정은 이렇게 늘어날 수 있다.

- `LEGACY_CURSOR_VERSION`
- `NORMALIZATION_RULE_CHANGED`
- `UNSUPPORTED_FILTER_ALIAS`
- `PAGE_SIZE_CAP_CHANGED`

그런데 외부 API 계약은 당장 이렇게만 유지해야 할 수 있다.

- `INVALID_CURSOR`
- `INVALID_QUERY`

이때 필요한 건 **이름 바꾸기**가 아니라 **호환 매핑 표**다.

| internal verdict / reason | external reason code | 왜 필요한가 |
|---|---|---|
| `LEGACY_CURSOR_VERSION` | `INVALID_CURSOR` | 기존 client 재시도 흐름 유지 |
| `NORMALIZATION_RULE_CHANGED` | `INVALID_QUERY` 또는 기존 alias | 앱이 새 분기 없이 재시작/수정 경로를 탈 수 있게 함 |
| `UNSUPPORTED_FILTER_ALIAS` | 기존 `INVALID_FILTER` | rollout 동안 분석 granularity와 public contract를 분리 |

즉 canary는 internal reason을 자세히 보더라도, public response는 당분간 호환 code를 유지할 수 있어야 한다.

### 6. parity packet은 결과 차이보다 해석 차이를 먼저 드러내야 한다

normalization version rollout canary에서는 "row가 같냐"보다 아래를 먼저 남겨야 한다.

| 필드 | 보는 질문 |
|---|---|
| `old_normalization_version`, `new_normalization_version` | 지금 어떤 해석 세계를 비교 중인가 |
| `old_fingerprint`, `new_fingerprint` | 입력 해석이 이미 달라졌는가 |
| `cache_namespace_old`, `cache_namespace_new` | cache 오염 없이 관찰 중인가 |
| `legacy_cursor_verdict` | old cursor를 새 기준에서 어떻게 봤는가 |
| `external_reason_code_old/new` | 클라이언트가 체감하는 API 계약이 달라졌는가 |
| `internal_reason_code_old/new` | drift 원인이 무엇인가 |
| `first_page_matches`, `second_page_matches` | pagination parity까지 유지되는가 |

pagination/list endpoint canary라면 이 parity packet을 [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)의 `fingerprint_bucket`, `cursor_verdict_pair`, `continuity_outcome`으로 좁혀 두는 편이 좋다. 그래야 normalization rollout 문서와 pagination cutover 문서가 같은 sample counter를 공유한다.

이 패킷이 있어야 mismatch를 다음처럼 분리할 수 있다.

- 데이터 차이
- 입력 해석 차이
- cache reuse 오염
- cursor world 변경
- API reason-code drift

### 7. rollout 단계도 cache, cursor, reason code를 같은 순서로 움직여야 한다

| 단계 | 해야 하는 일 | 막아야 하는 사고 |
|---|---|---|
| `PREPARE` | version packet 작성, cache namespace 예약, public reason-code compatibility 표 확정 | 코드만 배포되고 운영 계약이 비어 있는 상태 |
| `SHADOW` | raw request를 old/new normalizer에 동시에 태우고 fingerprint/reason drift 측정 | 결과 차이를 데이터 문제로 오해 |
| `CANARY` | new namespace warm-up, legacy cursor verdict 샘플링, public reason-code parity 감시 | cache hit만 보고 안전하다고 착각 |
| `PRIMARY` | new normalization version을 canonical로 승격, legacy cursor policy 적용 | 일부 노드만 옛 namespace/옛 reason code 사용 |
| `ROLLBACK WINDOW` | old packet을 즉시 복구 가능 상태로 유지 | rollback 시 cache/cursor/API 계약이 따로 움직이는 상태 |

특히 `SHADOW`와 `CANARY` 사이에는 다음 질문이 yes여야 한다.

1. new fingerprint drift가 의도된 범위 안인가
2. legacy cursor 정책이 endpoint별로 고정됐는가
3. public reason code 변화가 클라이언트에 허용되는가
4. new cache namespace가 충분히 warm-up됐는가

### 8. rollback은 코드 되돌리기가 아니라 canonical world 재선언이다

normalization rollout을 되돌릴 때는 다음을 같이 정리해야 한다.

- canonical normalization version
- canonical cache namespace
- 허용 cursor version 집합
- public reason-code mapping
- compare dashboard에서 canonical로 보는 fingerprint salt

이 중 하나라도 남겨 두면 rollback 뒤에도:

- new cursor가 섞여 재시작 에러가 나고
- old cache 대신 new namespace를 계속 읽고
- public reason code가 새 이름으로 남아
- 운영자는 rollback이 끝났다고 생각하지만 client는 다른 세계를 본다

즉 rollback checklist는 "앱을 되돌렸다"보다 **어느 해석 계약을 다시 정답으로 볼지 선언했는가**를 묻는 편이 맞다.

### 9. 가장 흔한 실패는 세 축 중 하나만 versioning하는 것이다

실전 실패 패턴은 대개 아래 셋이다.

| 실패 패턴 | 왜 위험한가 | 더 안전한 기본값 |
|---|---|---|
| cache namespace는 그대로 두고 normalizer만 교체 | old/new semantic cache contamination | namespace bump 기본 적용 |
| cursor는 유지하고 reject policy만 바꿈 | page 2에서 surprise rejection 또는 silent drift | cursor verdict를 version packet에 명시 |
| internal reason code를 그대로 public에 노출 | client retry/CTA contract가 깨짐 | public compatibility table 유지 |

즉 normalization rollout의 핵심은 "더 똑똑한 정규화"가 아니라 **서로 다른 semantic world를 섞지 않는 것**이다.

---

## 실전 시나리오

### 시나리오 1: 주문 검색에서 blank keyword를 `null`로 통일

기존에는 `"   "`를 keyword로 보고 새 버전은 `null`로 본다고 하자.

- fingerprint가 달라질 수 있으므로 cache namespace를 분리한다
- legacy cursor는 보통 `REJECT`가 안전하다
- public reason code는 기존 `INVALID_QUERY`를 유지하고 내부적으로만 `NORMALIZATION_RULE_CHANGED`를 쓴다

### 시나리오 2: unknown filter를 drop에서 reject로 변경

old는 `foo=bar`를 무시했지만 new는 400으로 거절한다.

- old cache 재사용을 끊는다
- shadow 단계에서 rejection reason drift를 bucket으로 본다
- client가 이미 `INVALID_FILTER`를 처리한다면 public code는 유지하고 internal code만 세분화한다

### 시나리오 3: default sort를 `createdAt DESC`로 고정

전에는 controller마다 sort default가 달랐고, 이제 중앙 normalizer가 기본 sort를 넣는다고 하자.

- cache namespace bump
- cursor는 기본 `REISSUE` 또는 `REJECT`
- pagination canary는 `page1 -> page2` continuity와 reason-code parity를 함께 본다

---

## 코드로 보기

```java
public enum LegacyCursorVerdict {
    ACCEPT,
    REISSUE,
    REJECT
}

public record NormalizationVersionPacket(
    int normalizationVersion,
    String queryFingerprintSalt,
    String cacheNamespace,
    LegacyCursorVerdict defaultLegacyCursorVerdict,
    Map<String, String> publicReasonCodeMap
) {}
```

```java
public record NormalizationCutoverSample(
    String rawQueryHash,
    int oldNormalizationVersion,
    int newNormalizationVersion,
    String oldFingerprint,
    String newFingerprint,
    String oldCacheNamespace,
    String newCacheNamespace,
    LegacyCursorVerdict legacyCursorVerdict,
    String oldInternalReasonCode,
    String newInternalReasonCode,
    String oldExternalReasonCode,
    String newExternalReasonCode,
    boolean firstPageMatches,
    boolean secondPageMatches
) {}
```

```java
public boolean canAcceptLegacyCursor(
    boolean sameNormalizedContract,
    boolean sameSortContract,
    boolean sameReasonCodeBehavior
) {
    return sameNormalizedContract && sameSortContract && sameReasonCodeBehavior;
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| cache namespace bump + legacy cursor `REJECT` | 가장 해석이 선명하다 | 재시작 UX와 cache warm-up 비용이 든다 | semantic drift가 분명할 때 기본값 |
| cache namespace bump + legacy cursor `REISSUE` | 점진 전환이 가능하다 | continuity 의미가 재시작 중심이 된다 | first response에서 새 cursor로 유도할 때 |
| legacy cursor 제한적 `ACCEPT` | 사용자 마찰이 적다 | semantic drift를 과소평가하기 쉽다 | normalized contract가 완전히 같다고 증명된 일부 조합 |
| public reason code도 새로 교체 | 분석 granularity가 높다 | client contract를 동시에 바꿔야 한다 | 클라이언트가 함께 배포되고 명시적 합의가 있을 때 |
| public reason code 호환 유지 | cutover 위험이 낮다 | 서버 내부와 외부 code 의미가 분리된다 | rollout 동안 안전성을 우선할 때 |

판단 기준은 다음과 같다.

- semantic drift가 조금이라도 있으면 cache namespace는 분리한다
- cursor 호환성은 decode 가능성보다 contract 동일성을 기준으로 본다
- public reason code는 internal classification과 분리해서 관리한다
- canary packet에 fingerprint, cache namespace, cursor verdict, reason code를 모두 남긴다

---

## 꼬리질문

> Q: normalization version만 올리고 cache prefix는 그대로 둬도 되나요?
> 의도: semantic drift와 cache contamination을 구분하는지 본다.
> 핵심: 보통 아니다. 같은 raw query가 다른 meaning을 가지면 namespace도 같이 끊는 편이 안전하다.

> Q: legacy cursor가 decode되면 `ACCEPT`해도 되나요?
> 의도: decode 가능성과 contract 동일성을 구분하는지 본다.
> 핵심: 아니다. normalized filter/sort/reason semantics가 같아야 한다.

> Q: internal reason code를 더 자세히 만들었는데 public code도 바로 바꿔야 하나요?
> 의도: 운영 분석과 client contract를 분리하는지 본다.
> 핵심: 꼭 그렇지 않다. rollout 동안은 compatibility map을 두는 편이 더 안전하다.

## 한 줄 정리

Normalization version rollout은 search input을 더 예쁘게 다듬는 작업이 아니라 cache, cursor, API reason-code, parity 해석을 함께 버전업하는 read contract cutover다.
