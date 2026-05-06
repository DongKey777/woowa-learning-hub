---
schema_version: 3
title: NOWAIT vs SKIP LOCKED vs 짧은 lock timeout 결정 가이드
concept_id: database/nowait-vs-skip-locked-vs-short-lock-timeout-decision-guide
canonical: false
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
  - skip-locked-vs-nowait
  - lock-budget-vs-queue-claim
  - busy-vs-work-stealing
aliases:
  - nowait vs skip locked vs short lock timeout
  - skip locked or nowait
  - lock budget queue claim chooser
  - work stealing vs fail fast lock choice
  - 행 잠금 대기 대신 건너뛰기 선택
  - busy로 끝낼지 다음 row를 집을지
  - queue claim 락 동작 선택
  - skip locked nowait timeout 차이
symptoms:
  - 잠긴 row를 만나면 바로 실패해야 하는지 다른 row를 집어야 하는지 조금 기다려야 하는지 기준이 흐린다
  - SKIP LOCKED와 NOWAIT를 둘 다 대기 안 하는 옵션 정도로만 외워서 queue 동작이 섞인다
  - 짧은 lock timeout을 work stealing 대체재처럼 써도 되는지 리뷰에서 자꾸 막힌다
intents:
  - comparison
  - design
  - troubleshooting
prerequisites:
  - database/lock-basics
  - database/transaction-basics
next_docs:
  - database/for-update-vs-advisory-lock-vs-lease-fencing-decision-guide
  - database/already-exists-vs-busy-vs-retryable-decision-guide
  - database/queue-claim-skip-locked-fairness
linked_paths:
  - contents/database/nowait-vs-short-lock-timeout-busy-guide.md
  - contents/database/queue-claim-skip-locked-fairness.md
  - contents/database/postgresql-55p03-nowait-vs-lock-timeout-beginner-card.md
  - contents/database/busy-fail-fast-vs-one-short-retry-card.md
  - contents/database/for-update-vs-advisory-lock-vs-lease-fencing-decision-guide.md
confusable_with:
  - database/for-update-vs-advisory-lock-vs-lease-fencing-decision-guide
  - database/already-exists-vs-busy-vs-retryable-decision-guide
  - database/queue-claim-skip-locked-fairness
forbidden_neighbors:
  - contents/database/nowait-vs-short-lock-timeout-busy-guide.md
expected_queries:
  - 잠겨 있으면 바로 실패해야 하는지 다른 row를 집어야 하는지 조금 기다렸다 포기해야 하는지 어떻게 고르지?
  - DB queue에서 SKIP LOCKED를 쓰는 상황과 NOWAIT를 쓰는 상황을 한 표로 비교해줘
  - 같은 락 경쟁인데 fail-fast, work stealing, 짧은 대기 예산을 어떤 질문으로 먼저 나눠?
  - 예약이나 job claim에서 막힌 row를 건너뛸지 바로 busy로 돌릴지 판단 기준이 뭐야?
  - FOR UPDATE 뒤에 NOWAIT를 붙이는 경우와 SKIP LOCKED로 다른 일을 찾는 경우는 왜 목적이 달라?
  - 짧은 lock timeout을 SKIP LOCKED 대체재처럼 보면 어디서 틀어져?
contextual_chunk_prefix: |
  이 문서는 데이터베이스에서 잠긴 row를 만났을 때 NOWAIT, SKIP LOCKED,
  짧은 lock timeout을 모두 대기 안 함으로만 섞지 않도록 fail-fast, work
  stealing, bounded wait를 갈라 주는 beginner chooser다. 잠기면 바로 busy로
  끝낼지, 다른 작업을 집으러 갈지, 몇 밀리초만 기다려 볼지, queue claim과
  기존 row 보호를 같은 문제로 보면 어디서 틀어지는지 같은 자연어 질문이 이
  문서의 결정 기준에 매핑된다.
---

# NOWAIT vs SKIP LOCKED vs 짧은 lock timeout 결정 가이드

## 한 줄 요약

> 지금 보던 row를 포기하고 바로 실패할 거면 `NOWAIT`, 다른 후보 일을 계속 집어야 하면 `SKIP LOCKED`, 같은 row를 조금만 기다려 보고 포기할 거면 짧은 `lock timeout`을 먼저 본다.

## 결정 매트릭스

| 지금 먼저 지키려는 것 | 1차 선택 | 왜 이 선택이 맞나 |
|---|---|---|
| 현재 보고 있는 row가 잠겨 있으면 즉시 `busy`나 fail-fast로 닫기 | `NOWAIT` | 같은 row를 계속 보되 대기 시간을 0에 가깝게 두는 정책이다 |
| queue에서 잠긴 작업을 건너뛰고 다른 `READY` row를 계속 처리 | `SKIP LOCKED` | 목표가 현재 row 보호보다 throughput 유지와 work stealing이기 때문이다 |
| 같은 row가 곧 풀릴 수 있어서 아주 짧게만 기다려 볼 가치가 있음 | 짧은 `lock timeout` | 실패 전 대기 예산을 수 ms~수십 ms로 제한하는 bounded wait다 |
| 긴 작업 ownership이나 stale worker 차단까지 필요 | 셋 다 아님 | 이 셋은 row 대기 방식이고 lease/fencing 같은 장기 소유권 규칙이 따로 필요하다 |

짧게 기억하면 `NOWAIT`는 fail-fast, `SKIP LOCKED`는 next-candidate 탐색, 짧은 `lock timeout`은 same-row bounded wait다.

## 흔한 오선택

가장 흔한 오선택은 `SKIP LOCKED`를 `NOWAIT`의 성능 좋은 버전으로 보는 것이다. 학습자 표현으로는 "어차피 안 기다릴 거면 둘 다 같은 것 아닌가?"에 가깝다. 하지만 `NOWAIT`는 지금 보던 row를 바로 포기하는 정책이고, `SKIP LOCKED`는 다른 row를 계속 집어 queue를 비우는 정책이라 목적이 다르다.

짧은 `lock timeout`을 `SKIP LOCKED` 대체재로 두는 것도 자주 틀린다. `lock timeout`은 여전히 같은 row를 기다리는 모델이라 queue fairness와 claim ordering이 남고, `SKIP LOCKED`처럼 다른 후보로 넘어가 throughput을 올려 주지 않는다.

반대로 기존 주문 row 수정처럼 보호 대상이 이미 뚜렷한데도 `SKIP LOCKED`를 먼저 찾는 것도 과하다. 이 장면은 queue claim보다 row 보호와 실패 언어가 더 중요해서 `NOWAIT`나 짧은 `lock timeout`, 또는 그냥 `FOR UPDATE` 자체를 먼저 봐야 한다.

## 다음 학습

`NOWAIT`와 짧은 `lock timeout`을 둘 다 `busy` 축으로 읽는 이유를 더 짧게 붙잡으려면 [NOWAIT와 짧은 lock timeout은 왜 자동 retry보다 busy에 더 가깝게 볼까?](./nowait-vs-short-lock-timeout-busy-guide.md)를 보면 된다.

`SKIP LOCKED`가 throughput은 올리지만 fairness와 starvation을 남기는 이유는 [Queue Claim with SKIP LOCKED, Fairness, and Starvation Trade-offs](./queue-claim-skip-locked-fairness.md)로 이어서 보면 된다.

row lock, 작업 진입 게이트, 긴 실행 ownership을 한 장에서 더 넓게 비교하려면 [FOR UPDATE Row Lock vs Advisory Lock vs Lease/Fencing 결정 가이드](./for-update-vs-advisory-lock-vs-lease-fencing-decision-guide.md)와 [Already Exists vs Busy vs Retryable 결정 가이드](./already-exists-vs-busy-vs-retryable-decision-guide.md)를 다음 문서로 잡으면 된다.
