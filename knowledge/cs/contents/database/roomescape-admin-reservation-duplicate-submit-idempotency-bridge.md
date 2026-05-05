---
schema_version: 3
title: 'roomescape 관리자 예약 중복 제출 ↔ 멱등성 키와 UNIQUE 브릿지'
concept_id: database/roomescape-admin-reservation-duplicate-submit-idempotency-bridge
canonical: false
category: database
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- duplicate-submit
- idempotency-key
- replay-safe-reservation-create
aliases:
- roomescape 관리자 예약 중복 제출
- roomescape 예약 더블클릭 중복 생성
- roomescape 예약 생성 재전송 한 번만 처리
- 룸이스케이프 예약 요청 멱등성
- roomescape reservation idempotency
symptoms:
- roomescape 관리자 예약 추가 버튼을 두 번 눌렀더니 같은 예약이 두 번 잡힐까 불안해요
- 응답이 늦어서 예약 생성 요청을 다시 보냈는데 같은 요청을 한 번만 인정하려면 어떻게 해야 하나요
- 리뷰에서 PRG만으로는 부족하고 멱등성 키를 따로 보라고 했는데 왜인지 모르겠어요
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- spring/roomescape-admin-reservation-post-redirect-get-bridge
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- database/transaction-basics
next_docs:
- database/idempotency-key-and-deduplication
- database/roomescape-reservation-concurrency-bridge
- spring/roomescape-admin-reservation-post-redirect-get-bridge
- spring/roomescape-duplicate-reservation-sqlexception-translation-bridge
linked_paths:
- contents/database/idempotency-key-and-deduplication.md
- contents/database/roomescape-reservation-concurrency-bridge.md
- contents/spring/roomescape-admin-reservation-post-redirect-get-bridge.md
- contents/spring/roomescape-duplicate-reservation-sqlexception-translation-bridge.md
- contents/database/duplicate-key-fresh-read-classifier-mini-card.md
confusable_with:
- database/idempotency-key-and-deduplication
- database/roomescape-reservation-concurrency-bridge
- spring/roomescape-admin-reservation-post-redirect-get-bridge
- spring/roomescape-duplicate-reservation-sqlexception-translation-bridge
forbidden_neighbors: []
expected_queries:
- roomescape 관리자 예약 API에서 같은 생성 요청이 재전송돼도 예약을 한 번만 만들게 하려면 DB에서 뭘 둬야 해?
- 예약 추가 버튼 더블클릭 때문에 같은 요청이 두 번 들어올 때 PRG 말고 멱등성 키가 왜 따로 필요해?
- roomescape에서 같은 사용자의 같은 예약 생성 시도를 replay-safe 하게 처리하라는 리뷰는 무슨 뜻이야?
- 응답 timeout 뒤 예약 생성 POST를 다시 보내도 기존 결과를 돌려주려면 어떤 identity를 저장해야 해?
- roomescape 중복 제출과 서로 다른 두 사용자의 슬롯 경쟁은 왜 다른 문제로 읽어야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 예약 생성 POST가 더블클릭, timeout 뒤
  재전송, 브라우저 재시도 때문에 같은 의미로 두 번 들어오는 장면을 멱등성 키와
  UNIQUE 제약으로 설명하는 mission_bridge다. roomescape 예약 중복 제출, 같은
  요청 한 번만 인정, PRG와 idempotency 차이, replay-safe create, duplicate submit
  vs 슬롯 경쟁 같은 학습자 표현이 이 문서의 검색 표면이다.
---

# roomescape 관리자 예약 중복 제출 ↔ 멱등성 키와 UNIQUE 브릿지

## 한 줄 요약

> roomescape에서 예약 생성 한 번은 "같은 의미의 요청 하나"여야 한다. 브라우저나 네트워크가 같은 POST를 다시 보내도 예약을 두 번 만들지 않으려면, controller의 `if`문보다 먼저 같은 request identity를 DB가 한 번만 통과시키는 멱등성 경계가 필요하다.

## 미션 시나리오

roomescape 관리자 예약 화면은 예약자, 날짜, 시간 슬롯을 고르고 `POST
/admin/reservations`를 보내는 흐름으로 자주 구현된다. 여기서 저장이 조금
느리거나 브라우저가 응답을 못 받으면 학습자는 버튼을 다시 누르기 쉽고, 자동
재시도나 새로고침까지 겹치면 "같은 예약 생성 의도"가 두 번 서버에 도착할 수 있다.

이때 흔한 첫 구현은 "`exists`로 먼저 확인하고 없으면 저장"이다. 하지만 두 요청이
거의 동시에 들어오면 둘 다 확인을 통과할 수 있고, 운이 나쁘면 예약이 두 번
생기거나 하나는 뒤늦게 duplicate key 예외로 터진다. 리뷰에서 "PRG는 새로고침
경계를 정리하는 것이고, 중복 제출은 멱등성으로 닫아야 한다", "같은 생성 시도
자체의 identity를 저장소가 먼저 인정하게 하라"는 코멘트가 나오는 이유가 여기다.

## CS concept 매핑

여기서 닿는 개념은 idempotency key와 insert-first arbitration이다. 예를 들어
roomescape 예약 생성 시도마다 `request_id`를 받고, `(request_id)` 또는
`(member_id, request_id)`에 `UNIQUE`를 두면 같은 의미의 요청 재전송 경쟁에서 DB가
한 번만 승자를 정한다.

```sql
INSERT INTO reservation_requests (request_id, reservation_date, reservation_time_id) VALUES (?, ?, ?);
```

이 insert가 성공한 요청만 실제 예약 row 생성까지 진행하고, 같은 `request_id`로
다시 온 요청은 "이미 처리 중이거나 이미 끝난 같은 시도"로 해석해 기존 결과를
재사용할 수 있다. 중요한 구분은 이것이 `roomescape-reservation-concurrency-bridge`
에서 다루는 "서로 다른 두 요청이 같은 슬롯을 다투는 문제"와 다르다는 점이다.
멱등성은 같은 요청을 한 번만 인정하는 계약이고, 슬롯 경쟁은 다른 요청들 사이의
승자를 고르는 계약이다.

| roomescape 장면 | 더 가까운 개념 | 왜 그 개념으로 읽나 |
| --- | --- | --- |
| 같은 관리자가 응답 timeout 뒤 같은 예약 생성 POST를 다시 보냄 | idempotency key | 같은 의미의 요청 재전송을 한 번만 인정해야 한다 |
| 두 관리자가 우연히 같은 슬롯을 거의 동시에 예약함 | uniqueness, concurrency arbitration | 서로 다른 요청끼리 같은 자원을 두고 경쟁하는 문제다 |
| redirect를 넣었는데도 더블클릭 중복이 남음 | PRG vs duplicate suppression 분리 | 브라우저 새로고침 주소 정리와 저장소 dedup은 다른 층위다 |
| duplicate key 예외가 났는데 기존 성공 결과를 다시 주고 싶음 | replay-safe response | 이미 끝난 같은 시도를 다시 읽어 응답하는 정책이 필요하다 |

## 미션 PR 코멘트 패턴

- "`exists` 확인 후 `save`만으로는 같은 요청 재전송 경쟁을 닫지 못합니다."라는 코멘트는 읽고 판단하는 단계보다 먼저 저장소 선점이 필요하다는 뜻이다.
- "PRG를 넣어도 더블클릭과 timeout retry는 남습니다."라는 코멘트는 브라우저 흐름 정리와 중복 제출 방어를 분리해 설명하라는 뜻이다.
- "`request_id`나 idempotency key 없이 `memberId + date + timeId`만으로 같은 시도를 다 설명하려 하면 의도가 섞입니다."라는 코멘트는 비즈니스 슬롯 식별자와 요청 식별자를 구분하라는 의미다.
- "duplicate key를 그냥 `500`으로 끝내지 말고 이미 처리된 요청인지, 다른 요청과 충돌한 것인지 응답 의미를 나눠 보세요."라는 코멘트는 dedup 신호와 business conflict 신호를 같은 예외로 뭉개지 말라는 뜻이다.

## 다음 학습

- 멱등성 키 저장소와 replay 응답 패턴을 일반화해서 보려면 `멱등성 키와 중복 방지`를 읽는다.
- 같은 슬롯을 서로 다른 요청이 다툴 때 어떤 제약이나 락을 고를지 보려면 `같은 시간대 예약 동시 요청 — 락 vs 유니크 제약 vs 낙관적 락 결정`으로 이어간다.
- 브라우저 새로고침과 redirect 경계부터 다시 정리하려면 `roomescape 관리자 예약 생성 POST 뒤 목록 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지`를 함께 본다.
- duplicate key를 `409`나 replay 응답으로 어떻게 번역할지 보려면 `roomescape 중복 예약 충돌 ↔ Spring SQLException 번역 브릿지`를 다음 문서로 잡는다.
