---
schema_version: 3
title: Offset Pagination vs Seek Pagination 결정 가이드
concept_id: database/offset-vs-seek-pagination-decision-guide
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- offset-vs-seek-choice
- stable-ordering
- cursor-contract
aliases:
- offset vs seek pagination
- limit offset vs keyset pagination
- cursor pagination chooser
- pagination strategy chooser
- infinite scroll pagination choice
- admin list pagination choice
- 페이지네이션 offset seek 차이
- cursor pagination 언제 써
symptoms:
- 목록은 보이는데 뒤 페이지로 갈수록 느려지고 중복이나 누락까지 보여서 어떤 pagination 방식을 골라야 할지 모르겠다
- 관리자 페이지처럼 페이지 번호 점프도 필요하고 무한 스크롤처럼 안정성도 원하는데 무엇을 우선해야 하는지 헷갈린다
- 리뷰어가 offset 대신 seek를 보라고 했는데 왜 그런지 감이 안 온다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/sql-relational-modeling-basics
- database/database-first-step-bridge
next_docs:
- database/pagination-duplicates-missing-symptom-router
- database/roomescape-admin-reservation-list-pagination-stability-bridge
- database/read-after-write-routing-decision-guide
linked_paths:
- contents/database/pagination-offset-vs-seek.md
- contents/database/pagination-duplicates-missing-symptom-router.md
- contents/database/roomescape-admin-reservation-list-pagination-stability-bridge.md
- contents/database/covering-index-composite-ordering.md
- contents/database/replica-read-routing-anomalies.md
confusable_with:
- database/pagination-duplicates-missing-symptom-router
- database/roomescape-admin-reservation-list-pagination-stability-bridge
- database/read-after-write-routing-decision-guide
forbidden_neighbors:
- contents/database/roomescape-admin-reservation-list-pagination-stability-bridge.md
- contents/database/read-after-write-routing-decision-guide.md
expected_queries:
- 관리자 목록처럼 몇 페이지로 바로 점프해야 하면 offset과 seek 중 무엇이 더 자연스러워?
- 무한 스크롤에서 새 글이 끼어들어도 덜 흔들리게 하려면 offset보다 다른 방식을 먼저 봐야 해?
- LIMIT OFFSET이 왜 뒤 페이지에서 갑자기 비싸지는지 선택 기준으로 설명해줘
- cursor pagination을 쓴다고 항상 안정적인 건 아니라는데 어떤 전제가 더 필요해?
- 페이지 번호 UX와 deep pagination 성능 사이에서 무엇을 먼저 포기해야 하는지 빠르게 정리해줘
- roomescape 관리자 목록과 피드형 목록이 왜 pagination 선택이 다른지 한 번에 보고 싶어
contextual_chunk_prefix: |
  이 문서는 목록 조회에서 OFFSET pagination과 seek pagination 중 무엇을
  골라야 하는지 빠르게 결정하게 돕는 beginner chooser다. 관리자 페이지
  번호 점프, 무한 스크롤, deep pagination, 중복·누락, stable order,
  cursor 계약, 뒤 페이지가 느림 같은 자연어 표현이 결정 매트릭스와
  오선택 패턴에 연결되도록 작성됐다.
---

# Offset Pagination vs Seek Pagination 결정 가이드

## 한 줄 요약

> 페이지 번호 점프와 단순 구현이 먼저면 `OFFSET`, 다음 페이지만 빠르고 안정적으로 이어 가는 UX가 먼저면 `seek`, 중복·누락이 이미 아프다면 방식보다 먼저 stable order와 cursor 계약을 같이 고정한다.

## 결정 매트릭스

| 지금 더 중요한 것 | 1차 선택 | 이유 |
| --- | --- | --- |
| 관리 화면처럼 `7페이지`로 바로 점프하는 UX | `OFFSET` | 페이지 번호와 `LIMIT/OFFSET` 모델이 가장 직접적으로 맞는다 |
| 피드, 로그, 무한 스크롤처럼 "다음 더 보기"만 빠르면 됨 | `seek` | 앞 row를 버리지 않고 마지막 key 다음 위치로 바로 이어 간다 |
| 뒤 페이지로 갈수록 latency가 눈에 띄게 커짐 | `seek` 우선 검토 | deep pagination에서 버리는 row 수가 커질수록 `OFFSET` 비용이 누적된다 |
| 새 row가 끼어들 때 중복·누락이 잘 보임 | `seek` + stable order | `OFFSET` window drift에 취약하고, seek도 정렬 key가 불안정하면 흔들린다 |
| 기존 관리자 UI를 빨리 붙여야 하고 데이터량도 아직 작음 | `OFFSET` 시작 가능 | 다만 `ORDER BY created_at, id` 같은 tie-breaker와 전환 시점을 미리 정해 둔다 |

짧게 기억하면 `OFFSET`은 페이지 번호 UX, `seek`는 연속 읽기 UX에 가깝다. 다만 둘 중 무엇을 택하든 정렬 기준이 유일하지 않으면 목록은 계속 흔들린다.

## 흔한 오선택

가장 흔한 오선택은 무한 스크롤인데도 익숙하다는 이유로 `OFFSET`을 계속 쓰는 경우다. 초반에는 멀쩡해 보여도 새 row가 중간에 들어오면 다음 페이지 경계가 밀려 중복·누락이 바로 보이기 시작한다.

반대로 `seek`를 골랐다고 끝난 것도 아니다. `ORDER BY created_at DESC`만 두고 cursor에는 `created_at`만 넣으면 동률 row를 안정적으로 넘기지 못한다. 학습자 표현으로는 "cursor인데도 어떤 글이 사라져요"가 여기에 해당한다.

또 하나는 성능 문제만 보고 선택하는 경우다. 관리자 페이지에서 운영자가 특정 페이지로 즉시 점프해야 한다면 `seek`가 더 빠르더라도 UX 비용이 커질 수 있다. 이때는 `OFFSET`을 쓰되 stable order, 적절한 인덱스, 전환 한계를 함께 설명하는 편이 맞다.

## 다음 학습

중복·누락 증상부터 원인을 가르고 싶으면 `페이지네이션 중복/누락 원인 라우터`로 이어 간다.

roomescape 관리자 목록처럼 리뷰 코멘트와 미션 장면으로 연결하고 싶으면 `roomescape 관리자 예약 목록 페이지네이션 ↔ 안정 정렬과 window drift 브릿지`를 본다.

페이지를 자르는 방식보다 write 직후 다른 read 경로가 문제인지 헷갈리면 `Read-After-Write 라우팅 결정 가이드`와 `Replica Read Routing Anomalies와 세션 일관성`을 함께 보는 편이 안전하다.
