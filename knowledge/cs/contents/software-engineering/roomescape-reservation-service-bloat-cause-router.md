---
schema_version: 3
title: roomescape 예약 서비스 비대화 원인 라우터
concept_id: software-engineering/roomescape-reservation-service-bloat-cause-router
canonical: false
category: software-engineering
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
review_feedback_tags:
- service-too-big
- mixed-responsibility
- reservation-flow-boundary
aliases:
- roomescape 예약 서비스 비대화
- roomescape ReservationService 너무 큼
- 룸이스케이프 서비스가 너무 많은 걸 알아요
- 예약 서비스 책임 분리 원인
- roomescape service too big
symptoms:
- roomescape ReservationService 메서드 하나에 조회, 검증, 저장, 응답 조립이 다 붙어 있어요
- 리뷰에서 서비스가 너무 많은 걸 안다거나 비대하다는 말을 들었는데 어디부터 쪼개야 할지 모르겠어요
- 예약 생성과 조회 로직이 한 서비스에 섞여 있어서 수정할수록 메서드가 길어져요
- 컨트롤러에서 뺀 코드를 서비스로 옮겼는데 여전히 역할이 뒤엉킨 느낌이에요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
next_docs:
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- software-engineering/roomescape-dao-vs-repository-bridge
- spring/roomescape-transactional-boundary-bridge
linked_paths:
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/software-engineering/roomescape-validation-vs-domain-rule-bridge.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
- contents/software-engineering/review-comment-pattern-cards.md
- contents/spring/roomescape-transactional-boundary-bridge.md
confusable_with:
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- software-engineering/roomescape-dao-vs-repository-bridge
forbidden_neighbors:
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/software-engineering/roomescape-validation-vs-domain-rule-bridge.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
- contents/spring/roomescape-transactional-boundary-bridge.md
expected_queries:
- roomescape ReservationService가 너무 커졌다는 리뷰를 받으면 먼저 어떤 책임부터 나눠 봐야 해?
- 예약 생성 서비스에 검증, 저장, 응답 조립이 다 있으면 어디가 섞였다고 읽어야 해?
- 컨트롤러 코드를 서비스로만 옮겼는데도 roomescape 서비스가 비대한 이유는 뭐야?
- 예약 조회 로직과 생성 로직이 한 서비스 메서드에 붙어 있으면 어떤 경계를 먼저 세워야 해?
- 룸이스케이프 미션에서 service가 너무 많은 걸 안다는 코멘트는 정확히 무엇을 뜻해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 ReservationService가 길어지고 검증과
  정책과 저장 세부와 응답 조립이 한 메서드에 눌어붙을 때 원인을 가르는
  symptom_router다. 예약 서비스 비대화, 컨트롤러 코드를 옮겼는데도 더러움,
  조회와 생성 로직 혼합, 400 성격 검증과 비즈니스 충돌이 뒤섞임,
  transaction과 repository 호출이 한곳에 엉킴 같은 학습자 표현을 service
  orchestration, validation boundary, repository boundary, transaction
  boundary 갈래로 라우팅한다.
---

# roomescape 예약 서비스 비대화 원인 라우터

## 한 줄 요약

> roomescape에서 서비스가 비대해지는 이유는 대개 "서비스를 만들었다"가 아니라, 유스케이스 조립과 규칙 판단과 저장 세부와 응답 모양이 한 메서드에 동시에 눌어붙었기 때문이다.

## 가능한 원인

1. **유스케이스 순서와 세부 작업이 한 메서드에 섞였다.** 예약 시간 조회, 중복 확인, 엔티티 생성, 저장, 응답 DTO 조립을 한 번에 적으면 `ReservationService`가 흐름 요약이 아니라 구현 창고가 된다. 이 갈래는 [roomescape 관리자 예약 생성 흐름 ↔ Service 계층 브릿지](./roomescape-reservation-flow-service-layer-bridge.md)로 가서 서비스가 소유해야 할 것은 "모든 코드"가 아니라 "유스케이스 순서"라는 감각부터 다시 잡는다.
2. **입력 검증과 도메인 규칙 검증이 같은 층에 엉켰다.** `name` 공백 검사, 날짜 형식 오류, 이미 찬 슬롯 충돌, 취소 가능 상태 판단을 한 메서드의 `if` 사슬에 몰아넣으면 서비스가 비대한 동시에 실패 의미도 흐려진다. 이 경우는 [roomescape 예약 생성 실패 응답 ↔ 입력 검증과 도메인 규칙 경계 브릿지](./roomescape-validation-vs-domain-rule-bridge.md)로 이어서 "요청 형식"과 "현재 상태 기반 정책"을 먼저 자른다.
3. **조회 모델과 저장 모델을 같은 서비스가 같이 끌고 간다.** 관리자 예약 목록 조회처럼 읽기 모양이 중요한 API와 예약 생성처럼 상태 전이가 중요한 API를 한 서비스에 붙이면, 메서드가 길어지는 것보다 "왜 이 서비스가 이 쿼리까지 아나"가 먼저 문제다. 이 갈래는 [roomescape 4단계 계층 분리에서 DAO와 Repository 어떻게 나누나](./roomescape-dao-vs-repository-bridge.md)로 가서 조회 전용 경로와 저장 책임을 분리해 본다.
4. **트랜잭션 경계와 외부 부수효과를 서비스가 한 번에 떠안았다.** 예약 저장, 상태 변경, 알림 호출, 예외 번역이 같은 메서드에 몰리면 서비스는 단순히 길어진 게 아니라 commit 기준까지 숨기게 된다. 이때는 [roomescape 예약 생성/삭제에서 `@Transactional` 경계 결정](../spring/roomescape-transactional-boundary-bridge.md)으로 가서 무엇을 한 트랜잭션으로 묶고 무엇을 바깥으로 밀어낼지 먼저 정한다.

## 빠른 자기 진단

1. 한 메서드 안에서 `request` 해석, repository 조회, 엔티티 생성, 응답 DTO 변환이 순서대로 다 보이면 서비스 계층 브릿지를 먼저 본다.
2. `400` 성격의 입력 오류와 `409` 성격의 충돌 예외가 같은 `if` 블록에서 결정되면 validation boundary 갈래가 우선이다.
3. 목록 조회 SQL 모양과 예약 생성 정책이 같은 클래스에 붙어 있으면 repository/DAO 경계가 흐린 쪽을 먼저 의심한다.
4. 저장 성공 후 알림, 이벤트, 후처리까지 같은 메서드에서 직접 호출하면 transaction boundary 갈래를 먼저 본다.

## 다음 학습

- 서비스가 실제로 무엇을 소유해야 하는지 다시 잡으려면 [roomescape 관리자 예약 생성 흐름 ↔ Service 계층 브릿지](./roomescape-reservation-flow-service-layer-bridge.md)를 본다.
- 입력 형식 오류와 현재 상태 충돌을 먼저 나누려면 [roomescape 예약 생성 실패 응답 ↔ 입력 검증과 도메인 규칙 경계 브릿지](./roomescape-validation-vs-domain-rule-bridge.md)를 잇는다.
- 조회 경로와 저장 경로를 같은 저장소 추상화에 묶어 두었는지 확인하려면 [roomescape 4단계 계층 분리에서 DAO와 Repository 어떻게 나누나](./roomescape-dao-vs-repository-bridge.md)를 본다.
- 서비스가 너무 많은 걸 안다는 말이 사실상 트랜잭션 경계 문제인지 보려면 [roomescape 예약 생성/삭제에서 `@Transactional` 경계 결정](../spring/roomescape-transactional-boundary-bridge.md)을 이어서 읽는다.
