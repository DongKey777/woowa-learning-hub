---
schema_version: 3
title: Legacy Cursor Reissue API Surface
concept_id: design-pattern/legacy-cursor-reissue-api-surface
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- legacy-cursor-reissue
- pagination-restart-envelope
- cursor-api-contract
aliases:
- legacy cursor reissue api surface
- reissue response shape
- reject response shape
- pagination restart envelope
- cursor restart metadata
- page1 restart response
- clear cursor and restart
- served page depth reset
- requested emitted cursor version
- cursor verdict api contract
symptoms:
- legacy cursor를 REISSUE했지만 response에 served_page_depth=1과 restart block이 없어 client가 page N 뒤에 row를 append한다
- REJECT를 generic INVALID_CURSOR로만 내려 canary metric과 client가 restart required boundary를 구분하지 못한다
- requested cursor world와 served cursor world, requested/emitted cursor version을 response shape에서 분리하지 않는다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/strict-pagination-fallback-contracts
- design-pattern/cursor-compatibility-sampling-cutover
- design-pattern/cursor-rollback-packet
next_docs:
- design-pattern/dual-read-pagination-parity-sample-packet-schema
- design-pattern/pinned-legacy-chain-risk-budget
- design-pattern/read-model-cutover-guardrails
linked_paths:
- contents/design-pattern/strict-pagination-fallback-contracts.md
- contents/design-pattern/cursor-pagination-parity-read-model-migration.md
- contents/design-pattern/cursor-compatibility-sampling-cutover.md
- contents/design-pattern/cursor-rollback-packet.md
- contents/design-pattern/dual-read-pagination-parity-sample-packet-schema.md
- contents/design-pattern/normalization-version-rollout-playbook.md
- contents/design-pattern/read-model-cutover-guardrails.md
confusable_with:
- design-pattern/cursor-rollback-packet
- design-pattern/cursor-compatibility-sampling-cutover
- design-pattern/strict-pagination-fallback-contracts
- design-pattern/pinned-legacy-chain-risk-budget
forbidden_neighbors: []
expected_queries:
- Legacy cursor REISSUE response는 continuation success가 아니라 page1 restart success라는 사실을 어떻게 API surface에 드러내?
- REISSUE 응답에 requested_page_depth와 served_page_depth를 분리해서 내려야 client가 append를 멈추는 이유가 뭐야?
- REJECT problem envelope에도 pagination_contract restart metadata를 유지해야 하는 이유가 뭐야?
- requested_cursor_version, emitted_cursor_version, verdict, reason_code를 HTTP status와 분리해야 cutover metrics가 안정되는 이유가 뭐야?
- REISSUE는 success일 수 있지만 continuity outcome은 RESTART_EXPECTED로 세야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Legacy Cursor Reissue API Surface playbook으로, pagination cutover에서
  legacy cursor를 REISSUE/REJECT할 때 response envelope에 verdict, reason_code,
  requested/served page depth, requested/emitted cursor version, restart block, clear cached
  cursor contract를 명시해 client와 observability가 page1 restart boundary를 같은 의미로 읽게 하는 방법을 설명한다.
---
# Legacy Cursor Reissue API Surface

> 한 줄 요약: pagination cutover에서 legacy cursor를 `REISSUE`/`REJECT`로 처리할 때는 단순 `INVALID_CURSOR`나 generic `next_cursor`로 숨기지 말고, 응답이 page `N` continuation이 아니라 page `1` restart boundary라는 사실을 response shape에 명시해야 client, observability, canary 해석이 모두 일치한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)
> - [Cursor Rollback Packet](./cursor-rollback-packet.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Normalization Version Rollout Playbook](./normalization-version-rollout-playbook.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)

retrieval-anchor-keywords: legacy cursor reissue api surface, reissue response shape, reject response shape, pagination restart envelope, cursor restart metadata, page1 restart response, clear cursor and restart, served page depth reset, requested emitted cursor version, cursor verdict api contract, cutover explicit restart, silent page1 restart once, invalid cursor restart contract, cursor boundary response, restart required block, page depth reset contract, reissue success envelope, reject problem envelope, restart expected outcome

---

## 핵심 개념

pagination cutover에서 legacy cursor를 받았을 때 중요한 질문은 "decode가 되느냐"가 아니다.  
더 중요한 질문은 **이 응답이 기존 chain의 continuation인지, 아니면 새 canonical world로 page 1부터 다시 시작하라는 boundary인지**다.

이 경계를 response shape에 드러내지 않으면 다음 사고가 난다.

- `REISSUE`인데 client가 page 4 응답이라고 오해하고 page 1 rows를 뒤에 append한다.
- `REJECT`인데 metrics는 그냥 `INVALID_CURSOR`로 뭉개져 restart contract drift를 못 본다.
- canary는 `RESTART_EXPECTED`인 전환을 failure나 hidden success로 잘못 집계한다.

핵심은 `REISSUE`와 `REJECT`를 둘 다 restart-based boundary로 보되, **`REISSUE`는 page 1 reset 성공 응답**, **`REJECT`는 clear-cursor restart를 요구하는 문제 응답**으로 구분하는 것이다.

### Retrieval Anchors

- `legacy cursor reissue api surface`
- `pagination restart envelope`
- `reissue response shape`
- `reject problem envelope`
- `page1 restart response`
- `clear cursor and restart`
- `served page depth reset`
- `requested emitted cursor version`
- `restart expected outcome`

---

## 깊이 들어가기

### 1. `REISSUE`와 `REJECT`는 둘 다 continuation이 아니라 boundary decision이다

legacy cursor verdict를 아래처럼 해석하는 편이 안전하다.

| verdict | 서버 의미 | 응답 family | client 해석 |
|---|---|---|---|
| `ACCEPT` | requested cursor world가 아직 canonical continuity를 유지함 | 일반 pagination success | 요청한 page depth 의미를 유지한다 |
| `REISSUE` | requested cursor world는 종료됐지만, 같은 query를 새 canonical world의 page 1로 재시작시킬 수 있음 | success envelope + explicit restart block | 기존 chain을 버리고 served page 1을 새 시작점으로 삼는다 |
| `REJECT` | requested cursor world를 더 이상 이어 줄 수 없고 즉시 fresh restart가 필요함 | problem/error envelope + explicit restart block | cached cursor를 지우고 fresh query로 page 1부터 다시 시작한다 |

즉 `REISSUE`는 "old cursor도 받고 new cursor도 받는다"가 아니다.  
의미는 **기존 chain은 끝났고, 응답이 새 chain의 page 1을 대신 deliver한다**는 뜻이다.

### 2. response surface는 requested world와 served world를 분리해서 보여 줘야 한다

status code만으로는 restart 의미가 충분히 드러나지 않는다.  
`200 OK`인 `REISSUE`도 있고, `409/422/400` 계열의 `REJECT`도 있을 수 있지만, client와 metrics는 둘 다 같은 vocabulary를 읽어야 한다.

최소한 아래 필드는 verdict와 함께 내려가는 편이 안전하다.

| 필드 | `REISSUE` | `REJECT` | 왜 필요한가 |
|---|---|---|---|
| `pagination_contract.verdict` | 필수 | 필수 | HTTP status와 분리된 정책 해석 축 |
| `pagination_contract.reason_code` | 필수 | 필수 | restart 원인을 관측/디버깅 |
| `pagination_contract.requested_page_depth` | 필수 | 필수 | page `N` 요청이 page `1` reset으로 바뀐 사실을 드러냄 |
| `page_info.served_page_depth` | `1` | 없음 | `REISSUE` 응답 rows가 page `1`임을 명시 |
| `pagination_contract.requested_cursor_version` | 필수 | 필수 | 어떤 legacy family가 boundary를 맞았는지 기록 |
| `pagination_contract.emitted_cursor_version` | 필수 | `null` 또는 없음 | 새 canonical chain 진입 version 노출 |
| `page_info.next_cursor` | 필수 | 없음 | `REISSUE` 뒤 이어질 유일한 cursor |
| `pagination_contract.query_fingerprint_hash` | 필수 | 필수 | restart dedupe와 bucket 해석 |
| `pagination_contract.pagination_contract_id` | 필수 | 필수 | 자동 restart loop 방지 key |
| `pagination_contract.restart.required` | `true` | `true` | restart boundary를 숨기지 않음 |
| `pagination_contract.restart.mode` | 필수 | 필수 | silent restart인지 CTA가 필요한지 분기 |
| `pagination_contract.restart.clear_cached_cursor` | `true` | `true` | old chain을 보존하지 않는다는 선언 |
| `pagination_contract.restart.preserve_query` | 보통 `true` | 보통 `true` | query state 유지 여부를 고정 |

이 표의 요지는 단순하다.  
**requested page depth**와 **served page depth**를 분리하지 않으면, `REISSUE`는 거의 반드시 hidden restart가 된다.

### 3. `REISSUE` success envelope는 "page 1 reset 성공"으로 읽혀야 한다

`REISSUE`는 success 응답이어도 continuation success가 아니다.  
응답 본문 자체가 이미 restart 결과여야 한다.

서버 invariant는 다음과 같다.

- rows는 requested page `N`이 아니라 canonical world의 page `1`을 나타낸다.
- `page_info.next_cursor`는 reissued chain의 다음 step이며, legacy cursor와 섞어 쓰면 안 된다.
- `restart.required=true`와 `served_page_depth=1`이 함께 있어야 client가 append를 멈춘다.
- UI가 infinite scroll이라도 이 응답은 "더 불러오기"가 아니라 "목록 재시작"으로 처리해야 한다.

예시:

```json
{
  "data": {
    "items": [
      {"id": "o-103"},
      {"id": "o-102"}
    ]
  },
  "page_info": {
    "served_page_depth": 1,
    "has_next": true,
    "next_cursor": "v2:orders:createdAtDesc:abc123"
  },
  "pagination_contract": {
    "pagination_contract_id": "orders.search/default-v2",
    "verdict": "REISSUE",
    "reason_code": "LEGACY_CURSOR_RESTART_REQUIRED",
    "requested_page_depth": 4,
    "requested_cursor_version": 1,
    "emitted_cursor_version": 2,
    "query_fingerprint_hash": "9e0baf12",
    "restart": {
      "required": true,
      "target_page_depth": 1,
      "mode": "SILENT_PAGE1_RESTART_ONCE",
      "clear_cached_cursor": true,
      "preserve_query": true
    }
  }
}
```

핵심은 `next_cursor`만 바뀐 것이 아니라, **`served_page_depth=1`과 restart block이 함께 내려와야 한다**는 점이다.

### 4. `REJECT` problem envelope도 restart metadata를 유지해야 한다

`REJECT`는 page data를 줄 수 없더라도 restart contract를 숨기면 안 된다.  
generic `INVALID_CURSOR` 하나만 내려가면 client는 refresh가 맞는지, query를 버려야 하는지, auto-retry가 가능한지 알 수 없다.

안전한 기본값은 problem/error envelope 안에 같은 `pagination_contract` block을 유지하는 것이다.

예시:

```json
{
  "error": {
    "code": "INVALID_CURSOR",
    "message": "The supplied cursor is no longer valid for this pagination contract."
  },
  "pagination_contract": {
    "pagination_contract_id": "orders.search/default-v2",
    "verdict": "REJECT",
    "reason_code": "LEGACY_CURSOR_VERSION_UNSUPPORTED",
    "requested_page_depth": 4,
    "requested_cursor_version": 1,
    "emitted_cursor_version": null,
    "query_fingerprint_hash": "9e0baf12",
    "restart": {
      "required": true,
      "target_page_depth": 1,
      "mode": "CLEAR_CURSOR_AND_RESTART_PAGE1_ONCE_THEN_CTA",
      "clear_cached_cursor": true,
      "preserve_query": true
    }
  }
}
```

`REJECT`에서 중요한 점은 세 가지다.

- `items`와 `next_cursor`는 내려주지 않는다.
- `clear_cached_cursor=true`가 restart contract의 일부다.
- `preserve_query=false`는 normalization/collation world까지 바뀌었을 때만 예외적으로 쓴다.

### 5. client restart semantics는 verdict별로 page 1-only로 고정한다

client 규칙은 "page `N`을 최대한 유지"보다 "restart semantics를 오해하지 않기"를 우선해야 한다.

| verdict | client 기본 동작 | 자동 처리 한도 | 절대 하면 안 되는 것 |
|---|---|---|---|
| `REISSUE` | 기존 cursor chain과 scroll anchor를 버리고, 응답에 포함된 served page `1`을 새 기준으로 렌더링 | `pagination_contract_id x query_fingerprint_hash` 기준 1회 | page `N` 뒤에 rows를 append |
| `REJECT` | cached cursor를 지우고 같은 normalized query로 page `1` fresh request를 다시 보냄 | 자동 0~1회 후 stop | 같은 legacy cursor를 다시 retry |

추가 invariant는 아래처럼 두는 편이 안전하다.

1. restart는 항상 page `1`부터 시작한다. page depth는 보존하지 않는다.
2. query, sort, page-size는 보존할 수 있어도 cursor chain과 pinned source는 보존하지 않는다.
3. infinite scroll, pull-to-refresh, background prefetch 모두 같은 `restart.mode`를 사용한다.
4. 두 번째 자동 restart 실패부터는 explicit refresh CTA로 올라간다.

이 규칙이 없으면 `REISSUE`는 브라우저마다 silent replace, append, blank refresh로 제각각 동작하게 된다.

### 6. observability는 HTTP status보다 `verdict + restart`를 먼저 봐야 한다

packet/metrics layer도 response surface와 같은 단어를 써야 한다.

| 관측 필드 | 왜 필요한가 |
|---|---|
| `requested_cursor_version` | 어떤 legacy family가 cutover boundary를 맞았는지 집계 |
| `emitted_cursor_version` | `REISSUE`가 실제로 어느 canonical version으로 유도했는지 확인 |
| `cursor_verdict_pair` | old/new path의 policy drift를 한 축으로 본다 |
| `continuity_outcome` | `PASS`와 `RESTART_EXPECTED`를 분리한다 |
| `reason_code` | restart 원인을 bucket별로 분해한다 |
| `chain_route` | `LEGACY_REISSUE`, `LEGACY_REJECT`, `PRIMARY_PRIMARY`를 분리한다 |

특히 아래 두 가지를 혼동하면 안 된다.

- `REISSUE`는 success status일 수 있어도 `PASS`가 아니라 `RESTART_EXPECTED`일 수 있다.
- `REJECT`는 4xx여도 의도된 contract라면 failure가 아니라 green boundary일 수 있다.

[Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)의 `cursor_verdict_pair`, `continuity_outcome`를 그대로 재사용하면 cutover, rollback, strict fallback을 같은 language로 읽을 수 있다.

### 7. `REISSUE`와 `REJECT`의 선택 기준은 response 편의가 아니라 semantic safety다

| 상황 | 기본 verdict | 이유 |
|---|---|---|
| legacy cursor를 decode할 수 있고, 같은 query로 canonical page `1` 재시작이 안전함 | `REISSUE` | restart-based compatibility를 제공할 수 있다 |
| sort / tie-breaker / normalization / cursor schema drift가 있어 page `1` 응답도 애매함 | `REJECT` | hidden semantic change를 막는다 |
| rollback bridge TTL이 끝남 | `REJECT` | bridge를 장시간 유지하면 split-brain이 길어진다 |
| mixed cursor world 요청 | `REJECT` | 어떤 boundary row를 기준으로 이어야 할지 모호하다 |

즉 `REISSUE`는 UX-friendly default가 아니라 **page 1 reset을 명시적으로 deliver할 수 있을 때만 쓰는 제한적 정책**이다.

---

## 실전 시나리오

### 시나리오 1: mobile v1 cursor를 v2 cutover 중 받는 경우

- request는 page `4` continuation이지만, canonical world는 이미 `v2`
- server는 legacy `v1` cursor를 `REISSUE`
- response body는 `served_page_depth=1`인 새 page `1`과 `v2` `next_cursor`를 담음
- client는 infinite scroll append 대신 목록을 page `1` 기준으로 교체

핵심은 "계속 읽기 성공"이 아니라 **"page 1 restart를 성공적으로 인도했다"**로 해석하는 것이다.

### 시나리오 2: 같은 cursor가 bridge TTL 뒤 다시 들어오는 경우

- 이미 rollback/cutover bridge window가 끝남
- server는 `REJECT`와 `LEGACY_CURSOR_VERSION_UNSUPPORTED` 또는 bridge-expired reason을 반환
- client는 cached cursor를 지우고 fresh query를 다시 시작
- 두 번째 자동 restart 실패부터는 explicit refresh CTA로 올림

이 경우 억지로 `REISSUE`를 유지하면 client별 loop와 split-brain이 길어진다.

---

## 코드로 보기

```ts
type CursorVerdict = "ACCEPT" | "REISSUE" | "REJECT";

type RestartMode =
  | "NONE"
  | "SILENT_PAGE1_RESTART_ONCE"
  | "CLEAR_CURSOR_AND_RESTART_PAGE1_ONCE_THEN_CTA";

interface PaginationContract {
  paginationContractId: string;
  verdict: CursorVerdict;
  reasonCode: string;
  requestedPageDepth: number;
  requestedCursorVersion: number | null;
  emittedCursorVersion: number | null;
  queryFingerprintHash: string;
  restart: {
    required: boolean;
    targetPageDepth: 1;
    mode: RestartMode;
    clearCachedCursor: boolean;
    preserveQuery: boolean;
  };
}
```

이 타입에서 중요한 필드는 `requestedPageDepth`와 `targetPageDepth: 1`이다.  
둘을 분리하지 않으면 client는 restart response를 continuation response로 오해한다.

---

## 하지 말아야 할 것

- `REISSUE`인데 일반 success pagination처럼 보이게 하고 `next_cursor`만 조용히 바꾸지 말 것
- `REJECT`인데 generic `INVALID_CURSOR`만 내려주고 restart mode를 숨기지 말 것
- page `N` request에서 내려온 `REISSUE` rows를 기존 infinite scroll 끝에 append하지 말 것
- HTTP `200`이면 성공 continuity, `4xx`면 실패라고 단순 분기하지 말 것
- `pagination_contract_id` 없이 auto-restart를 돌려 loop를 만들지 말 것

## 한 줄 정리

Legacy cursor cutover에서 `REISSUE`와 `REJECT`의 핵심 차이는 성공/실패가 아니라 **server가 page 1 restart를 대신 deliver하느냐, 아니면 clear-cursor restart만 요구하느냐**다. 그 차이는 반드시 response shape에 드러나야 한다.
