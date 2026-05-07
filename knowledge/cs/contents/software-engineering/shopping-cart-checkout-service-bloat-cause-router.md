---
schema_version: 3
title: shopping-cart checkout 서비스 비대화 원인 라우터
concept_id: software-engineering/shopping-cart-checkout-service-bloat-cause-router
canonical: false
category: software-engineering
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- service-too-big
- mixed-responsibility
- checkout-boundary
aliases:
- shopping-cart checkout 서비스 비대화
- 장바구니 checkout service 너무 큼
- shopping-cart 서비스가 너무 많은 걸 알아요
- checkout 책임 분리 원인
- shopping-cart service too big
symptoms:
- shopping-cart CheckoutService 메서드 하나에 검증, 금액 계산, 주문 생성, 결제 호출, 응답 조립이 다 붙어 있어요
- 리뷰에서 checkout 서비스가 너무 많은 걸 안다고 하는데 어디부터 잘라야 할지 모르겠어요
- 장바구니 checkout 로직을 컨트롤러에서 서비스로 옮겼는데도 메서드가 계속 길어져요
- 결제 흐름, 총액 재계산, 주문 snapshot 저장이 한 서비스에 섞여 있어서 수정할수록 더 복잡해져요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
next_docs:
- software-engineering/shopping-cart-checkout-service-layer-bridge
- software-engineering/shopping-cart-checkout-validation-domain-invariant-bridge
- software-engineering/shopping-cart-checkout-total-revalidation-source-of-truth-bridge
- software-engineering/shopping-cart-order-snapshot-from-cart-bridge
- spring/shopping-cart-payment-transaction-boundary-bridge
linked_paths:
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
- contents/software-engineering/shopping-cart-checkout-validation-domain-invariant-bridge.md
- contents/software-engineering/shopping-cart-checkout-total-revalidation-source-of-truth-bridge.md
- contents/software-engineering/shopping-cart-order-snapshot-from-cart-bridge.md
- contents/spring/shopping-cart-payment-transaction-boundary-bridge.md
confusable_with:
- software-engineering/shopping-cart-checkout-service-layer-bridge
- software-engineering/shopping-cart-checkout-validation-domain-invariant-bridge
- software-engineering/shopping-cart-checkout-total-revalidation-source-of-truth-bridge
- software-engineering/shopping-cart-order-snapshot-from-cart-bridge
forbidden_neighbors: []
expected_queries:
- shopping-cart checkout 서비스가 너무 커졌다는 리뷰를 받으면 먼저 어떤 책임부터 나눠 봐야 해?
- 장바구니 checkout 메서드에 검증, 총액 계산, 주문 생성, 결제 호출이 다 있으면 어디가 섞인 거야?
- 컨트롤러 코드를 서비스로만 옮겼는데도 shopping-cart 서비스가 비대한 이유는 뭐야?
- checkout에서 결제 트랜잭션 얘기 전에 서비스가 너무 많은 걸 안다는 말은 정확히 무슨 뜻이야?
- 장바구니 주문 생성 흐름에서 총액 재계산과 snapshot 저장까지 한 서비스에 넣으면 왜 점점 복잡해져?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 CheckoutService가 길어지고 검증과
  총액 재계산과 주문 생성과 결제 호출과 응답 조립이 한 메서드에 눌어붙을 때
  원인을 가르는 symptom_router다. checkout 서비스가 너무 큼, controller에서
  옮겼는데도 복잡함, 총액 재계산과 snapshot 저장이 한곳에 섞임, 결제 호출을
  어디서 해야 하는지 모르겠음 같은 학습자 표현을 service orchestration,
  validation boundary, source of truth, order snapshot, transaction boundary
  갈래로 라우팅한다.
---

# shopping-cart checkout 서비스 비대화 원인 라우터

## 한 줄 요약

> shopping-cart checkout 서비스가 비대해지는 이유는 보통 "서비스를 만들었기 때문"이 아니라, 유스케이스 순서와 규칙 판정과 금액 재검증과 기록 보존 방식이 한 메서드에 동시에 눌어붙었기 때문이다.

## 가능한 원인

1. **유스케이스 순서와 세부 작업이 한 메서드에 섞였다.** 주문 생성, 결제 승인 요청, 상태 확정, 응답 조립을 같은 메서드가 전부 품고 있으면 서비스가 흐름 요약이 아니라 구현 창고가 된다. 이 갈래는 [shopping-cart 결제 승인/주문 확정 흐름 ↔ Service 계층 브릿지](./shopping-cart-checkout-service-layer-bridge.md)로 가서 service가 소유해야 할 것은 "모든 코드"가 아니라 "checkout 순서"라는 감각부터 다시 잡는다.
2. **입력 검증과 현재 상태 충돌 판정이 같은 곳에 엉켰다.** `paymentMethod` 누락 같은 입구 오류와 품절, 중복 쿠폰, 이미 확정된 주문 같은 상태 기반 충돌을 한 `if` 사슬에서 처리하면 서비스가 비대할 뿐 아니라 실패 의미도 흐려진다. 이 경우는 [shopping-cart 주문 생성 실패 응답 ↔ 입력 검증과 도메인 불변식 브릿지](./shopping-cart-checkout-validation-domain-invariant-bridge.md)로 이어서 `400` 성격과 `409` 성격 질문을 먼저 자른다.
3. **화면에서 본 금액과 실제 확정 금액을 같은 진실로 다룬다.** 장바구니 화면 총액, 쿠폰 적용 결과, 최종 주문 금액을 같은 변수 흐름에 묶어 두면 서비스가 계산과 검증과 응답 표현을 동시에 떠안게 된다. 이 갈래는 [shopping-cart 결제 금액 재확인 ↔ Source of Truth와 서버 재계산 브릿지](./shopping-cart-checkout-total-revalidation-source-of-truth-bridge.md)로 보내서 checkout 직전에 무엇을 다시 계산해야 하는지부터 분리한다.
4. **주문 시점 기록 보존과 트랜잭션 경계가 함께 뭉쳤다.** 주문 snapshot 저장, 장바구니 비우기, 외부 결제 호출, commit 기준을 한 메서드가 한 번에 들고 있으면 변경 포인트가 한곳에 과하게 모인다. 이때는 [shopping-cart 주문 생성 시점 cart 복사 ↔ Order Snapshot 브릿지](./shopping-cart-order-snapshot-from-cart-bridge.md)와 [shopping-cart 결제 승인/주문 확정 ↔ Spring 트랜잭션 경계 브릿지](../spring/shopping-cart-payment-transaction-boundary-bridge.md)를 이어서 보며 "무엇을 남길지"와 "무엇을 함께 commit할지"를 나눠 읽는다.

## 빠른 자기 진단

1. 한 메서드 안에서 request 해석, repository 조회, 결제 client 호출, 응답 DTO 변환이 순서대로 다 보이면 service orchestration 갈래를 먼저 본다.
2. `400` 성격 입력 오류와 `409` 성격 비즈니스 충돌이 같은 분기에서 결정되면 validation boundary가 우선이다.
3. 화면에서 받은 총액을 그대로 믿을지, 서버가 다시 계산할지 흔들리면 source of truth 갈래가 먼저다.
4. 주문 완료 후 장바구니 비우기, snapshot 저장, 외부 승인 호출까지 한 트랜잭션처럼 적혀 있으면 snapshot과 transaction boundary를 따로 본다.

## 다음 학습

- checkout 흐름에서 service가 실제로 무엇을 소유해야 하는지 다시 잡으려면 [shopping-cart 결제 승인/주문 확정 흐름 ↔ Service 계층 브릿지](./shopping-cart-checkout-service-layer-bridge.md)를 본다.
- 입력 형식 오류와 현재 상태 충돌을 먼저 나누려면 [shopping-cart 주문 생성 실패 응답 ↔ 입력 검증과 도메인 불변식 브릿지](./shopping-cart-checkout-validation-domain-invariant-bridge.md)를 잇는다.
- 장바구니 화면 총액과 최종 주문 금액을 같은 진실로 두고 있는지 점검하려면 [shopping-cart 결제 금액 재확인 ↔ Source of Truth와 서버 재계산 브릿지](./shopping-cart-checkout-total-revalidation-source-of-truth-bridge.md)를 본다.
- checkout 뒤에도 주문 사실이 재현돼야 하는 이유를 보려면 [shopping-cart 주문 생성 시점 cart 복사 ↔ Order Snapshot 브릿지](./shopping-cart-order-snapshot-from-cart-bridge.md)를 이어서 읽는다.
- 외부 결제 승인과 로컬 commit을 같은 rollback으로 묶을 수 없는 이유는 [shopping-cart 결제 승인/주문 확정 ↔ Spring 트랜잭션 경계 브릿지](../spring/shopping-cart-payment-transaction-boundary-bridge.md)에서 확인한다.
