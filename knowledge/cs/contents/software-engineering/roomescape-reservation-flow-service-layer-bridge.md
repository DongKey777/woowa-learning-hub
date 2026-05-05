---
schema_version: 3
title: roomescape 관리자 예약 생성 흐름 ↔ Service 계층 브릿지
concept_id: software-engineering/roomescape-reservation-flow-service-layer-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- controller-logic-leak
- service-orchestration
- reservation-flow-boundary
aliases:
- roomescape service layer
- roomescape 예약 생성 흐름
- ReservationService 책임
- controller logic leak roomescape
- 룸이스케이프 서비스 계층
symptoms:
- 컨트롤러에 예약 생성 로직이 너무 많다고 리뷰를 받았어
- ReservationService가 너무 얇아서 뭐를 더 넣어야 할지 모르겠어
- 예약 생성 순서를 controller에서 짜면 왜 안 되는지 헷갈려
intents:
- mission_bridge
- design
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
next_docs:
- software-engineering/roomescape-dao-vs-repository-bridge
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- spring/roomescape-transactional-boundary-bridge
linked_paths:
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
- contents/software-engineering/roomescape-validation-vs-domain-rule-bridge.md
- contents/spring/roomescape-transactional-boundary-bridge.md
confusable_with:
- software-engineering/service-layer-basics
- software-engineering/roomescape-dao-vs-repository-bridge
- spring/roomescape-transactional-boundary-bridge
forbidden_neighbors:
  - contents/software-engineering/roomescape-dao-vs-repository-bridge.md
  - contents/spring/roomescape-transactional-boundary-bridge.md
expected_queries:
- roomescape에서 예약 생성 순서를 Service가 가져가야 하는 이유가 뭐야?
- 컨트롤러에서 예약 엔티티 만들고 저장하면 왜 리뷰에서 걸려?
- ReservationService가 얇아 보여도 괜찮다는 말이 무슨 뜻이야?
- roomescape 미션에서 controller와 service 책임을 어디서 끊어?
- 예약 시간 조회, 중복 확인, 저장 순서를 한 메서드에 모으는 게 왜 자연스러워?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 예약 생성 API를 만들 때
  learner가 controller에 흐름 로직을 두었다가 service 책임 분리 리뷰를 받는
  상황을 다루는 mission_bridge다. 예약 시간 조회, 중복 확인, 엔티티 생성,
  저장 순서를 어디에 둘지, Service가 얇아 보여도 괜찮은지, controller logic
  leak라는 코멘트가 무엇을 뜻하는지 service layer orchestration 관점으로 연결한다.
---

# roomescape 관리자 예약 생성 흐름 ↔ Service 계층 브릿지

## 한 줄 요약

> roomescape 예약 생성에서 `요청 해석 -> 예약 가능 여부 확인 -> 엔티티 조립 -> 저장`은 한 번의 유스케이스 흐름이라 Service가 모으는 편이 자연스럽다. Controller는 HTTP 입구를, Repository는 저장 세부를 맡고, 그 사이 순서는 `ReservationService`가 소유한다.

## 미션 시나리오

roomescape 초반 단계에서는 `ReservationController` 안에서 `request.date()`와 `request.timeId()`를 꺼내고, `ReservationTime`을 조회한 뒤, `Reservation`을 만들고, 마지막에 저장까지 한 번에 적기 쉽다. 학습자 입장에서는 파일 수가 적어서 이 편이 더 단순해 보인다.

하지만 단계가 올라가면 흐름이 금방 길어진다. 이미 찬 슬롯인지 확인해야 하고, 예약자 이름 검증과 비즈니스 충돌을 나눠야 하고, 삭제나 변경 시 같은 규칙을 다시 써야 한다. 이때 리뷰에서 "controller가 흐름을 너무 많이 안다", "service가 유스케이스를 가져가야 한다"는 코멘트가 붙는다.

짧은 예시는 아래처럼 읽으면 된다.

```java
ReservationTime time = reservationTimeRepository.getById(request.timeId());
reservationPolicy.ensureBookable(request.date(), time);
return reservationRepository.save(Reservation.of(request.name(), request.date(), time));
```

이 세 줄은 저장 기술이나 HTTP 세부보다 "예약 생성 유스케이스의 순서"를 말한다. 그래서 controller보다 service에 있을 때 더 읽기 쉽다.

## CS concept 매핑

Service 계층은 "한 유스케이스를 끝내는 순서와 경계"를 소유한다. roomescape 예약 생성에 대입하면 다음처럼 나뉜다.

| roomescape 장면 | 더 가까운 책임 | 왜 그 자리에 두나 |
| --- | --- | --- |
| JSON body를 DTO로 받기 | Controller | HTTP 요청을 애플리케이션 입력으로 바꾸는 입구이기 때문이다 |
| 이미 찬 슬롯인지 확인하고 예외 선택 | Service | 현재 상태 조회와 정책 판단을 함께 조립해야 하기 때문이다 |
| `Reservation` 객체 자체의 기본 규칙 유지 | Domain | 이름, 날짜, 시간 같은 한 예약의 의미를 스스로 지켜야 하기 때문이다 |
| SQL 실행과 row 매핑 | Repository | 저장 기술 세부를 바깥 계층에 새지 않게 해야 하기 때문이다 |

여기서 자주 나오는 오해는 "Service가 얇으면 존재 가치가 없는 것 아닌가?"다. 그렇지 않다. roomescape처럼 작은 미션에서도 Service가 가지는 가치는 코드 길이보다 "유스케이스 순서가 한곳에 모여 있는가"에 있다. Controller가 순서를 소유하면 웹 진입점이 바뀔 때 같은 흐름이 흩어지고, Repository가 순서를 소유하면 저장소가 정책까지 떠안게 된다.

또 `roomescape-dao-vs-repository-bridge`가 저장소 이름과 경계를 다룬다면, 이 문서는 그 저장소를 어떤 순서로 호출해 예약 생성이라는 한 동작을 완성하는지에 초점을 둔다. `roomescape-transactional-boundary-bridge`는 그 흐름을 어디까지 한 트랜잭션으로 묶을지로 이어진다.

## 미션 PR 코멘트 패턴

- "`ReservationController`가 time 조회, 중복 확인, 저장까지 다 하면 계층 분리가 약해집니다."라는 코멘트는 HTTP 입구가 유스케이스 흐름을 소유하지 말라는 뜻이다.
- "`ReservationService`가 얇아 보여도 괜찮아요. 중요한 건 예약 생성 순서가 한곳에 모이는 겁니다."라는 코멘트는 Service의 가치를 코드 줄 수가 아니라 orchestration으로 보라는 뜻이다.
- "`Repository`는 저장만 알고, 예약 가능 정책은 Service 쪽에서 결정해 보세요."라는 코멘트는 persistence 세부와 business rule을 분리하라는 뜻이다.
- "`삭제 API`나 `관리자 예약 추가`에서도 같은 규칙을 재사용해야 하니 controller보다 service에 두는 편이 안전합니다."라는 코멘트는 유스케이스 재사용성과 변경 범위를 함께 보라는 뜻이다.

## 다음 학습

- 저장소 추상화 이름이 왜 `Repository`로 기우는지 보려면 [roomescape 4단계 계층 분리에서 DAO와 Repository 어떻게 나누나](./roomescape-dao-vs-repository-bridge.md)를 본다.
- 입력 검증과 충돌 규칙을 더 정확히 자르려면 [roomescape 예약 생성 실패 응답 ↔ 입력 검증과 도메인 규칙 경계 브릿지](./roomescape-validation-vs-domain-rule-bridge.md)를 본다.
- 이 흐름을 어디까지 한 트랜잭션으로 묶을지 이어서 보려면 [roomescape 예약 생성/삭제에서 @Transactional 경계 결정](../spring/roomescape-transactional-boundary-bridge.md)을 본다.
