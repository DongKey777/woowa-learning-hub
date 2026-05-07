---
schema_version: 3
title: 정규화 vs 반정규화 vs Summary Table 결정 가이드
concept_id: database/normalization-vs-denormalization-vs-summary-table-decision-guide
canonical: true
category: database
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- read-model-choice
- source-of-truth-boundary
- premature-denormalization
aliases:
- normalization vs denormalization vs summary table
- 정규화 반정규화 summary table 선택
- join 느릴 때 구조 선택
- read model chooser
- source of truth vs projection chooser
- summary table 언제 쓰나
- 조회 느릴 때 반정규화만 하면 되나
symptoms:
- JOIN이 많아서 느린데 정규화를 풀지 summary table을 둘지 모르겠다
- 조회 화면이 무거워졌을 때 write model을 바꿔야 하는지 읽기 전용 테이블을 따로 둬야 하는지 헷갈린다
- 중복 저장이 싫은데 목록 성능이 안 나와서 어디까지 반정규화해야 할지 판단이 안 선다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/normalization-basics
- database/index-basics
- database/transaction-basics
next_docs:
- database/normalization-denormalization-tradeoffs
- database/incremental-summary-table-refresh-watermark
- database/summary-drift-detection-bounded-rebuild
linked_paths:
- contents/database/normalization-basics.md
- contents/database/normalization-denormalization-tradeoffs.md
- contents/database/incremental-summary-table-refresh-watermark.md
- contents/database/summary-drift-detection-bounded-rebuild.md
- contents/database/sql-reading-relational-modeling-primer.md
- contents/database/query-tuning-checklist.md
confusable_with:
- database/normalization-denormalization-tradeoffs
- database/incremental-summary-table-refresh-watermark
- database/summary-drift-detection-bounded-rebuild
forbidden_neighbors:
- contents/database/query-tuning-checklist.md
- contents/database/online-backfill-consistency.md
- contents/database/cdc-debezium-outbox-binlog.md
expected_queries:
- 조회가 느릴 때 정규화를 풀어야 하는지 summary table을 만들어야 하는지 어떻게 고르지?
- admin 목록 때문에 JOIN이 많은데 반정규화와 읽기 전용 집계 테이블 중 어디서 시작해야 해?
- source of truth는 유지하고 싶은데 화면 응답이 느리면 어떤 구조를 먼저 검토해?
- write model을 바꾸지 않고 조회만 빠르게 만들려면 반정규화보다 다른 선택지가 있어?
- 정규화, 반정규화, summary table을 읽기/쓰기 기준으로 빠르게 비교하고 싶어
- 중복 컬럼 추가와 별도 projection 테이블을 같은 선택으로 보면 왜 위험해?
contextual_chunk_prefix: |
  이 문서는 조회 성능 문제가 보일 때 정규화 유지, write model 안의 반정규화,
  별도 summary table 중 무엇을 먼저 선택할지 판단하게 돕는 intermediate
  chooser다. JOIN이 많아 느림, source of truth는 지키고 싶음, admin 목록만
  무거움, 중복 저장이 걱정됨, 읽기 최적화와 projection 분리를 어디서 나눌지
  헷갈림 같은 자연어 표현이 세 가지 선택지의 결정 기준으로 매핑된다.
---

# 정규화 vs 반정규화 vs Summary Table 결정 가이드

## 한 줄 요약

> 저장 진실을 단단히 지키는 게 먼저면 `정규화`, 같은 write row에 읽기 편의 컬럼을 조금 붙이는 수준이면 `반정규화`, 특정 화면의 읽기 비용을 별도 파이프라인으로 떼어내야 하면 `summary table`을 먼저 본다.

## 결정 매트릭스

| 지금 더 큰 문제 | 먼저 볼 선택지 | 이유 |
|---|---|---|
| 값이 여러 군데 어긋나면 바로 장애가 된다 | 정규화 | source of truth를 한곳에 두고 갱신 경로를 짧게 유지하는 편이 우선이다 |
| 같은 row를 읽을 때 JOIN 몇 개만 줄이면 충분하다 | 반정규화 | write model은 유지하면서 자주 같이 읽는 컬럼만 붙여 비용을 낮출 수 있다 |
| admin 목록, 통계, 대시보드처럼 반복 조회가 계속 무겁다 | summary table | 읽기 전용 projection으로 쿼리 복잡도와 p99를 따로 관리할 수 있다 |
| 아직 병목 원인이 인덱스인지 모델인지 불분명하다 | 정규화 유지 | 구조를 풀기 전에 query plan과 인덱스부터 확인하는 편이 안전하다 |
| freshness lag를 감수하더라도 읽기 SLA가 더 중요하다 | summary table | 늦어도 되는 범위를 명시하고 projection pipeline로 운영할 수 있다 |

정규화와 반정규화는 write model 안에서의 선택이고, summary table은 읽기 모델을 따로 세우는 선택이라는 점을 먼저 나눠서 보면 덜 헷갈린다.

## 흔한 오선택

### JOIN이 느리면 바로 반정규화

학습자 표현으로는 "테이블이 너무 많이 나뉘어서 느린 것 같아요"가 자주 나온다. 하지만 실제로는 인덱스 부재나 잘못된 필터 순서가 원인일 수 있다. 구조를 풀기 전에 query plan과 access path를 먼저 본다.

### 목록 화면 하나 때문에 write model 전체를 뜯어고침

"admin 페이지가 느리니 주문 row에 필요한 값을 다 붙이자"는 선택은 갱신 경로를 길게 만든다. 특정 화면만 문제면 summary table이 더 작은 변경으로 끝날 수 있다.

### summary table을 그냥 큰 반정규화로 이해

"어차피 중복 저장이면 같은 거 아닌가?"라고 보기 쉽다. 반정규화는 보통 같은 트랜잭션 안의 write model 중복이고, summary table은 refresh, watermark, drift 복구를 따로 운영해야 하는 projection이다.

### source of truth 없이 읽기 테이블을 먼저 신뢰

"대시보드 수치가 맞겠지"라고 두면 stale data가 조용히 거짓말한다. summary table을 고르면 freshness와 rebuild 경로까지 같이 설계해야 한다.

## 다음 학습

정규화와 반정규화의 기본 trade-off를 먼저 다시 잡으려면 `database/normalization-denormalization-tradeoffs`로, summary table을 골랐다면 refresh 경계는 `database/incremental-summary-table-refresh-watermark`, drift 복구는 `database/summary-drift-detection-bounded-rebuild`로 이어서 보면 된다.
