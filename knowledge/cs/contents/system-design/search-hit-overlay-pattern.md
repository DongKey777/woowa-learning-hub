---
schema_version: 3
title: Search Hit Overlay Pattern
concept_id: system-design/search-hit-overlay-pattern
canonical: false
category: system-design
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- search hit overlay pattern
- stale search hit overlay
- search stale row patch
- stale search result patch
aliases:
- search hit overlay pattern
- stale search hit overlay
- search stale row patch
- stale search result patch
- search freshness overlay
- top k hydrate overlay
- ranked ids then hydrate
- search result hydration pattern
- search result patching
- search hit enrichment freshness
- search detail consistency
- search hit stale after update
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/list-detail-monotonicity-bridge.md
- contents/system-design/read-after-write-routing-primer.md
- contents/system-design/mixed-cache-replica-freshness-bridge.md
- contents/system-design/search-indexing-pipeline-design.md
- contents/system-design/document-search-ranking-platform-design.md
- contents/system-design/tenant-aware-search-architecture-design.md
- contents/design-pattern/projection-freshness-slo-pattern.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Search Hit Overlay Pattern 설계 핵심을 설명해줘
- search hit overlay pattern가 왜 필요한지 알려줘
- Search Hit Overlay Pattern 실무 트레이드오프는 뭐야?
- search hit overlay pattern 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Search Hit Overlay Pattern를 다루는 deep_dive 문서다. search index는 후보를 빨리 찾고, fresher row/detail store는 상위 hit의 몇 개 필드만 안전하게 덮어쓰는 식으로 합치면 모든 search read를 primary read로 바꾸지 않고도 stale 검색 결과를 줄일 수 있다. 검색 질의가 search hit overlay pattern, stale search hit overlay, search stale row patch, stale search result patch처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Search Hit Overlay Pattern

> 한 줄 요약: search index는 후보를 빨리 찾고, fresher row/detail store는 상위 hit의 몇 개 필드만 안전하게 덮어쓰는 식으로 합치면 모든 search read를 primary read로 바꾸지 않고도 stale 검색 결과를 줄일 수 있다.

retrieval-anchor-keywords: search hit overlay pattern, stale search hit overlay, search stale row patch, stale search result patch, search freshness overlay, top k hydrate overlay, ranked ids then hydrate, search result hydration pattern, search result patching, search hit enrichment freshness, search detail consistency, search hit stale after update, search result older than detail, safe search overlay beginner, search hit overlay pattern basics

**난이도: 🟢 Beginner**

관련 문서:

- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
- [Document Search / Ranking Platform 설계](./document-search-ranking-platform-design.md)
- [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md)
- [Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md)

---

## 핵심 개념

먼저 어려운 용어보다 화면 경험으로 생각하자.

> 검색은 "무엇을 찾을지"를 빠르게 결정하고, overlay는 "사용자에게 보일 몇 개 필드가 너무 오래되지 않았는지"를 마지막에 한 번 더 확인하는 단계다.

즉 이 패턴은 검색 엔진을 버리고 primary DB를 직접 검색하는 방법이 아니다.
보통은 아래처럼 역할을 나눈다.

- search index: 후보 문서 ID, rank, highlight를 빠르게 찾는다
- row/detail store: 상위 hit의 상태, 제목, 가격, 공개 여부 같은 최신 필드를 확인한다
- overlay step: search hit 위에 fresher 필드만 덮어쓴다

핵심은 **검색은 여전히 검색 엔진으로 하고, freshness 보정만 작은 범위로 한다**는 점이다.

---

## 초보자 mental model: 검색은 후보 찾기, overlay는 표면 고치기

한 번에 외우면 쉽다.

- search index는 "어떤 문서를 보여 줄지"를 정하는 빠른 후보 탐색기다.
- overlay는 "보여 주기로 한 결과의 몇 필드가 너무 낡지 않았는지"를 확인하는 얇은 보정층이다.
- 그래서 overlay는 보통 페이지에 실제로 보여 줄 상위 `N`개에만 적용한다.

```text
query
  -> search index returns ranked hits
  -> take visible top N ids
  -> batch read fresher rows/details
  -> compare version/status/updated_at
  -> patch only safe display fields
  -> render
```

이 구조의 장점은 두 가지다.

- search ranking, typo tolerance, highlight는 그대로 유지한다
- 모든 검색을 primary read로 바꾸지 않고도 stale 표면을 줄인다

---

## 언제 이 패턴이 필요한가

| 보이는 문제 | 왜 search만 믿으면 깨지나 | overlay가 하는 일 |
|---|---|---|
| 검색 결과 제목이 상세보다 오래됨 | index refresh lag가 있다 | fresher title로 덮어쓴다 |
| 상태가 `PENDING`인데 상세는 `PAID`다 | summary document가 아직 안 따라왔다 | 최신 status만 교체한다 |
| 비공개/삭제 문서가 잠깐 남아 보인다 | delete/update tombstone 반영이 늦다 | 표시 suppress 또는 hidden 처리한다 |
| 가격/재고가 상세와 다르다 | 검색 문서는 ranking용 snapshot일 수 있다 | 최신 가격/재고 필드를 교체한다 |

반대로 아래는 overlay만으로 해결하려 하면 위험하다.

| 주의 상황 | 왜 위험한가 | 더 먼저 볼 문서 |
|---|---|---|
| 검색 predicate 자체를 DB에서 다시 계산해 순서를 바꾸고 싶다 | 사실상 search를 DB로 다시 하는 셈이라 비용이 커진다 | [Document Search / Ranking Platform 설계](./document-search-ranking-platform-design.md) |
| ACL/tenant 경계를 search hit만 믿고 통과시키고 있다 | freshness 문제가 아니라 보안/격리 문제다 | [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md) |
| 방금 내가 수정한 값이 바로 안 보인다 | search overlay보다 `recent-write` routing이 먼저다 | [Read-After-Write Routing Primer](./read-after-write-routing-primer.md) |

---

## 안전한 overlay 방식 4가지

초보자 단계에서는 아래 4개 안에서 고르면 대부분 충분하다.

| 방식 | 어떻게 동작하나 | 잘 맞는 경우 | 주의점 |
|---|---|---|---|
| top-`N` batch hydrate | 현재 페이지에 보이는 hit ID만 한 번에 fresh read | 가장 일반적 | page size가 커지면 hydrate 비용을 제한해야 한다 |
| selective field patch | `status`, `title`, `price`, `visibility` 같은 일부 필드만 덮어씀 | ranking은 index에 두고 표면만 보정할 때 | score, highlight, snippet까지 함부로 바꾸지 않는다 |
| stale suppress | fresh row가 `DELETED`, `HIDDEN`, `FORBIDDEN`이면 결과를 숨김 | 잘못 노출되면 안 되는 상태 | 결과 개수/페이지네이션 변화를 UX와 같이 정해야 한다 |
| version-gated overlay | `row.version > hit.version`일 때만 patch | 명확한 freshness 비교 기준이 있을 때 | version 없이 `updated_at`만 쓰면 clock drift를 조심한다 |

짧게 정리하면:

- 먼저 `top-N batch hydrate`
- 그 위에 `selective field patch`
- 필요하면 `stale suppress`
- 비교 기준은 가능하면 `version-gated`

---

## 주문 검색 예시로 보기

사용자가 `123`을 검색했는데 search index에는 아직 예전 문서가 남아 있다고 하자.

```text
search hit
- id = order:123
- rank = 1
- title = "주문 123"
- status = PENDING
- version = 40
```

하지만 fresher row store에는 이미 결제가 끝난 상태다.

```text
detail row
- id = order:123
- status = PAID
- version = 42
- updated_at = 10:21:03
```

이때 search query 자체를 primary에서 다시 수행할 필요는 없다.
대신 상위 hit ID만 batch hydrate한 뒤, version을 비교해서 표면 필드만 덮어쓴다.

```text
candidate hit ids = [123, 456, 789]
fresh rows = batchGet([123, 456, 789])

if fresh.version > hit.version:
  hit.status = fresh.status
  hit.title = fresh.title
  hit.version = fresh.version
```

이렇게 하면:

- rank 1이라는 검색 결과 순서는 유지된다
- 사용자는 `PENDING` 대신 `PAID`를 본다
- 전체 검색을 primary read로 바꾸지 않아도 된다

---

## overlay에서 무엇을 바꾸고, 무엇을 안 바꾸나

| 항목 | overlay해도 비교적 안전 | 이유 |
|---|---|---|
| 상태 배지 (`PENDING -> PAID`) | 예 | 사용자 혼동을 줄이는 대표 필드다 |
| 제목/표시명 | 예 | 최신 행의 canonical 표시값을 따라가기 쉽다 |
| 가격/재고/공개 여부 | 예, 단 도메인 중요도 높으면 신중히 | stale이면 제품 사고로 이어질 수 있다 |
| 삭제/숨김 여부 | 예 | stale 노출 방지에 중요하다 |

| 항목 | 함부로 overlay하지 말 것 | 이유 |
|---|---|---|
| rank/score | 아니오 | search engine의 ranking 계약을 깨기 쉽다 |
| snippet/highlight | 보통 아니오 | search hit text와 어긋나기 쉽다 |
| total hit count | 보통 아니오 | 상위 몇 개 patch와 전체 집계는 다른 문제다 |
| filter match 여부 | 아니오 | query semantics 자체를 다시 계산해야 할 수 있다 |

외우는 법은 간단하다.

- **보여 주는 표면 필드**는 overlay 후보
- **검색 의미와 순서**는 search engine 계약

---

## 모든 search를 primary로 보내지 않으려면

이 문서의 목표는 "overlay 때문에 결국 다 primary로 읽게 되는 것"을 피하는 것이다.
그래서 보통 아래 순서로 좁게 적용한다.

1. 검색은 기존처럼 index가 담당한다.
2. 실제로 보여 줄 page의 top `N` id만 hydrate한다.
3. hydrate는 가능하면 replica/detail cache/summary store에서 먼저 읽는다.
4. 정말 최근 write 구간이거나 safety-critical row만 primary fallback한다.

| 선택 | 비용 | freshness | beginner 추천도 |
|---|---|---|---|
| search 결과 전체를 primary에서 재검색 | 매우 큼 | 높음 | 낮음 |
| top `N` hit만 batch hydrate | 중간 | 충분히 좋음 | 높음 |
| top `N` 중 recent-write entity만 primary fallback | 제한적 | 필요한 곳만 높음 | 높음 |

즉 overlay는 "search 결과를 DB로 다시 계산"하는 패턴이 아니라, **작은 hydrate 비용으로 stale 표면만 줄이는 패턴**이어야 한다.

---

## common confusion

- `overlay를 넣었으니 search index freshness는 이제 신경 안 써도 된다`
  - 아니다. overlay는 얇은 보정층일 뿐이고, index lag가 길면 결국 hit count, snippet, ranking drift는 남는다.
- `상세가 더 최신이면 rank도 다시 정렬해야 한다`
  - 보통 아니다. overlay의 1차 목적은 최신 표면 보정이지 ranking 재계산이 아니다.
- `stale hit를 고치려면 search 요청마다 primary DB를 읽어야 한다`
  - 아니다. 대부분은 top `N` hydrate + selective patch로 충분하다.
- `overlay는 cache와 search를 섞으니 위험하다`
  - 위험한 것은 "아무 규칙 없이" 섞는 것이다. `id`, `version`, `safe fields` 기준이 있으면 관리 가능하다.

---

## 면접/설계 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> search 결과는 여전히 index에서 찾고, 페이지에 실제로 보여 줄 상위 hit만 fresher row/detail store로 batch hydrate해서 일부 필드를 overlay합니다. 이렇게 하면 ranking과 검색 성능은 유지하면서도 status, title, visibility 같은 stale 표면을 줄일 수 있습니다. 핵심은 전체 검색을 primary로 재실행하지 않고, top-N selective patch와 version 비교로 좁게 보정하는 것입니다.

## 한 줄 정리

Search hit overlay pattern은 search index의 빠른 후보 탐색은 유지하고, 상위 hit의 최신 표면 필드만 작은 hydrate/read로 덮어써 stale 검색 결과를 줄이는 beginner-friendly freshness 패턴이다.
