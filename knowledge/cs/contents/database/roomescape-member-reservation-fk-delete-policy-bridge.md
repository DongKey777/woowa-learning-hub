---
schema_version: 3
title: Roomescape Member / Reservation FK Delete Policy Bridge
concept_id: database/roomescape-member-reservation-fk-delete-policy-bridge
canonical: false
category: database
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 76
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- roomescape
- foreign-key
- delete-policy
- reservation-modeling
aliases:
- roomescape member reservation foreign key delete policy
- 룸이스케이프 회원 예약 FK 삭제 정책
- reservation member FK restrict cascade
- 예약 회원 삭제 참조 무결성
- Roomescape FK delete bridge
symptoms:
- roomescape에서 회원을 삭제할 때 기존 예약을 어떻게 처리해야 할지 모르겠다
- FK 때문에 member 삭제가 실패하거나 cascade로 예약까지 사라져 당황한다
- soft delete, restrict, cascade 중 무엇을 골라야 하는지 리뷰에서 막혔다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- database/primary-foreign-key-basics
- database/sql-relational-modeling-basics
next_docs:
- database/foreign-key-cascade-lock-surprises
- database/soft-delete-uniqueness-indexing-lifecycle
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
linked_paths:
- contents/database/primary-foreign-key-basics.md
- contents/database/sql-reading-relational-modeling-primer.md
- contents/database/foreign-key-cascade-lock-surprises.md
- contents/database/soft-delete-uniqueness-indexing-lifecycle.md
- contents/database/roomescape-reservation-cancel-reschedule-active-predicate-bridge.md
- contents/software-engineering/roomescape-reservation-responsibility-placement-decision-guide.md
confusable_with:
- database/primary-foreign-key-basics
- database/foreign-key-cascade-lock-surprises
- database/soft-delete-uniqueness-indexing-lifecycle
forbidden_neighbors:
- contents/database/roomescape-reservation-concurrency-bridge.md
expected_queries:
- roomescape 회원 삭제 시 예약 FK를 어떻게 처리해야 해?
- 예약이 있는 member를 삭제하면 restrict cascade soft delete 중 뭘 봐야 해?
- 룸이스케이프 member reservation FK 리뷰를 DB 모델링으로 설명해줘
- 기존 예약을 보존해야 할 때 foreign key delete policy를 어떻게 잡아?
contextual_chunk_prefix: |
  이 문서는 roomescape member/reservation foreign key delete policy
  mission_bridge다. member delete, reservation history preservation,
  restrict vs cascade, soft delete, referential integrity, FK violation 같은
  자연어 질문을 Roomescape 데이터 모델링과 참조 무결성 판단으로 매핑한다.
---
# Roomescape Member / Reservation FK Delete Policy Bridge

> 한 줄 요약: roomescape에서 회원 삭제는 "row를 지울 수 있나"보다 "기존 예약 기록을 어떤 의미로 보존할 것인가"를 먼저 결정해야 한다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "회원을 삭제할 때 기존 예약을 어떻게 처리해야 할지 모르겠어요" | member와 reservation FK가 있는 roomescape 모델 | row 삭제보다 예약 기록 보존 의미를 먼저 정한다 |
| "FK 때문에 삭제가 실패하거나 cascade로 예약까지 사라져요" | restrict/cascade 정책을 처음 고르는 단계 | 참조 무결성과 product history requirement를 함께 본다 |
| "soft delete, restrict, cascade 중 무엇을 골라야 하나요?" | 탈퇴 회원, 과거 예약, 활성 예약 정책 분리 | 물리 삭제 요구, snapshot 필요, active predicate를 나눠 결정한다 |

## CS concept 매핑

| roomescape 장면 | DB 개념 |
|---|---|
| 예약이 있는 회원 삭제가 실패 | FK restrict / referential integrity |
| 회원 삭제와 함께 예약도 사라짐 | cascade delete |
| 회원은 탈퇴했지만 예약 기록은 남겨야 함 | soft delete 또는 anonymized snapshot |
| 예약 목록에서 탈퇴 회원 이름을 보여줘야 함 | snapshot column 또는 nullable reference policy |
| 취소 예약은 남기고 활성 예약만 막아야 함 | active predicate / lifecycle state |

## 리뷰 신호

- "`ON DELETE CASCADE`를 붙이면 편하지 않나요?"는 데이터 보존 의미를 먼저 물어야 하는 신호다.
- "예약 이력이 사라져도 되나요?"는 참조 무결성보다 product history requirement를 먼저 확인하라는 말이다.
- "회원 삭제와 예약 취소를 같은 의미로 보지 마세요"는 entity lifecycle이 다르다는 지적이다.
- "soft delete를 쓰면 unique constraint도 다시 봐야 합니다"는 삭제 정책이 조회/제약 조건까지 번진다는 뜻이다.

## 판단 순서

1. 예약 기록이 감사, CS 대응, 결제 이력과 연결되는지 본다.
2. 회원 row를 물리 삭제해야 하는 요구가 있는지 본다.
3. 삭제 회원의 표시 이름을 snapshot으로 남길지 nullable FK로 둘지 정한다.
4. active reservation만 막을지, 과거 reservation까지 FK로 묶을지 정한다.
5. soft delete를 고르면 uniqueness와 조회 predicate까지 같이 설계한다.

처음 미션에서는 cascade를 기본값처럼 쓰기보다, 기존 예약 보존 의미가 있으면 restrict나 soft delete 쪽에서 출발하는 편이 리뷰 설명이 쉽다.
