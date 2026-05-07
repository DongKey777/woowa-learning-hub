---
schema_version: 3
title: 'lotto 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나'
concept_id: spring/lotto-mvc-controller-binding-validation-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- request-binding
- bean-validation
- input-vs-domain-rule
aliases:
- lotto spring mvc 입력 검증
- 로또 컨트롤러 바인딩
- lotto requestbody dto 검증
- 로또 http 요청 파싱
- lotto modelattribute requestbody 선택
symptoms:
- 콘솔 로또 입력을 스프링 controller에서 어떤 DTO로 받아야 할지 모르겠어요
- 구매 금액 형식 오류와 로또 번호 규칙 오류를 같은 검증으로 처리하고 있어요
- controller에서 split과 Lotto 생성을 같이 하다 보니 어디까지가 HTTP 책임인지 헷갈려요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/mvc-controller-basics
- spring/modelattribute-vs-requestbody-binding-primer
- software-engineering/lotto-inputview-domain-conversion-boundary-bridge
next_docs:
- spring/requestbody-400-before-controller-primer
- spring/spring-bindingresult-local-validation-400-primer
- software-engineering/lotto-inputview-domain-conversion-boundary-bridge
linked_paths:
- contents/spring/spring-mvc-controller-basics.md
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/spring/spring-bindingresult-local-validation-400-primer.md
- contents/spring/spring-requestbody-400-before-controller-primer.md
- contents/software-engineering/lotto-inputview-domain-conversion-boundary-bridge.md
- contents/software-engineering/lotto-domain-invariant-bridge.md
confusable_with:
- spring/baseball-mvc-controller-binding-bridge
- spring/blackjack-mvc-controller-binding-validation-bridge
- software-engineering/lotto-inputview-domain-conversion-boundary-bridge
forbidden_neighbors: []
expected_queries:
- 로또 미션을 웹으로 옮기면 구매 금액과 수동 번호 입력은 컨트롤러에서 어떻게 받아야 해?
- lotto에서 RequestBody 검증과 Lotto 도메인 규칙 검증을 왜 나눠서 보라고 해?
- 로또 API에서 400 입력 오류와 중복 번호 같은 도메인 오류를 같은 레이어에서 처리하면 뭐가 섞여?
- 콘솔 InputView에서 하던 split 검증을 Spring MVC에서는 어느 계층으로 옮기면 돼?
- 로또 미션 리뷰에서 controller는 형식만 보고 Lotto가 규칙을 지키게 하라는 말이 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션을 콘솔 InputView 중심 구조에서 Spring MVC 요청
  구조로 옮길 때 구매 금액, 수동 번호, 당첨 번호 입력을 어떤 DTO로 바인딩하고
  어디까지 형식 검증할지 설명하는 mission_bridge다. RequestBody DTO,
  ModelAttribute 선택, 숫자 형식 오류와 도메인 규칙 오류 분리, controller에서
  split과 Lotto 생성이 함께 일어나는 냄새, HTTP 입구와 도메인 불변식 경계를
  어떻게 자를지 같은 학습자 표현을 Spring binding과 validation 관점으로
  연결한다.
---

# lotto 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나

## 한 줄 요약

> 콘솔 lotto의 `InputView`가 하던 문자열 입력 수집은 Spring MVC에서 DTO 바인딩으로 옮겨 오지만, `6개`, `중복 없음`, `1~45`, `보너스 번호는 당첨 번호와 달라야 함` 같은 규칙까지 controller가 떠안으면 HTTP 입구와 도메인 경계가 다시 섞인다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "콘솔 `InputView`에서 하던 split을 controller에 그대로 넣어도 되나요?" | controller가 문자열 분리, 숫자 변환, Lotto 생성까지 한 메서드에서 처리하는 코드 | HTTP 바인딩/형식 검증과 도메인 불변식 검증을 분리한다 |
| "구매 금액 오류와 번호 중복 오류를 같은 `@Valid`로 막고 싶어요" | 요청 필드 형식과 Lotto 규칙이 DTO annotation에 모두 들어간 구조 | 요청 한 장으로 알 수 있는 형식 오류와 값 조합 규칙을 다른 층으로 본다 |
| "`@RequestBody`랑 `@ModelAttribute` 중 lotto에는 뭐가 맞아요?" | JSON API와 HTML form 입력 방식을 같은 controller signature로 처리하려는 상황 | content type과 UI 흐름에 맞춰 바인딩 방식을 먼저 선택한다 |

## 미션 시나리오

콘솔 lotto에서는 `InputView`가 구매 금액, 수동 번호, 당첨 번호를 읽고 쉼표로
나누며 흐름을 계속 붙잡는다. Spring MVC로 옮기면 이 입력이
`POST /purchases`, `POST /winning-numbers` 같은 HTTP 요청으로 갈라지고,
이제 controller는 문자열을 직접 `split()`하는 자리보다 요청 body나 form 값을
DTO로 받는 입구가 된다.

이때 자주 나오는 초기 구현은 controller가 `String numbers`를 받아 직접 자르고,
길이 검사와 숫자 변환, `Lotto.from(...)` 호출, 예외 메시지 번역까지 한 메서드에
모아 두는 형태다. 그러면 빈 요청, JSON 형식 오류, 구매 금액 형식 오류,
중복 번호, 범위 위반이 모두 비슷한 검증처럼 섞인다. 리뷰에서 "controller는
형식만, 로또 규칙은 도메인이"라는 말이 붙는 장면이 여기다.

## CS concept 매핑

Spring MVC에서 controller는 HTTP 입력을 메서드 인자로 바꾸는 자리다. 그래서
구매 금액이나 수동 번호는 `@RequestBody`나 `@ModelAttribute` DTO로 받고,
`@NotBlank`, 숫자 형식, 필드 존재 여부 같은 문 앞 검증을 먼저 처리하는 편이
맞다. 반면 `번호는 정확히 6개여야 한다`, `중복되면 안 된다`, `보너스 번호는
당첨 번호와 겹치면 안 된다`는 현재 입력 값들의 의미를 아는 도메인 객체가
끝까지 책임져야 한다.

짧게 말하면 controller 검증은 "이 요청이 HTTP 형식상 읽을 수 있는가"를 보고,
`Lotto`, `WinningNumbers`, `PurchaseAmount` 같은 타입은 "읽은 값이 미션 규칙상
유효한가"를 본다. 이 둘을 나누면 `400 잘못된 요청`과 도메인 규칙 위반을 서로
다른 층에서 설명할 수 있고, 콘솔 입력 경로와 웹 입력 경로도 같은 도메인 팩토리
로직을 재사용할 수 있다.

## 미션 PR 코멘트 패턴

- "`split()`과 숫자 변환이 controller에 있어도 되지만, 그 자리에서 곧바로 모든 로또 규칙까지 설명하면 HTTP 입구가 너무 많은 의미를 압니다.`"
- "`@Valid`는 형식 오류를 잡는 용도이고, 중복 번호나 보너스 번호 충돌은 도메인 생성 로직이 설명하게 두세요.`"
- "`InputView`를 없앴다고 해서 controller가 새 `InputView`가 되면 안 됩니다. DTO 바인딩과 도메인 팩토리 경계를 분리해 보세요.`"
- "`400 입력 오류`와 `미션 규칙 위반`을 같은 예외 덩어리로 다루면 이후 API 응답 설계와 테스트도 같이 흐려집니다.`"

## 다음 학습

- JSON 본문이 controller 전에 왜 `400`으로 끊기는지 먼저 가르려면 `spring/requestbody-400-before-controller-primer`
- `@RequestBody`와 `@ModelAttribute`를 어느 입력 장면에서 가를지 더 보려면 `spring/modelattribute-vs-requestbody-binding-primer`
- 콘솔 `InputView` 감각이 도메인 변환 경계와 어떻게 이어지는지 보려면 `software-engineering/lotto-inputview-domain-conversion-boundary-bridge`
- 번호 6개, 중복 없음, 범위 보장을 도메인이 왜 직접 쥐어야 하는지 복습하려면 `software-engineering/lotto-domain-invariant-bridge`
