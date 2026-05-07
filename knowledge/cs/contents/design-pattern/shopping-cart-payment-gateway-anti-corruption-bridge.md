---
schema_version: 3
title: 'shopping-cart 결제사 응답 번역 ↔ Anti-Corruption Layer 브릿지'
concept_id: design-pattern/shopping-cart-payment-gateway-anti-corruption-bridge
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- payment-gateway-dto-leakage
- pg-status-translation
- anti-corruption-seam
aliases:
- shopping-cart 결제사 응답 번역
- 장바구니 PG DTO 누수
- shopping-cart 외부 결제 코드 매핑
- PG 에러 코드를 도메인으로 바꾸기
- shopping-cart 결제 응답 번역 계층
symptoms:
- PG 응답 DTO를 그대로 Order나 Payment 엔티티에 넣어도 되는지 모르겠어요
- 결제사 status code와 error code가 서비스 전역으로 퍼져서 리뷰에서 경계가 흐리다고 해요
- 환불 사유나 승인 실패 코드를 어디서 우리 언어로 바꿔야 할지 헷갈려요
intents:
- mission_bridge
- design
- troubleshooting
- comparison
prerequisites:
- software-engineering/shopping-cart-checkout-service-layer-bridge
- design-pattern/facade-anti-corruption-seam
- design-pattern/anti-corruption-translation-map-pattern
next_docs:
- design-pattern/facade-anti-corruption-seam
- design-pattern/anti-corruption-adapter-layering
- design-pattern/anti-corruption-translation-map-pattern
linked_paths:
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
- contents/design-pattern/facade-anti-corruption-seam.md
- contents/design-pattern/anti-corruption-adapter-layering.md
- contents/design-pattern/anti-corruption-translation-map-pattern.md
- contents/spring/shopping-cart-payment-method-router-qualifier-bridge.md
confusable_with:
- software-engineering/shopping-cart-checkout-service-layer-bridge
- spring/shopping-cart-payment-method-router-qualifier-bridge
- design-pattern/anti-corruption-adapter-layering
forbidden_neighbors:
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
- contents/spring/shopping-cart-payment-method-router-qualifier-bridge.md
expected_queries:
- shopping-cart 미션에서 PG 응답 DTO를 그대로 도메인에 두지 말라는 리뷰는 왜 나와?
- 결제 승인 결과와 에러 코드를 우리 enum이나 예외로 바꾸는 자리는 어디가 맞아?
- 장바구니 checkout에서 외부 결제사 status 값을 서비스 전역에 퍼뜨리지 않으려면 어떻게 설계해?
- shopping-cart에서 PaymentClient 응답을 translation map이나 facade 뒤에 숨기라는 뜻이 뭐야?
- 결제사 필드명이 바뀔 때 주문 도메인까지 같이 흔들리지 않게 막는 경계가 필요해?
contextual_chunk_prefix: |
  이 문서는 Woowa shopping-cart 미션에서 외부 PG 응답 DTO, 상태 코드,
  에러 코드가 주문/결제 도메인으로 그대로 스며드는 상황을
  Anti-Corruption Layer 관점으로 다시 묶는 mission_bridge다. 결제사 응답을
  어디서 우리 언어로 번역할지, PaymentClient 결과를 서비스 전역에 퍼뜨리지
  않는 이유가 무엇인지, facade와 translation map을 왜 두는지, 리뷰에서
  "외부 모델 누수"라고 지적하는 장면을 shopping-cart checkout 맥락으로
  연결한다.
---

# shopping-cart 결제사 응답 번역 ↔ Anti-Corruption Layer 브릿지

## 한 줄 요약

shopping-cart에서 PG 응답을 그대로 도메인에 퍼뜨리면 외부 계약 변경이 주문 모델까지 흔들리므로, 결제 경계에서 우리 언어로 한 번 번역하는 anti-corruption seam이 필요하다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "PG 응답 DTO를 그대로 Order나 Payment 엔티티에 넣어도 되나요?" | 외부 결제 승인 응답을 내부 도메인으로 넘기는 단계 | 외부 모델을 내부 결과 타입으로 번역하는 seam을 둔다 |
| "결제사 status code와 error code가 서비스 전역으로 퍼져요" | PG 코드표가 controller/service/domain/test에 새는 구조 | 외부 코드를 우리 enum/exception/result로 닫는다 |
| "환불 사유나 승인 실패 코드를 어디서 우리 언어로 바꿔야 하나요?" | PG adapter와 checkout service 경계 | facade/translator가 외부 계약과 내부 유스케이스 언어를 분리한다 |

## 미션 시나리오

shopping-cart checkout을 붙이다 보면 `PaymentClient`가 내려준 `approved_at`, `result_code`, `pay_method`, `failure_reason` 같은 필드를 그대로 `Order`나 `Payment` 생성자에 넘기기 쉽다. 처음엔 빨라 보이지만, PG 문서 한 번 바뀌면 주문 상태 전이 조건, 예외 메시지, 테스트 fixture가 같이 흔들린다.

리뷰에서는 보통 "외부 DTO가 도메인에 새고 있다", "PG 용어가 서비스 전역에 퍼진다", "에러 코드를 우리 예외로 닫아라" 같은 코멘트가 나온다. 학습자가 느끼는 핵심 혼란은 "`PaymentClient`를 분리했는데도 왜 아직 경계가 흐리다고 하지?"라는 지점이다.

## CS concept 매핑

여기서의 CS 개념은 Anti-Corruption Layer다. `PaymentClient` adapter가 외부 호출을 담당하더라도, 그 결과를 바로 도메인에 넘기면 외부 모델이 내부 언어를 오염시킨다. shopping-cart에서는 `PG 승인 성공`, `재시도 가능 실패`, `이미 처리된 결제`, `사용자 취소` 같은 내부 의미로 다시 묶어야 Order와 Payment가 PG 벤더의 코드표를 몰라도 된다.

실무적으로는 facade나 translator가 이 seam이 된다. 예를 들어 `PaymentClient` 응답의 `status=AUTH_OK`를 `PaymentApprovalResult.authorized(...)`로 바꾸고, `E409_DUP`를 `DuplicateApprovalException` 같은 내부 예외로 닫는다. 그러면 checkout service는 "이번 승인 결과가 주문 확정 가능한가"만 읽고, PG 필드명 변경은 translation map 한 곳에서만 수습한다.

## 미션 PR 코멘트 패턴

- "`Order`가 PG 응답 필드를 직접 들고 있으면 결제사 계약이 도메인 모델이 됩니다. 내부 결과 타입으로 한 번 번역해 보세요."
- "adapter를 뒀다는 사실만으로 ACL이 생기진 않습니다. 외부 status code와 error code를 서비스 밖에서 막아야 합니다."
- "`paymentMethod`, `resultCode`, `failureReason`을 컨트롤러부터 예외 처리까지 그대로 흘리면 벤더 변경 비용이 너무 커집니다."
- "checkout service는 승인 결과를 해석해 유스케이스를 끝내면 되고, PG 전문 용어 해석은 facade/translator 경계로 내리는 편이 낫습니다."

## 다음 학습

- anti-corruption seam을 일반 패턴으로 다시 보려면 `design-pattern/facade-anti-corruption-seam`
- adapter, facade, translator를 층으로 나누는 법은 `design-pattern/anti-corruption-adapter-layering`
- 외부 상태 코드와 에러 코드를 고정 매핑하는 예시는 `design-pattern/anti-corruption-translation-map-pattern`
- checkout orchestration과 외부 연동 경계를 함께 보려면 `software-engineering/shopping-cart-checkout-service-layer-bridge`
