---
schema_version: 3
title: Lost Update vs Write Skew vs Phantom 결정 가이드
concept_id: database/lost-update-vs-write-skew-vs-phantom-chooser
canonical: false
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/roomescape
- missions/shopping-cart
- missions/baseball
review_feedback_tags:
- anomaly-classification-drift
- same-row-vs-set-invariant
- absence-check-race-misread
aliases:
- lost update vs write skew vs phantom
- 동시성 이상 현상 구분 가이드
- same row different row new row 차이
- overwrite vs set invariant vs absence check
- anomaly chooser lost update write skew phantom
- 어떤 anomaly인지 먼저 가르는 문서
symptoms:
- 같은 동시성 버그를 매번 lost update라고 부르는데 리뷰에서는 phantom이나 write skew라고 한다
- 같은 row 덮어쓰기와 집합 규칙 깨짐과 빈 범위 판단 실패가 한 덩어리로 들린다
- version column으로 막을 문제인지 guard row나 serializable로 가야 할 문제인지 분류가 안 된다
intents:
- comparison
- troubleshooting
- design
prerequisites:
- database/transaction-basics
- database/transaction-isolation-basics
next_docs:
- database/unique-vs-version-cas-vs-for-update-chooser
- database/read-committed-vs-repeatable-read-vs-serializable-decision-guide
- database/constraint-first-booking-primer
linked_paths:
- contents/database/lost-update-detection-patterns.md
- contents/database/write-skew-phantom-read-case-studies.md
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/unique-vs-version-cas-vs-for-update-decision-guide.md
- contents/database/read-committed-vs-repeatable-read-vs-serializable-decision-guide.md
- contents/database/constraint-first-booking-primer.md
- contents/database/phantom-safe-booking-patterns-primer.md
confusable_with:
- database/lost-update-detection-patterns
- database/range-invariant-enforcement-write-skew-phantom
- database/read-committed-vs-repeatable-read-vs-serializable-decision-guide
forbidden_neighbors:
- contents/database/read-committed-vs-repeatable-read-vs-serializable-decision-guide.md
expected_queries:
- 재고가 꼬였는데 이게 같은 row 덮어쓰기인지 범위 문제인지 어떻게 나눠 봐?
- 두 요청이 각자 다른 row를 바꿨는데 전체 규칙이 깨졌다면 어떤 anomaly로 보는 게 맞아?
- 비어 있다고 보고 insert했는데 뒤늦게 겹치는 row가 생긴 상황은 lost update가 아니지?
- version check로 끝낼 문제와 guard row나 serializable까지 봐야 할 문제를 무엇으로 구분해?
- same row overwrite, different row invariant break, new row insert race를 한 번에 정리한 설명이 필요해
contextual_chunk_prefix: |
  이 문서는 학습자가 lost update, write skew, phantom을 모두 "동시성
  문제"로만 뭉뚱그릴 때 same row overwrite인지, different row 집합
  규칙 붕괴인지, 빈 범위라고 믿은 사이 새 row가 끼어든 것인지 먼저
  가르는 beginner chooser다. version column으로 닫히는지, guard row나
  serializable이 필요한지, overlap check가 왜 lost update가 아닌지 같은
  자연어 질문이 결정 매트릭스와 오선택 패턴에 바로 매핑되도록 작성됐다.
---

# Lost Update vs Write Skew vs Phantom 결정 가이드

## 한 줄 요약

> 같은 existing row가 조용히 덮이면 `lost update`, 서로 다른 row는 멀쩡히 저장됐는데 전체 규칙이 깨지면 `write skew`, 비어 있다고 믿은 범위 사이로 새 row가 들어오면 `phantom`을 먼저 본다.

## 결정 매트릭스

| 지금 깨진 것 | `lost update` | `write skew` | `phantom` |
|---|---|---|---|
| 마지막에 무엇이 충돌했나 | 같은 existing row 최종값 | 서로 다른 existing row들의 조합 | 없다고 믿은 범위에 새 row |
| 학습자 기억법 | same row | different row | new row |
| 흔한 장면 | 재고 수량, 프로필, 카운터를 읽고 다시 저장 | 당직 1명 유지, 총합 capacity, 활성 상태 개수 | 겹치는 예약 없음 확인 후 insert |
| 먼저 떠올릴 보호 장치 | version CAS, atomic update, `FOR UPDATE` | guard row, 조건부 집계 update, `SERIALIZABLE` | `UNIQUE`로 환원, exclusion/slotization, predicate-safe 보호 |
| 리뷰에서 자주 나오는 말 | "앞선 저장이 덮였다" | "각 row는 맞는데 규칙이 깨졌다" | "absence check가 새었다" |

짧게 외우면 `lost update`는 저장 충돌, `write skew`는 집합 규칙 충돌, `phantom`은 부재 판단 충돌이다.

## 흔한 오선택

둘 다 오래된 조회를 보고 결정했다는 이유로 `lost update`로 묶는 오선택이 많다. 학습자 표현으로는 "둘 다 stale read니까 같은 문제 아닌가?"에 가깝다. 하지만 같은 row를 덮었는지부터 봐야 한다. 서로 다른 row를 바꿨다면 `write skew`나 `phantom` 쪽이다.

예약 겹침을 `write skew` 하나로만 닫는 것도 흔하다. "겹치는 예약이 없다고 보고 insert했어요"라면 핵심은 기존 row 덮어쓰기가 아니라 빈 범위 판단 사이로 새 row가 들어온 것이다. 이때는 `phantom` 관점에서 range 보호 장치를 먼저 떠올리는 편이 정확하다.

`SERIALIZABLE`만 붙이면 셋 다 같은 방식으로 해결된다고 보는 것도 오선택이다. 같은 row overwrite는 version CAS나 원자적 update가 더 직접적일 수 있고, 반대로 집합 규칙이나 overlap 규칙은 guard row나 constraint로 쓰기 충돌 지점을 만드는 쪽이 더 설명력이 높다.

## 다음 학습

같은 row overwrite가 중심이면 [UNIQUE vs Version CAS vs FOR UPDATE 결정 가이드](./unique-vs-version-cas-vs-for-update-decision-guide.md)와 [Lost Update Detection Patterns](./lost-update-detection-patterns.md)로 내려가면 된다.

서로 다른 row 조합이 규칙을 깨뜨리는 장면이면 [Read Committed vs Repeatable Read vs Serializable 결정 가이드](./read-committed-vs-repeatable-read-vs-serializable-decision-guide.md)와 [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)를 이어서 본다.

비어 있는 범위 판단과 예약 겹침이 핵심이면 [Constraint-First Booking Primer](./constraint-first-booking-primer.md)와 [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)로 이어 가면 된다.
