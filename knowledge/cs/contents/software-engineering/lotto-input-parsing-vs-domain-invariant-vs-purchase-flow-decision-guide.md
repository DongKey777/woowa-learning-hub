---
schema_version: 3
title: 'lotto 입력 파싱 vs 도메인 불변식 vs 구매 흐름 결정 가이드'
concept_id: software-engineering/lotto-input-parsing-vs-domain-invariant-vs-purchase-flow-decision-guide
canonical: false
category: software-engineering
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/lotto
review_feedback_tags:
- boundary-choice-confusion
- input-vs-domain-vs-service
- purchase-flow-separation
aliases:
- lotto 경계 선택 기준
- 로또 입력 검증 도메인 서비스 구분
- lotto InputView vs Lotto vs Service
- 로또 어디부터 분리해야 해
- lotto 파싱과 불변식 차이
- 로또 구매 흐름 책임 위치
- lotto boundary chooser
symptoms:
- InputView가 Lotto를 만들고 service도 검증해서 어디가 주인인지 모르겠어요
- 리뷰에서 파싱은 밖으로, 불변식은 도메인으로, 구매 흐름은 service로 나누라는데 같은 말처럼 들려요
- 로또 코드가 길어졌는데 지금 잘라야 할 축이 입력인지 규칙인지 유스케이스 순서인지 헷갈려요
intents:
- comparison
- design
- mission_bridge
prerequisites:
- software-engineering/lotto-inputview-domain-conversion-boundary-bridge
- software-engineering/lotto-domain-invariant-bridge
- software-engineering/lotto-purchase-flow-service-layer-bridge
next_docs:
- software-engineering/lotto-inputview-domain-conversion-boundary-bridge
- software-engineering/lotto-domain-invariant-bridge
- software-engineering/lotto-purchase-flow-service-layer-bridge
linked_paths:
- contents/software-engineering/lotto-inputview-domain-conversion-boundary-bridge.md
- contents/software-engineering/lotto-domain-invariant-bridge.md
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
- contents/software-engineering/lotto-boundary-mixing-cause-router.md
confusable_with:
- software-engineering/lotto-inputview-domain-conversion-boundary-bridge
- software-engineering/lotto-domain-invariant-bridge
- software-engineering/lotto-purchase-flow-service-layer-bridge
forbidden_neighbors:
- contents/software-engineering/lotto-inputview-domain-conversion-boundary-bridge.md
- contents/software-engineering/lotto-domain-invariant-bridge.md
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
expected_queries:
- 로또 미션에서 문자열 split은 밖에서 하고 6개 중복 검사는 Lotto가 하라는 말이 정확히 어떻게 다른 거야?
- InputView가 숫자 리스트를 만들고 service가 여러 장을 구매시키는 흐름에서 각 단계 책임을 어떻게 나눠?
- 로또 리뷰에서 지금 고쳐야 할 게 입력 변환 문제인지 도메인 규칙 문제인지 구매 orchestration 문제인지 빨리 구분하고 싶어
- 컨트롤러에서 Lotto를 만들고 반복문도 돌리고 있는데 무엇부터 service로 옮기고 무엇은 도메인에 남겨야 해?
- 로또 코드가 한 메서드에 몰렸을 때 파싱, 불변식, 구매 흐름을 어떤 질문으로 가르면 돼?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션에서 InputView 문자열 파싱, Lotto 한 장의
  불변식 보장, 구매 금액으로 여러 장을 조립하는 service 흐름이 한 코드에
  섞였을 때 무엇을 입력 변환 경계, 무엇을 도메인 규칙, 무엇을 유스케이스
  orchestration으로 봐야 하는지 가르는 chooser다. split 이후 도메인 생성,
  6개 중복 검사 위치, 구매 반복문 위치, 지금 어디부터 잘라야 하는지 같은
  학습자 질문을 세 가지 책임 축으로 매핑한다.
---

# lotto 입력 파싱 vs 도메인 불변식 vs 구매 흐름 결정 가이드

## 한 줄 요약

> 문자열을 숫자로 읽는 질문이면 입력 파싱, `Lotto`가 항상 유효해야 하느냐를 묻는 순간이면 도메인 불변식, 구매 금액으로 몇 장을 어떻게 만들지 묻는 순간이면 service 흐름으로 자르면 된다.

## 결정 매트릭스

| 지금 코드가 답해야 하는 질문 | 먼저 볼 경계 | 왜 그쪽이 맞는가 |
|---|---|---|
| `"1,2,3,4,5,6"`을 어떻게 나누고 숫자로 바꿀까? | 입력 파싱 경계 | 바깥 문자열 표현을 안쪽에서 쓸 값으로 바꾸는 번역 문제다. |
| `Lotto`가 항상 6개, 중복 없음, 1-45를 만족해야 하나? | 도메인 불변식 | 어떤 진입점에서 만들든 계속 지켜야 하는 타입 계약이다. |
| 구매 금액으로 몇 장을 사고 어떤 순서로 생성기를 호출할까? | 구매 흐름 service | 한 번의 유스케이스를 끝까지 조립하는 orchestration 문제다. |
| controller에 `split`, `Lotto.from`, `for` 반복문이 한꺼번에 있나? | 입력 파싱 + service | 문자열 번역과 여러 장 구매 순서가 동시에 새고 있다는 신호다. |
| `Lotto` 안에서 `money / 1000`이나 `Random` 호출까지 하고 있나? | 도메인 불변식 밖 | 한 장 규칙 객체가 유스케이스 흐름까지 품어 책임이 커진 상태다. |

## 흔한 오선택

입력 파싱 문제를 도메인 불변식 문제로만 보는 경우:
`"split만 했는데 왜 Lotto를 여기서 만들면 안 되죠?"`라는 질문은 흔하다. 문자열 형식 오류와 도메인 규칙 예외는 성격이 다르므로, 먼저 숫자 목록으로 번역한 뒤 도메인 팩토리로 넘기는 편이 설명이 쉽다.

도메인 불변식을 service 검증으로 대신하는 경우:
`"service에서 이미 6개인지 확인했으니 Lotto는 그냥 담아도 되지 않나요?"`라는 식이면 타입 계약이 호출자에게 새고 있다. 자동 생성기나 테스트 코드가 같은 객체를 만들 때도 규칙이 유지되어야 하므로, 최종 보장은 `Lotto` 쪽에 남아야 한다.

구매 흐름을 도메인 객체 안으로 밀어 넣는 경우:
`"Lotto가 여러 장도 만들고 금액 계산도 하면 더 객체지향 같은데요?"`라는 오해가 자주 나온다. 한 장 규칙과 여러 장 구매 순서는 바뀌는 이유가 다르기 때문에, 반복 생성과 장수 계산은 service가 조립하는 편이 덜 꼬인다.

## 다음 학습

- 입력 계층이 어디까지 번역하고 어디서 도메인 생성으로 넘기는지 보려면 [lotto InputView 문자열 파싱 ↔ DTO/도메인 변환 경계 브릿지](./lotto-inputview-domain-conversion-boundary-bridge.md)
- `Lotto`가 왜 자기 규칙을 스스로 보장해야 하는지 보려면 [lotto 번호 6개·중복없음·1-45 도메인 불변식을 어디에서 보장하나](./lotto-domain-invariant-bridge.md)
- 여러 장 구매를 한 번의 유스케이스 흐름으로 묶는 이유를 보려면 [lotto 여러 장 구매 흐름 ↔ Service 계층 브릿지](./lotto-purchase-flow-service-layer-bridge.md)
- 코드가 이미 한 군데로 몰려 있다면 먼저 [lotto 책임 경계가 자꾸 섞여요 원인 라우터](./lotto-boundary-mixing-cause-router.md)로 원인부터 자를 수 있다.
