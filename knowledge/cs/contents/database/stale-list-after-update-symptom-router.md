---
schema_version: 3
title: 수정했는데 목록은 옛값이에요 원인 라우터
concept_id: database/stale-list-after-update-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
- missions/roomescape
review_feedback_tags:
- list-after-update-stale
- projection-vs-primary-read
- cache-replica-source-split
aliases:
- 수정했는데 목록만 옛값
- 상세는 바뀌었는데 리스트는 안 바뀜
- update 후 list stale
- save success list old data
- 목록 새로고침해야 반영됨
- detail 은 최신인데 list 는 예전 값
symptoms:
- 수정 저장은 성공했는데 목록 화면에는 예전 값이 그대로 보여요
- 상세 페이지에서는 방금 바꾼 값이 보이는데 리스트로 돌아가면 이전 상태예요
- 새로고침을 몇 번 하거나 조금 기다리면 목록도 맞아지는데 직후에는 안 바뀌어요
- 같은 데이터를 보는 것 같은데 관리자 목록과 사용자 목록의 반영 시점이 달라 보여요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- database/transaction-basics
- database/read-after-write-routing-decision-guide
next_docs:
- database/cache-replica-split-read-inconsistency
- database/replica-lag-read-after-write-strategies
- database/incremental-summary-table-refresh-watermark
- database/summary-drift-detection-bounded-rebuild
linked_paths:
- contents/database/cache-replica-split-read-inconsistency.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/read-after-write-routing-decision-guide.md
- contents/database/incremental-summary-table-refresh-watermark.md
- contents/database/summary-drift-detection-bounded-rebuild.md
- contents/database/roomescape-admin-reservation-list-pagination-stability-bridge.md
confusable_with:
- database/payment-succeeded-but-order-not-visible-symptom-router
- database/cache-replica-split-read-inconsistency
- database/pagination-duplicates-missing-symptom-router
forbidden_neighbors: []
expected_queries:
- 수정은 됐는데 목록만 옛값으로 보이면 어디부터 의심해야 해?
- 상세에서는 최신인데 리스트에서는 예전 값일 때 원인을 어떻게 나눠?
- save 는 성공했는데 list 화면 반영만 늦으면 cache 문제야 replica 문제야?
- 업데이트 직후 관리자 목록과 사용자 목록이 다르게 보일 때 무슨 문서로 가야 해?
- 수정 후 새로고침해야 목록이 바뀌는 현상을 projection 지연과 stale read로 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 수정 저장은 성공했는데 목록 화면만 예전 상태로 남는 학습자 증상을
  cache stale, replica lag, projection이나 summary refresh 지연, 목록 조회와
  상세 조회의 source split으로 나눠 주는 symptom_router다. 상세는 바뀌었는데
  리스트는 안 바뀜, save success 뒤 list old data, 몇 초 뒤에는 맞아짐, 관리자와
  사용자 목록 반영 시점이 다름 같은 자연어 표현이 목록 freshness 분기와 매핑된다.
---

# 수정했는데 목록은 옛값이에요 원인 라우터

## 한 줄 요약

> 수정 직후 목록만 옛값이면 "업데이트가 실패했다"보다, 목록이 상세와 다른 읽기 경로나 다른 갱신 파이프라인을 보고 있을 가능성이 더 크다.

## 가능한 원인

1. 목록은 cache나 replica를 읽고, 상세는 primary나 더 신선한 경로를 읽는다. 같은 entity를 본다고 느껴도 실제 source가 다르면 상세는 최신인데 목록은 몇 초 늦을 수 있다. 이 갈래는 [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md)와 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)로 이어진다.
2. 목록이 원본 row가 아니라 projection, summary table, 읽기 전용 집계를 본다. 수정 commit은 끝났지만 목록용 파생 상태가 아직 따라오지 않았으면 상세는 바뀌고 리스트는 그대로 남는다. 이 경우는 [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)와 [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)로 가서 refresh 경계와 watermark를 먼저 본다.
3. 직후 조회에만 freshness 보장이 빠져 있다. 수정 성공 뒤 첫 목록 조회를 일반 read path로 보내면 사용자는 "save는 됐는데 list만 안 바뀜"으로 느낀다. 이때는 [Read-After-Write 라우팅 결정 가이드](./read-after-write-routing-decision-guide.md)로 가서 primary fallback이나 짧은 strict read window가 필요한지 고른다.
4. 문제의 본질이 stale read가 아니라 목록 절단 규약이다. 수정 이후 첫 페이지에서만 항목 위치가 밀리거나 사라져서 "안 바뀐 것처럼" 보일 수 있다. 새로고침할 때 위치가 바뀌거나 페이지 경계가 흔들리면 [roomescape 관리자 예약 목록 페이지네이션 ↔ 안정 정렬과 window drift 브릿지](./roomescape-admin-reservation-list-pagination-stability-bridge.md) 쪽을 본다.

## 빠른 자기 진단

1. 상세 조회와 목록 조회가 같은 데이터 소스인지 먼저 본다. 상세는 최신인데 목록만 늦으면 source split 가능성이 높다.
2. 몇 초 뒤나 새로고침 뒤에 목록이 맞아지면 write 실패보다 replica lag, cache invalidate 지연, projection refresh 지연을 먼저 의심한다.
3. 목록이 원본 테이블 직접 조회인지, summary table이나 read model인지 확인한다. 파생 상태라면 watermark와 refresh job 경계가 핵심이다.
4. 첫 페이지에서만 안 보이거나 위치가 흔들리면 stale 문제가 아니라 pagination 정렬 계약일 수 있다. 이 경우 freshness보다 stable order를 먼저 본다.

## 다음 학습

- cache와 replica 중 어느 쪽이 옛값을 주는지 먼저 가르고 싶다면 [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md)를 본다.
- 수정 직후 첫 조회에 어떤 strict read 전략이 필요한지 정하고 싶다면 [Read-After-Write 라우팅 결정 가이드](./read-after-write-routing-decision-guide.md)로 이어간다.
- 목록이 projection이나 summary table이라면 [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)와 [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)을 함께 본다.
- roomescape 같은 관리자 목록에서 사실은 페이지 경계가 흔들린 것인지 확인하려면 [roomescape 관리자 예약 목록 페이지네이션 ↔ 안정 정렬과 window drift 브릿지](./roomescape-admin-reservation-list-pagination-stability-bridge.md)를 읽는다.
