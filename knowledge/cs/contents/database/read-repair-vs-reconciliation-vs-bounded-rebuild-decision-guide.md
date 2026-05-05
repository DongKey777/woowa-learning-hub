---
schema_version: 3
title: Read Repair vs Reconciliation vs Bounded Rebuild 결정 가이드
concept_id: database/read-repair-vs-reconciliation-vs-bounded-rebuild-decision-guide
canonical: false
category: database
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- failover-repair-scope
- stale-projection-recovery-choice
- rebuild-boundary-choice
aliases:
- read repair vs reconciliation vs bounded rebuild
- stale 데이터 복구 선택 가이드
- failover 복구 범위 결정
- projection repair chooser
- summary drift repair choice
- 부분 복구 vs 재계산
- 캐시 보정 vs 범위 재검증
symptoms:
- 일부 요청만 옛값을 보는데 read repair로 끝낼지 별도 reconciliation job이 필요한지 헷갈린다
- 요약 테이블 값이 틀렸을 때 한 건 보정, 범위 스캔, bounded rebuild 중 무엇을 먼저 선택할지 모르겠다
- failover 뒤 stale cache와 실제 데이터 드리프트를 같은 복구 절차로 다루고 있다
intents:
- comparison
- troubleshooting
- design
prerequisites:
- database/failover-after-old-new-flip-symptom-router
- database/incremental-summary-table-refresh-watermark
- database/summary-drift-detection-bounded-rebuild
next_docs:
- database/read-repair-reconciliation-after-failover
- database/cdc-gap-repair-reconciliation-playbook
- database/summary-drift-detection-bounded-rebuild
linked_paths:
- contents/database/read-repair-reconciliation-after-failover.md
- contents/database/cdc-gap-repair-reconciliation-playbook.md
- contents/database/summary-drift-detection-bounded-rebuild.md
- contents/database/failover-after-old-new-flip-symptom-router.md
- contents/database/incremental-summary-table-refresh-watermark.md
confusable_with:
- database/read-repair-reconciliation-after-failover
- database/cdc-gap-repair-reconciliation-playbook
- database/summary-drift-detection-bounded-rebuild
forbidden_neighbors:
- contents/database/read-repair-reconciliation-after-failover.md
- contents/database/summary-drift-detection-bounded-rebuild.md
expected_queries:
- failover 뒤 stale read가 보일 때 read repair랑 reconciliation job 중 어디서 시작해?
- 캐시 한두 건만 틀린데 bounded rebuild까지 해야 하는 상황이야?
- summary table 값이 어긋났을 때 부분 재계산과 reconciliation을 어떻게 나눠 봐?
- read repair는 요청 경로에서 고치고 reconciliation은 배치라는데 실제 선택 기준이 뭐야?
- failover 후 일부 화면만 옛값이면 전체 rebuild보다 먼저 확인할 복구 단계가 있어?
contextual_chunk_prefix: |
  이 문서는 학습자가 stale read, cache mismatch, summary drift를 한 묶음의
  "복구"로 생각할 때 read repair, reconciliation, bounded rebuild를 어디서
  갈라 봐야 하는지 설명하는 intermediate chooser다. failover 뒤 일부 요청만
  옛값, 캐시 몇 건만 틀림, summary bucket 전체가 어긋남, projection repair
  scope를 어디까지 잡아야 하나 같은 자연어 질문이 요청 경로 보정, 범위
  검증, 부분 재계산 선택 기준으로 이어지도록 작성됐다.
---

# Read Repair vs Reconciliation vs Bounded Rebuild 결정 가이드

## 한 줄 요약

> 한두 건의 stale read를 요청 흐름에서 바로잡는 건 `read repair`, 어느 범위가 틀렸는지 스캔하며 맞추는 건 `reconciliation`, 드리프트가 확인된 구간만 다시 계산하는 건 `bounded rebuild`로 나눠 본다.

## 결정 매트릭스

| 지금 보이는 문제 | 먼저 볼 선택지 | 왜 이쪽이 맞나 |
|---|---|---|
| 특정 요청에서 캐시 버전만 낡았고 DB 진실은 이미 확실하다 | `read repair` | 읽는 순간 최신 진실원으로 덮어쓰는 게 가장 작게 끝난다 |
| failover 뒤 어떤 aggregate들이 갈라졌는지 아직 범위를 모른다 | `reconciliation` | source of truth와 projection을 대조하며 손상 범위를 찾는 단계가 먼저다 |
| summary table의 특정 day bucket이 틀린 것이 확인됐다 | `bounded rebuild` | 영향 구간을 닫아 source에서 그 범위만 재계산하는 편이 빠르고 검증 가능하다 |
| stale 현상이 한두 건이 아니라 여러 projection으로 번진다 | `reconciliation` 후 필요 시 `bounded rebuild` | 먼저 어디가 틀렸는지 자른 뒤, 재계산 범위를 좁혀야 blast radius가 줄어든다 |
| 요청 경로에서 바로 고치면 write 폭증이나 잘못된 덮어쓰기가 걱정된다 | `read repair` 대신 배치성 `reconciliation` | 사용자 트래픽 경로보다 통제된 repair loop가 안전하다 |

짧게 기억하면 read repair는 "읽다가 한 건 고침", reconciliation은 "범위를 스캔하며 진실원과 대조", bounded rebuild는 "틀린 구간만 다시 만듦"이다.

## 흔한 오선택

가장 흔한 오선택은 stale cache 한두 건을 보고 곧바로 전체 rebuild로 뛰는 것이다. 학습자 표현으로는 "어차피 값이 틀렸으니 summary를 전부 다시 밀어야 하나?"에 가깝다. 하지만 진실원이 이미 확실하고 손상 범위가 국소적이면 read repair나 작은 reconciliation으로 끝날 일을 불필요하게 크게 만든다.

반대로 failover 뒤 일부 화면이 갈라졌는데 read repair만 붙이고 끝내는 것도 자주 틀린다. 요청 경로에서 보이는 row만 고치면 아직 읽히지 않은 나머지 stale projection은 그대로 남을 수 있다. 이 장면은 "읽는 김에 보정"보다 "어느 범위가 갈라졌는지 스캔"이 먼저다.

또 하나는 bounded rebuild를 reconciliation의 동의어처럼 쓰는 것이다. reconciliation은 손상 범위를 찾고 source와 비교하는 과정이고, bounded rebuild는 그 결과를 바탕으로 닫힌 구간을 다시 계산하는 실행 단계다. 범위를 모르는데 rebuild부터 시작하면 replay cutoff와 영향 범위 검증이 흔들린다.

## 다음 학습

failover 뒤 stale read와 projection 정리 흐름을 먼저 보고 싶으면 [Read Repair와 Failover Reconciliation](./read-repair-reconciliation-after-failover.md)와 [Failover 뒤 옛값/새값 번갈아 보임 원인 라우터](./failover-after-old-new-flip-symptom-router.md)를 이어서 보면 된다.

CDC gap이나 projection repair 경계를 더 엄밀하게 자르고 싶으면 [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)로 내려가면 된다.

summary table drift가 확인된 뒤 어떤 bucket만 다시 계산할지 알고 싶으면 [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)와 [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)를 다음 문서로 잡으면 된다.
