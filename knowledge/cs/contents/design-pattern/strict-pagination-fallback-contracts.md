---
schema_version: 3
title: Strict Pagination Fallback Contracts
concept_id: design-pattern/strict-pagination-fallback-contracts
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- strict-pagination-fallback
- cursor-world-boundary
- page-depth-fallback
aliases:
- strict pagination fallback contract
- strict list fallback
- list endpoint fallback boundaries
- first page only fallback
- later page rejection contract
- next page continuation contract
- legacy cursor rejection contract
- cursor invalidation fallback
- page depth fallback scope
- actor owned strict list
symptoms:
- strict list fallback을 endpoint 전체 우회로 이해해 actor, query fingerprint, page depth, TTL scope 없이 old path를 넓게 연다
- page1 fallback은 성공했지만 next cursor가 old/new cursor world를 섞어 page2 duplicate/gap을 만든다
- first-page visibility, next-page continuity, legacy cursor rejection을 하나의 fallback 성공으로 뭉개 cutover parity가 흐려진다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/strict-read-fallback-contracts
- design-pattern/cursor-pagination-sort-stability-pattern
- design-pattern/cursor-pagination-parity-read-model-migration
next_docs:
- design-pattern/pinned-legacy-chain-risk-budget
- design-pattern/legacy-cursor-reissue-api-surface
- design-pattern/fallback-capacity-and-headroom-contracts
linked_paths:
- contents/design-pattern/strict-read-fallback-contracts.md
- contents/design-pattern/fallback-capacity-and-headroom-contracts.md
- contents/design-pattern/pinned-legacy-chain-risk-budget.md
- contents/design-pattern/cursor-pagination-sort-stability-pattern.md
- contents/design-pattern/cursor-pagination-parity-read-model-migration.md
- contents/design-pattern/cursor-compatibility-sampling-cutover.md
- contents/design-pattern/strict-list-canary-metrics-rollback-triggers.md
- contents/design-pattern/dual-read-pagination-parity-sample-packet-schema.md
- contents/design-pattern/read-model-cutover-guardrails.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/design-pattern/projection-freshness-slo-pattern.md
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/system-design/dual-read-comparison-verification-platform-design.md
confusable_with:
- design-pattern/strict-read-fallback-contracts
- design-pattern/pinned-legacy-chain-risk-budget
- design-pattern/cursor-pagination-parity-read-model-migration
- design-pattern/legacy-cursor-reissue-api-surface
forbidden_neighbors: []
expected_queries:
- Strict pagination fallback은 endpoint 전체 fallback이 아니라 actor, query fingerprint, page depth, cursor policy를 함께 고정해야 하는 이유가 뭐야?
- page1-only fallback은 visibility 계약이고 page2 continuation은 별도 continuity 계약이라는 차이가 뭐야?
- fallback source가 page1을 serve했을 때 next cursor를 ACCEPT, REISSUE, REJECT 중 무엇으로 처리할지 문서화해야 하는 이유가 뭐야?
- mixed cursor world를 REJECT하지 않으면 old/new boundary row가 섞여 duplicate/gap이 생기는 이유가 뭐야?
- pinned chain ACCEPT는 왜 fallback capacity, TTL, rollback zero ttl을 가진 예외 계약이어야 해?
contextual_chunk_prefix: |
  이 문서는 Strict Pagination Fallback Contracts playbook으로, list/cursor endpoint의
  strict fallback을 actor scope, normalized query fingerprint, page depth, TTL, cursor source,
  ACCEPT/REISSUE/REJECT verdict, mixed cursor rejection, page1-only visibility와 page2 continuity
  경계로 나누어 설계하는 방법을 설명한다.
---
# Strict Pagination Fallback Contracts

> 한 줄 요약: cursor/list endpoint의 strict fallback은 endpoint 전체를 old path로 되돌리는 우회가 아니라 actor, query fingerprint, page depth, cursor policy를 함께 고정한 계약이어야 하며, 특히 `first-page fallback`, `next-page continuation`, `legacy-cursor rejection`을 서로 다른 경계로 분리해 적어야 cutover 중에도 pagination parity가 깨지지 않는다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)
> - [Pinned Legacy Chain Risk Budget](./pinned-legacy-chain-risk-budget.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)
> - [Strict List Canary Metrics and Rollback Triggers](./strict-list-canary-metrics-rollback-triggers.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: strict pagination fallback contract, strict list fallback, list endpoint fallback boundaries, first page only fallback, first page fallback boundary, later page rejection contract, next page continuation contract, legacy cursor rejection contract, cursor invalidation fallback, page depth fallback scope, actor owned strict list, legacy cursor reissue reject, fallback cursor pinning, pagination parity cutover, next page continuity fallback, mixed cursor prevention, mixed cursor world rejection, single cursor world chain, projection cutover strict list, projection fallback cursor contract, read model migration strict list, pinned legacy chain risk budget, accept pinned chain ttl, strict list canary metrics, page depth canary dashboard, strict list rollback trigger, page1 page2 split canary

---

## 핵심 개념

상세 endpoint의 strict fallback은 보통 "이 요청을 다른 read path로 보내라"로 설명할 수 있다.  
하지만 cursor/list endpoint는 그렇지 않다.

- page 1을 어느 source에서 읽었는가
- next cursor가 어느 cursor world를 가리키는가
- page 2부터도 strict 보장이 필요한가
- legacy/new cursor를 어떤 조건에서 받아들일 것인가
- cutover 중 fallback 샘플을 parity에서 어떻게 분리할 것인가

이 질문에 답이 없으면 `first page는 살렸다`고 생각한 순간 `page 2`에서 duplicate, gap, restart surprise가 난다.

Strict Pagination Fallback Contract는 [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)의 ownership/routing/rate 계약을 목록 endpoint로 좁혀서, **page depth와 cursor invalidation까지 포함한 운영 계약**으로 만든 것이다.

### Retrieval Anchors

- `strict pagination fallback contract`
- `strict list fallback`
- `first page only fallback`
- `cursor invalidation fallback`
- `page depth fallback scope`
- `actor owned strict list`
- `legacy cursor reissue reject`
- `fallback cursor pinning`
- `pagination parity cutover`
- `next page continuity fallback`
- `later page rejection contract`
- `mixed cursor prevention`
- `single cursor world chain`

---

## 깊이 들어가기

### 1. strict list는 상세 strict와 따로 registry를 가져야 한다

많은 팀이 "내 주문 목록도 strict"라고만 적고 끝낸다.  
하지만 목록 strict는 상세 strict보다 계약면이 넓다.

- actor 본인의 직후 생성 항목이 page 1에 보여야 하는가
- 같은 query fingerprint일 때만 strict인가
- sort가 `createdAt DESC`일 때만 strict인가
- page 2 이후도 strict인가, 아니면 page 1만 strict인가

즉 strict list registry는 최소한 `endpoint + actor scope + normalized query + page depth`를 같이 적어야 한다.

### 2. fallback scope 단위는 endpoint가 아니라 actor + query + page depth다

실전에서 위험한 확장은 "내가 방금 만든 주문 목록 first page" fallback이 "전체 주문 검색 endpoint" fallback으로 번지는 경우다.

그래서 scope를 다음처럼 고정해 두는 편이 안전하다.

| 축 | 꼭 적어야 하는 것 | 예시 |
|---|---|---|
| Actor scope | 누구에게 strict를 허용하는가 | 작성자 본인만 |
| Query scope | 어떤 normalized query에만 적용하는가 | `status=ALL`, 기본 sort, keyword 없음 |
| Page depth | 몇 페이지까지 strict fallback을 허용하는가 | page 1 only |
| TTL | 얼마나 오래 fallback을 허용하는가 | 생성 후 5초 |
| Route | 어떤 source로 우회하는가 | old projection 또는 write query port |

이 다섯 축 중 하나라도 비어 있으면 fallback은 금방 "목록 endpoint 전체의 숨은 dual stack"이 된다.

### 3. `first-page-only`는 UX 약속이지 pagination continuity 약속이 아니다

`first-page-only fallback`이 의미하는 것은 보통 다음이다.

- 방금 쓴 항목이 첫 페이지에서 보이게 한다
- strict 보장은 actor-owned query에만 한정한다
- page 2 이후는 일반 consistency 예산으로 돌린다

즉 이 계약은 "page 1은 strict"이지 "old/new pagination chain이 끝까지 이어진다"를 뜻하지 않는다.  
그래서 first-page-only를 문서화할 때는 반드시 **page 2 이후 verdict**를 같이 적어야 한다.

문서에 `first-page-only`만 쓰고 `next cursor` 의미를 비워 두면, 클라이언트는 pagination continuity가 보장된다고 오해한다.

### 4. list endpoint fallback 경계는 세 가지를 따로 적어야 한다

상세 strict read는 보통 "이 요청을 fallback path로 보낼지"로 설명할 수 있다.  
하지만 목록 endpoint는 같은 strict read라도 아래 세 경계가 서로 다른 약속이다.

| 경계 | 실제로 보호하는 것 | 안전한 기본값 | 더 강한 선택이 정당화되는 조건 | 따로 봐야 하는 지표 |
|---|---|---|---|---|
| `first-page fallback` | actor-owned list의 즉시 가시성 | `page1-only` strict fallback | 방금 생성/수정한 row가 첫 화면에서 바로 보여야 하고 scope가 아주 좁을 때 | page-1 fallback rate, strict-window hit rate |
| `next-page continuation` | page 1 뒤의 pagination chain 연속성 | `REISSUE` 또는 `REJECT` | continuity 자체가 UX 약속이고 same-source chain, TTL pinning, capacity reserve가 증명됐을 때 | second-page mismatch, duplicate/gap, pinned-chain saturation |
| `legacy-cursor rejection` | 이전 cursor world와 새 cursor world의 프로토콜 경계 | 기본 `REJECT`, 제한적 `REISSUE` | sort/filter/null ordering/collation/cursor schema가 실질적으로 동일할 때만 `ACCEPT` 검토 | accepted-after-reject drift, rejection reason 분포, restart success rate |

즉 `page 1은 strict`라고 적었다고 해서 `page 2도 같은 source로 이어진다`거나 `예전 cursor도 계속 받는다`가 자동으로 따라오지 않는다.  
첫 번째는 **visibility 계약**, 두 번째는 **continuity 계약**, 세 번째는 **protocol boundary 계약**이다.

### 5. cursor invalidation policy는 fallback 계약의 일부여야 한다

page 1이 fallback source에서 나갔다면, page 2 요청에 들어오는 cursor를 어떻게 처리할지 미리 고정해야 한다.

| 정책 | 의미 | 언제 안전한가 | 기본 추천 |
|---|---|---|---|
| `ACCEPT` | fallback source가 발급한 cursor chain을 page 2 이후도 그대로 계속 받음 | same sort/filter/collation + TTL pinning + fallback capacity가 증명됐을 때만 | 예외적 |
| `REISSUE` | page 1 응답은 보여 주되, 다음부터는 canonical cursor로 재시작하게 함 | first-page visibility는 필요하지만 full continuity는 strict가 아닐 때 | 제한적 허용 |
| `REJECT` | page 1 strict만 보장하고, 이후 cursor는 명시적으로 끊음 | general search, cutover 중 semantics 차이, legacy cursor 혼용 위험이 있을 때 | 안전한 기본값 |

핵심은 `page 1 fallback 성공`과 `다음 cursor 호환`을 별개로 보는 것이다.  
[Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)에서 말하는 `ACCEPT/REISSUE/REJECT`는 cutover용 verdict이지만, strict pagination fallback에서도 같은 축으로 써야 해석이 통일된다.

### 6. first-page-only 계약은 "무슨 cursor를 발급할지"까지 써야 한다

가장 흔한 사고는 page 1은 old projection에서 읽고, next cursor는 새 projection 기준으로 그냥 발급하는 것이다.

이 경우 표면상 page 1은 살지만 실제로는:

- page 2에서 경계 row가 바뀌고
- duplicate/gap이 생기고
- legacy cursor를 받은 client가 silently 다른 cursor world로 넘어가고
- cutover parity 대시보드는 원인을 설명하지 못한다

그래서 page 1 strict fallback 응답에는 최소한 다음 메타데이터가 필요하다.

- `cursor_source`: `primary`, `fallback-old`, `fallback-write-model`
- `cursor_version`
- `cursor_verdict`: `ACCEPT`, `REISSUE`, `REJECT`
- `query_fingerprint_hash`
- `pagination_contract_id`
- `fallback_reason`: watermark lag, version lag, cutover mismatch 등
- `strict_window_expires_at`

즉 first page 응답은 단순 row 목록이 아니라 **어느 pagination world를 보고 있는지에 대한 선언**이어야 한다.

### 7. projection cutover safe default는 `page1-only + later-page REJECT/REISSUE + mixed-cursor 금지`다

projection cutover 중 strict list의 안전한 기본값은 `page 1만 fallback으로 살리고`, `later page는 명시적으로 REISSUE 또는 REJECT`, `old/new cursor world 혼합은 금지`로 못 박는 것이다.

그 이유는 cutover 동안 아래 축 중 하나라도 쉽게 달라지기 때문이다.

- projection version / freshness watermark
- stable sort tie-breaker
- normalization version / query fingerprint
- cursor schema / emitted version

later-page 요청은 아래처럼 따로 문서화해 두는 편이 안전하다.

| later-page 요청 형태 | 기본 verdict | 왜 이렇게 보나 | 응답/관측에 꼭 남길 것 |
|---|---|---|---|
| page 1 strict fallback 뒤 `fallback-old` cursor로 page 2 continuation | `REJECT` 또는 제한적 `REISSUE` | first-page visibility와 full-chain continuity를 분리한다 | `cursor_source`, `cursor_verdict`, `reason_code` |
| page 1 응답이 재발급한 canonical cursor로 page 2 재시작 | `ACCEPT` | same cursor world에서 새 chain이 시작된다 | `requested_cursor_version`, `emitted_cursor_version` |
| legacy cursor와 reissued canonical cursor가 섞인 재시도 | 항상 `REJECT` | 어떤 cursor world를 기준으로 boundary row를 계산할지 모호하다 | `reason_code=mixed_cursor_world` |
| query fingerprint / sort / size bucket이 바뀐 later-page 요청 | fresh query만 허용 | strict scope 밖으로 이미 벗어났다 | `reason_code=query_scope_changed` |

특히 `REISSUE`는 "old cursor도 받고 new cursor도 받는다"가 아니다.  
의미는 **page 1 응답이 발급한 canonical cursor만 이후 chain의 유일한 진입점**이라는 뜻이다.

실무에서는 아래 single-world invariant를 later-page guard로 고정하는 편이 안전하다.

1. 한 pagination chain은 하나의 normalized query fingerprint만 가진다.
2. 한 pagination chain은 하나의 cursor world(`source + cursor_version + normalization_version`)만 가진다.
3. 한 pagination chain은 하나의 continuation mode(`ACCEPT_PINNED_CHAIN` 또는 `REISSUE/REJECT`)만 가진다.

이 세 invariant가 깨지면 page 1은 맞아 보여도 page 2에서 duplicate/gap이 생기고, [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)와 [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)에서 말하는 `requested/emitted version matrix`, `continuity outcome` 해석도 흐려진다.

### 8. next-page continuation은 기본 strict-read와 다른 용량 계약을 먹는다

next page를 same source로 계속 읽게 하는 순간, strict list는 단순 fallback이 아니라 **짧은 dual-pagination world 운영**이 된다.

- page 1 응답 source를 actor/query별로 pinning해야 하고
- 같은 chain에 대해 old/new cursor 혼합을 막아야 하고
- pinned chain TTL 동안 fallback source capacity를 따로 예약해야 하며
- rollback 때도 "어느 chain이 canonical인가"를 다시 선언해야 한다

그래서 `PINNED_CHAIN_ACCEPT`는 `page 1 visibility`보다 훨씬 비싼 약속이다.  
대부분의 strict list는 first-page fallback만 두고, next page는 `REISSUE`나 `REJECT`로 끊는 편이 안전하다.
`ACCEPT`를 예외적으로 남길 때 필요한 justify gate, TTL, reserve, rollback zero-ttl은 [Pinned Legacy Chain Risk Budget](./pinned-legacy-chain-risk-budget.md)처럼 별도 budget 문서로 고정하는 편이 안전하다.

### 9. 허용 가능한 계약 모양은 몇 개 안 된다

목록 strict fallback은 대체로 아래 셋 중 하나로 고정하는 편이 안전하다.

| 계약 모양 | 설명 | 적합한 경우 | 주의점 |
|---|---|---|---|
| `NO_LIST_FALLBACK` | 목록 strict를 두지 않음 | 일반 검색, 추천 목록 | read-your-writes는 다른 UX로 해결해야 함 |
| `PAGE1_STRICT_REJECT_OR_REISSUE` | page 1만 strict fallback, page 2는 재시작 또는 거절 | actor-owned recent list, 직후 조회 shortcut | 응답에 restart semantics를 명확히 노출해야 함 |
| `PINNED_CHAIN_ACCEPT` | 좁은 TTL 동안 same source cursor chain 유지 | 일부 my-list where continuity도 strict | capacity, cursor TTL, rollback semantics가 더 무거워짐 |

대부분의 endpoint는 두 번째 모양이면 충분하다.  
세 번째 모양은 편해 보여도 사실상 old/new pagination world를 병행 운영하는 비용을 감수하는 선택이다.

### 10. legacy-cursor rejection은 에러 처리가 아니라 cutover 경계 선언이다

legacy cursor rejection을 "page 2에서 에러 하나 던지면 된다" 정도로 보면 운영 해석이 무너진다.

- rejection은 fallback 실패가 아니라 `이 cursor world는 더 이상 이어지지 않는다`는 선언이어야 하고
- reason code는 sort drift, cursor schema change, cutover mode, strict window expiry처럼 재시작 이유를 설명해야 하며
- client는 silent restart인지, explicit restart CTA인지, fresh query 재발급인지 동일하게 처리해야 한다

즉 legacy-cursor rejection은 예외 처리보다 **boundary management**에 가깝다.  
특히 cutover 중에는 `legacy accepted` 샘플과 `legacy rejected` 샘플을 섞지 말고 별도로 기록해야 drift를 읽을 수 있다.

### 11. query fingerprint와 page-size bucket이 빠지면 운영 해석이 안 된다

strict pagination fallback은 "몇 번 fallback했나"만 보면 충분하지 않다.  
다음 정보가 같이 남아야 원인을 해석할 수 있다.

- normalized query fingerprint
- sort key + direction
- page size bucket
- requested cursor version
- page depth
- fallback route
- cursor verdict
- duplicate/gap 여부
- page 1 / page 2 continuity mismatch 여부

특히 `page1 strict fallback success but second-page mismatch`는 일반 fallback rate보다 위험한 샘플이다.  
page 1 체감은 살렸지만 pagination contract는 이미 깨졌다는 뜻이기 때문이다.

### 12. cutover parity는 fallback chain을 별도 표본으로 분리해야 한다

cutover sampled dual-read가 canonical traffic만 보면 strict list 사고를 놓치기 쉽다.

최소한 다음 두 집합을 따로 본다.

1. `primary -> primary` chain parity  
   new projection이 canonical path로 안전한지 본다.
2. `fallback page1 -> verdict -> page2` chain parity  
   strict fallback이 pagination contract를 깨지 않는지 본다.

두 번째 집합에서는 특히 다음을 남겨야 한다.

- page 1이 어느 source에서 나왔는지
- next cursor verdict가 무엇이었는지
- page 2를 정말 허용했는지, 재시작시켰는지
- `page1 ∪ page2` union에서 duplicate/gap이 있었는지

즉 strict list fallback은 [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)의 일반 fallback 항목으로 뭉개면 안 되고, **pagination chain 단위 guardrail**로 따로 본다.

### 13. cutover admission과 rollback 기준도 page-depth별로 가져야 한다

운영 기준도 endpoint 전체가 아니라 page depth별로 다르게 적는 편이 맞다.

| 지표 | 왜 보나 | 예시 중지 기준 |
|---|---|---|
| page-1 strict fallback rate | primary freshness 압박 감지 | 15분 이동평균 2% 초과 |
| fallback chain second-page mismatch rate | first-page-only 계약이 실제로 새 bug를 만들지 확인 | 0.1% 초과 시 canary freeze |
| legacy cursor rejected-after-accept sample | cursor invalidation drift 감지 | 샘플 1건이라도 원인 분석 전 승격 중지 |
| duplicate/gap sample rate | pagination parity 붕괴 감지 | size bucket별 임계치 초과 시 rollback |
| fallback source burst saturation | old path / write model 2차 장애 방지 | headroom 20% 미만 시 strict scope 축소 |

여기서 중요한 건 `page 1 strict success`만으로 cutover를 통과시키지 않는 것이다.  
목록 endpoint는 `next cursor`가 실제 사용자 경험의 절반이다.

특히 `fallback source burst saturation` 행은 old projection이나 write-side가 page1 strict burst를 실제로 감당하는지 별도 용량 계약으로 확인해야 하며, 그 기준은 [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)로 내려가야 한다.
page-depth별 metric family와 freeze/hard rollback 분리는 [Strict List Canary Metrics and Rollback Triggers](./strict-list-canary-metrics-rollback-triggers.md)에서 더 좁게 다룬다.

### 14. 최소 계약 패킷을 템플릿으로 남겨 두면 팀 간 해석이 빨라진다

| 필드 | 꼭 적어야 하는 질문 | 예시 |
|---|---|---|
| Endpoint ID | 어느 list endpoint인가 | `my-orders.list` |
| Strict reason | 왜 strict가 필요한가 | 직후 생성 주문이 page 1에서 보여야 함 |
| Actor scope | 누구에게만 strict인가 | 작성자 본인 |
| Query scope | 어떤 normalized query만 strict인가 | `status=ALL`, default sort |
| Page-depth policy | 어느 페이지까지 strict인가 | `page1-only` |
| First-page fallback | page 1 strict를 어디까지 보장하는가 | actor-owned first page only |
| Next-page policy | page 2부터 same chain을 이어 줄 것인가 | `REISSUE` |
| Legacy cursor policy | old cursor를 받아들일 것인가 | `REJECT` |
| Cursor world mix policy | later-page에서 어떤 cursor world만 허용하는가 | `single-world-only` |
| Fallback route | 어디로 우회하는가 | old projection |
| Cursor verdict | 새 cursor를 어떻게 설명하는가 | `REISSUE` |
| Cursor TTL | chain pinning 또는 restart 유효 시간 | 5초 |
| Parity gate | 어떤 샘플을 봐야 승격 가능한가 | `page1->page2` continuity |
| Max rate | 허용 fallback/mismatch 상한 | fallback 0.5%, mismatch 0.1% |
| Owner | 누가 승인/운영하는가 | orders team + platform on-call |

이 패킷이 있으면 "strict list를 운영한다"는 말이 page 1 UX, cursor invalidation, cutover parity를 모두 포함하게 된다.

### 15. 하지 말아야 할 것

- page 1만 old projection으로 읽고 next cursor는 새 projection 기준으로 조용히 발급하지 말 것
- page 1 응답이 재발급한 canonical cursor와 legacy/fallback cursor를 같은 later-page chain에서 함께 받지 말 것
- actor-owned strict shortcut을 전체 search endpoint fallback으로 넓히지 말 것
- `first-page-only`라고 문서화해 놓고 response에서는 일반 pagination처럼 보이게 만들지 말 것
- cutover parity 샘플에서 fallback traffic을 canonical sample에 섞어 버리지 말 것
- `ACCEPT`를 기본값처럼 두지 말 것

strict pagination fallback의 기본값은 대개 `narrow scope + page1 only + REISSUE/REJECT`다.  
`ACCEPT`는 편한 기본값이 아니라 비싼 예외다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 직후 내 주문 목록

사용자는 방금 만든 주문이 `내 주문` 첫 페이지에서 바로 보여야 한다.

- actor scope: 작성자 본인
- query scope: 기본 정렬, 필터 없음
- page-depth policy: page 1 only
- fallback route: old projection
- cursor verdict: `REISSUE`
- later-page rule: reissued canonical cursor만 허용, legacy/fallback cursor는 `REJECT`

이 경우 page 1 visibility는 보장하지만, page 2 이후는 canonical cursor로 다시 시작하게 만들어 old/new chain 혼합을 막는다.

### 시나리오 2: 검색 projection cutover 중 strict shortcut 유지

일반 검색은 strict가 아니지만 `내가 방금 만든 글 검색` shortcut만 strict라고 해 보자.

- 일반 검색: no fallback
- strict shortcut: page 1 only fallback
- canary gate: fallback chain second-page mismatch rate 별도 관찰
- rollback trigger: legacy accepted sample에서 duplicate/gap 발생

즉 strict shortcut을 살린다고 전체 search cursor contract를 느슨하게 만들 필요는 없다.

### 시나리오 3: continuity도 중요한 VIP 목록

일부 고객센터 화면은 page 2 이후도 같은 source continuity가 중요할 수 있다.

- page-depth policy: pinned chain
- cursor verdict: `ACCEPT`
- strict window: 10초
- 추가 요구사항: fallback source capacity reserve, cursor TTL cleanup, rollback 시 client restart message

이 경우는 가능하지만, 운영 비용이 커서 예외적으로만 허용하는 편이 맞다.

---

## 코드로 보기

### strict pagination fallback contract

```java
public enum NextPagePolicy {
    ACCEPT_PINNED_CHAIN,
    REISSUE,
    REJECT
}

public enum LegacyCursorPolicy {
    ACCEPT,
    REISSUE,
    REJECT
}

public enum CursorWorldMixPolicy {
    SINGLE_WORLD_ONLY,
    ALLOW_PINNED_CHAIN
}

public record StrictPaginationFallbackContract(
    String endpointId,
    String queryFingerprint,
    int maxStrictPageDepth,
    Duration strictWindow,
    FallbackRoute fallbackRoute,
    NextPagePolicy nextPagePolicy,
    LegacyCursorPolicy legacyCursorPolicy,
    CursorWorldMixPolicy cursorWorldMixPolicy
) {}
```

### routing verdict

```java
public record PaginationRouteDecision(
    ReadRoute route,
    NextPagePolicy nextPagePolicy,
    LegacyCursorPolicy legacyCursorPolicy,
    boolean strictApplied,
    String fallbackReason
) {}

public class StrictPaginationRouter {
    public PaginationRouteDecision decide(
        int requestedPageDepth,
        boolean actorOwned,
        boolean primaryFreshEnough,
        StrictPaginationFallbackContract contract
    ) {
        if (!actorOwned || requestedPageDepth > contract.maxStrictPageDepth()) {
            return new PaginationRouteDecision(
                ReadRoute.PRIMARY,
                NextPagePolicy.REISSUE,
                LegacyCursorPolicy.REJECT,
                false,
                "strict_scope_exceeded"
            );
        }

        if (primaryFreshEnough) {
            return new PaginationRouteDecision(
                ReadRoute.PRIMARY,
                NextPagePolicy.ACCEPT_PINNED_CHAIN,
                LegacyCursorPolicy.ACCEPT,
                false,
                "primary_fresh"
            );
        }

        return new PaginationRouteDecision(
            contract.fallbackRoute().readRoute(),
            contract.nextPagePolicy(),
            contract.legacyCursorPolicy(),
            true,
            "projection_lag"
        );
    }
}
```

### safe default

```java
// 대부분의 strict list는 page 1만 fallback하고,
// page 2부터는 reissued canonical cursor만 허용해 mixed-cursor를 막는다.
StrictPaginationFallbackContract contract =
    new StrictPaginationFallbackContract(
        "my-orders.list",
        "status=ALL|sort=createdAt,DESC",
        1,
        Duration.ofSeconds(5),
        FallbackRoute.OLD_PROJECTION,
        NextPagePolicy.REISSUE,
        LegacyCursorPolicy.REJECT,
        CursorWorldMixPolicy.SINGLE_WORLD_ONLY
    );
```

---

## 정리

strict pagination fallback의 핵심은 "목록도 strict하게 읽는다"가 아니다.  
핵심은 **어떤 actor/query/page depth에서만 strict를 허용하고, 그 순간 발급된 cursor가 어느 world에 속하는지까지 문서화하는 것**이다.

이 축이 빠지면 page 1 UX를 지키려다 page 2 parity를 잃고, cutover canary는 그 차이를 설명하지 못한다.  
그래서 strict list 계약은 fallback route보다 먼저 `page-depth policy + cursor verdict + cursor-world mix policy + parity gate`를 문서로 고정해야 한다.
