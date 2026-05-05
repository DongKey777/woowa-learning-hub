---
schema_version: 3
title: roomescape 예약 생성 책임 배치 결정 가이드
concept_id: software-engineering/roomescape-reservation-responsibility-placement-decision-guide
canonical: false
category: software-engineering
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/roomescape
review_feedback_tags:
- responsibility-placement
- controller-vs-service-vs-repository
- validation-boundary
aliases:
- roomescape 예약 생성 책임 배치 결정 가이드
- roomescape controller service repository chooser
- roomescape 예약 책임 어디에 둘까
- ReservationController ReservationService 역할 구분 roomescape
- 룸이스케이프 예약 로직 배치 분기표
- roomescape validation repository transaction 경계 판단
symptoms:
- roomescape 예약 생성 코드에서 컨트롤러, 서비스, 리포지토리 중 어디에 로직을 둬야 할지 자꾸 헷갈려요
- 리뷰어가 이 검증은 service가 아니라 controller나 domain이 더 가깝다고 했는데 기준을 모르겠어요
- ReservationService가 커지는 이유가 책임 배치 실수인지부터 판단하고 싶어요
intents:
- comparison
- design
- mission_bridge
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
- contents/spring/roomescape-transactional-boundary-bridge.md
- contents/software-engineering/roomescape-reservation-service-bloat-cause-router.md
confusable_with:
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- software-engineering/roomescape-dao-vs-repository-bridge
- spring/roomescape-transactional-boundary-bridge
forbidden_neighbors:
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/software-engineering/roomescape-validation-vs-domain-rule-bridge.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
- contents/spring/roomescape-transactional-boundary-bridge.md
expected_queries:
- roomescape 예약 생성에서 이름 형식 검사, 중복 확인, SQL 저장을 각각 어느 계층에 두는 게 맞아?
- ReservationController가 DTO를 받고 바로 repository를 부르면 왜 책임이 섞였다고 말해?
- roomescape 미션에서 service가 유스케이스 순서만 가져가고 세부 구현은 밖으로 밀라는 리뷰를 어떻게 판단해?
- 예약 생성 로직이 커질 때 controller 문제인지 validation 경계 문제인지 repository 경계 문제인지 한 표로 보고 싶어
- roomescape에서 트랜잭션 시작 위치까지 포함해 책임 배치를 고르는 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 예약 생성 기능을 만들며 controller,
  service, domain rule, repository, transaction 경계를 어디에 두는지 헷갈리는
  학습자를 위한 chooser다. 이름 형식 검사는 어디에, 중복 예약 충돌은 어디에,
  JdbcTemplate 호출은 어디에, 트랜잭션은 어디서 열지, ReservationService가 왜
  비대해지는지 같은 자연어 paraphrase가 책임 배치 결정 표로 매핑된다.
---

# roomescape 예약 생성 책임 배치 결정 가이드

## 한 줄 요약

> roomescape 예약 생성에서 헷갈리는 건 "로직이 많다"보다 "이 판단이 요청 해석인지, 유스케이스 조립인지, 도메인 규칙인지, 저장 세부인지"를 먼저 못 가른다는 점이다.

## 결정 매트릭스

| 리뷰 장면 | 더 가까운 책임 | 먼저 볼 문서 |
| --- | --- | --- |
| `@NotBlank`, 날짜 파싱, 요청 형식 오류를 다룸 | controller / request validation | `roomescape 예약 생성 실패 응답 ↔ 입력 검증과 도메인 규칙 경계 브릿지` |
| 예약 가능 여부 확인, 엔티티 조립, 저장 순서를 한 번에 엮음 | service orchestration | `roomescape 관리자 예약 생성 흐름 ↔ Service 계층 브릿지` |
| `JdbcTemplate`, row mapping, SQL 세부가 중심 | repository boundary | `roomescape 4단계 계층 분리에서 DAO와 Repository 어떻게 나누나` |
| commit 기준, 동시성 예외 번역, 후처리 묶음을 정함 | transaction boundary | `roomescape 예약 생성/삭제에서 @Transactional 경계 결정` |
| 한 메서드에 위 네 가지가 동시에 눌어붙음 | symptom split first | `roomescape 예약 서비스 비대화 원인 라우터` |

짧게 외우면, "요청 한 장으로 알 수 있나"는 controller, "한 유스케이스 순서를 설명하나"는 service, "저장 기술을 직접 만지나"는 repository, "같이 성공하거나 같이 실패해야 하나"는 transaction 축이다.

## 흔한 오선택

`ReservationService`에만 넣으면 계층 분리가 끝난다고 보는 오선택이 흔하다.
컨트롤러의 형식 검증, 저장소의 SQL 세부, 트랜잭션 경계 결정까지 한 메서드로 모이면 파일 위치만 바뀌고 책임은 여전히 섞여 있다.

반대로 repository가 예약 가능 여부까지 판단하게 만드는 경우도 많다.
이미 찬 슬롯인지 판단하려면 저장소 조회는 필요하지만, "그래서 이번 요청을 거절할지"는 유스케이스와 정책의 문맥이라 service나 domain rule 쪽이 더 자연스럽다.

또 `@Valid`로 해결되지 않는 충돌을 모두 transaction 문제로 넘기는 실수도 있다.
요청 형식 오류와 현재 상태 충돌을 먼저 나누지 않으면 `400`과 `409`가 뒤섞이고, 그다음 트랜잭션을 어디에 둘지도 흐려진다.

## 다음 학습

- 유스케이스 순서를 service가 왜 소유하는지 다시 잡으려면 [roomescape 관리자 예약 생성 흐름 ↔ Service 계층 브릿지](./roomescape-reservation-flow-service-layer-bridge.md)를 본다.
- `400` 성격 입력 오류와 슬롯 충돌 규칙을 나누려면 [roomescape 예약 생성 실패 응답 ↔ 입력 검증과 도메인 규칙 경계 브릿지](./roomescape-validation-vs-domain-rule-bridge.md)를 읽는다.
- 저장소 이름과 JDBC 구현 경계를 정리하려면 [roomescape 4단계 계층 분리에서 DAO와 Repository 어떻게 나누나](./roomescape-dao-vs-repository-bridge.md)를 본다.
- 책임이 한 메서드에 이미 뭉쳐 있다면 [roomescape 예약 서비스 비대화 원인 라우터](./roomescape-reservation-service-bloat-cause-router.md)로 먼저 증상을 가른다.
