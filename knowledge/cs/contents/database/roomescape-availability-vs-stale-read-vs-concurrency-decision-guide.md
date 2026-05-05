---
schema_version: 3
title: roomescape 예약 가능 시간/직후 조회 문제 결정 가이드
concept_id: database/roomescape-availability-vs-stale-read-vs-concurrency-decision-guide
canonical: false
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/roomescape
review_feedback_tags:
- available-times-vs-stale-read
- post-create-freshness-vs-concurrency
- availability-debug-split
aliases:
- roomescape 예약 가능 시간 문제 결정 가이드
- roomescape available times chooser
- 예약 가능 시간 조회와 직후 재조회 구분
- availability vs stale read vs concurrency
- 가능 시간은 열려 보이는데 생성은 실패
- 예약 직후 조회가 이상할 때 어디부터 볼까
- roomescape 예약 디버깅 분기표
symptoms:
- roomescape에서 가능한 시간은 열려 보이는데 예약 생성은 충돌로 실패해요
- 예약을 만든 직후 목록이나 가능 시간이 이전 상태처럼 보여서 쿼리 문제인지 헷갈려요
- 리뷰어가 anti-join 버그와 recent write freshness와 동시성 문제를 먼저 갈라 보라고 했어요
intents:
- comparison
- troubleshooting
- mission_bridge
prerequisites:
- database/transaction-basics
- database/read-after-write-routing-decision-guide
next_docs:
- database/roomescape-available-times-empty-cause-router
- database/roomescape-reservation-create-read-after-write-bridge
- database/roomescape-reservation-concurrency-bridge
- database/roomescape-available-times-active-predicate-antijoin-bridge
linked_paths:
- contents/database/roomescape-available-times-empty-cause-router.md
- contents/database/roomescape-reservation-create-read-after-write-bridge.md
- contents/database/roomescape-reservation-concurrency-bridge.md
- contents/database/roomescape-available-times-active-predicate-antijoin-bridge.md
- contents/database/roomescape-reservation-cancel-reschedule-active-predicate-bridge.md
confusable_with:
- database/roomescape-available-times-empty-cause-router
- database/roomescape-reservation-create-read-after-write-bridge
- database/roomescape-reservation-concurrency-bridge
- database/roomescape-available-times-active-predicate-antijoin-bridge
forbidden_neighbors:
- contents/database/roomescape-reservation-create-read-after-write-bridge.md
- contents/database/roomescape-available-times-active-predicate-antijoin-bridge.md
expected_queries:
- roomescape에서 가능 시간 조회는 열려 있는데 실제 저장만 막히면 어떤 종류 문제부터 나눠 봐야 해?
- 예약 직후 첫 새로고침만 이전 값이면 조회 SQL보다 freshness 경로를 먼저 의심하는 기준이 뭐야?
- 같은 슬롯이 비어 보였다가 생성에서만 터질 때 anti-join 실수와 write-time 경쟁을 어떻게 구분해?
- 가능한 시간 목록이 이상한지, 방금 쓴 결과를 못 읽는 건지, 동시 요청 충돌인지 빠르게 가르는 질문을 알려줘
- roomescape 예약 디버깅에서 조회 버그와 read-after-write와 동시성 중 어디로 보내야 할지 결정하는 표가 필요해
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 예약 가능 시간이 비어 보이거나 열려 보이는데
  저장은 막히고, 예약 직후 조회만 이전 상태처럼 보이는 장면을 anti-join 의미 오류,
  recent-write freshness 부족, write-time 동시성 충돌로 가르는 chooser다. 가능한
  시간 조회가 이상함, 첫 새로고침만 틀림, 생성에서만 conflict 남, active predicate와
  read-after-write와 concurrency를 어떻게 나누지 같은 자연어 paraphrase가 이
  문서의 결정 매트릭스에 매핑된다.
---

# roomescape 예약 가능 시간/직후 조회 문제 결정 가이드

## 한 줄 요약

> 화면이 이상한지, 방금 쓴 결과를 아직 못 읽는지, 실제로 동시에 같은 슬롯을 두 요청이 다투는지부터 갈라야 roomescape 예약 디버깅이 빨라진다.

## 결정 매트릭스

| 먼저 보이는 장면 | 더 가까운 문서 | 왜 그쪽이 먼저인가 |
|---|---|---|
| 가능한 시간이 하루 통째로 비거나 취소한 슬롯이 계속 막혀 보임 | `roomescape 예약 가능 시간이 안 보여요 원인 라우터` | 조회 SQL, `LEFT JOIN` 조건 위치, active predicate가 blocker를 너무 넓게 잡았을 가능성이 크다 |
| 예약 생성은 성공했는데 직후 목록이나 가능 시간만 잠깐 옛값을 보여 줌 | `roomescape 예약 생성 직후 재조회 ↔ Read-After-Write 브릿지` | 저장 실패보다 post-write read freshness가 흔들린 장면에 가깝다 |
| 가능 시간은 열려 보였는데 생성 시점에만 conflict나 duplicate가 남 | `같은 시간대 예약 동시 요청 — 락 vs 유니크 제약 vs 낙관적 락 결정` | 조회 화면과 별개로 write-time arbitration surface에서 승자를 가르는 문제다 |
| 취소나 변경 이후에만 가능 시간 판정이 자꾸 뒤틀림 | `roomescape 예약 가능 시간 조회 ↔ anti-join과 active predicate 브릿지` | blocker에서 빠져야 할 상태 정의와 anti-join 조건이 맞물려 있는지 먼저 봐야 한다 |

짧게 외우면, "항상 비어 보임"은 조회 의미, "직후만 틀림"은 freshness, "생성에서만 터짐"은 동시성 축이다.

## 흔한 오선택

`가능 시간이 열려 보였으니 동시성 문제는 아니다`라고 단정하는 오선택이 흔하다.
목록 API는 읽기 truth를 보여 줄 뿐이고, 실제 저장은 `UNIQUE`, slot row, lock 같은 다른 arbitration surface에서 승자를 정할 수 있다.

반대로 예약 직후 한 번만 옛값이 보였는데도 조회 SQL부터 갈아엎는 경우도 많다.
새로고침 한 번 뒤에는 정상이라면 anti-join 버그보다 read-after-write 보장 부족이 더 직접적인 설명일 수 있다.

또 `LEFT JOIN` 조건 위치 문제를 단순한 race condition으로 몰아가는 경우도 있다.
취소된 예약을 계속 blocker로 읽거나 `WHERE`에서 `NULL` 행을 지워 버리면, 동시 요청이 없어도 가능한 시간이 통째로 사라져 보인다.

## 다음 학습

- 가능 시간 조회 SQL과 blocker 정의부터 점검하려면 [roomescape 예약 가능 시간이 안 보여요 원인 라우터](./roomescape-available-times-empty-cause-router.md)를 본다.
- 저장은 됐는데 직후 조회만 늦다면 [roomescape 예약 생성 직후 재조회 ↔ Read-After-Write 브릿지](./roomescape-reservation-create-read-after-write-bridge.md)로 이어간다.
- 생성 단계 승자 결정 방식을 다시 고르려면 [같은 시간대 예약 동시 요청 — 락 vs 유니크 제약 vs 낙관적 락 결정](./roomescape-reservation-concurrency-bridge.md)을 읽는다.
- active predicate와 anti-join 의미를 roomescape 예시로 다시 묶으려면 [roomescape 예약 가능 시간 조회 ↔ anti-join과 active predicate 브릿지](./roomescape-available-times-active-predicate-antijoin-bridge.md)를 본다.
