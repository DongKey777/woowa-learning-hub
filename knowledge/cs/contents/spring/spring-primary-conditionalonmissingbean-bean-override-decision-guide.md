---
schema_version: 3
title: Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드
concept_id: spring/primary-conditionalonmissingbean-bean-override-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
  - primary-vs-missingbean
  - bean-override-vs-candidate-selection
  - starter-backoff-misread
aliases:
- '@Primary vs @ConditionalOnMissingBean'
- '@Primary vs bean override'
- conditionalonmissingbean vs bean override
- 기본 bean 사라졌는데 primary 붙이면 되나
- found 2 beans라서 overriding 켜야 하나
- user bean 만들었더니 boot bean 없어짐
symptoms:
- starter bean이 안 떠서 @Primary를 붙여야 하나 헷갈려요
- 같은 타입 bean이 두 개인데 overriding을 켜면 되는지 모르겠어요
- 내 bean을 추가했더니 Boot 기본 bean이 사라진 것 같아요
intents:
- comparison
- troubleshooting
- design
prerequisites:
- spring/ioc-di-basics
- spring/bean-di-basics
next_docs:
- spring/primary-qualifier-collection-injection
- spring/spring-primary-vs-bean-override-primer
- spring/spring-conditionalonmissingbean-vs-primary-primer
linked_paths:
- contents/spring/spring-primary-qualifier-collection-injection-decision-guide.md
- contents/spring/spring-primary-vs-bean-override-primer.md
- contents/spring/spring-conditionalonmissingbean-vs-primary-primer.md
- contents/spring/spring-beandefinitionoverrideexception-quick-triage.md
- contents/spring/spring-starter-added-but-bean-missing-faq.md
confusable_with:
- spring/primary-qualifier-collection-injection
- spring/spring-primary-vs-bean-override-primer
- spring/spring-conditionalonmissingbean-vs-primary-primer
forbidden_neighbors:
- contents/spring/spring-allow-bean-definition-overriding-test-boundaries-primer.md
expected_queries:
- starter가 만든 bean이 안 보일 때 primary를 먼저 봐야 해?
- 같은 타입 bean이 두 개일 때 overriding을 켜는 문제랑 뭐가 달라?
- 내 bean을 등록했더니 기본 bean이 사라졌는데 conditional on missing bean 때문이야?
- bean 이름 충돌이랑 후보 선택이랑 auto-configuration back off를 어떻게 구분해?
- primary를 붙이면 boot 기본 bean이 다시 생겨?
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 bean 문제를 만났을 때 @Primary와
  @ConditionalOnMissingBean과 bean override를 같은 해결책으로 섞어
  읽는 상황을 가르는 chooser다. 같은 타입 bean이 두 개라 주입이
  깨짐, starter bean이 안 뜸, user bean을 만들었더니 Boot 기본 bean이
  사라짐, overriding을 켜야 하나, primary를 붙이면 복구되나 같은
  자연어 질문을 등록 단계 / back-off / 주입 우선순위 세 갈래로
  분리해서 다음 문서로 보내는 데 목적이 있다.
---

# Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드

## 한 줄 요약

> `@Primary`는 이미 등록된 후보 중 기본 주입 대상을 고르는 규칙이고, `@ConditionalOnMissingBean`은 Boot 기본 bean을 등록할지 말지 결정하며, bean override는 같은 이름 충돌을 등록 단계에서 다루는 스위치다.

## 결정 매트릭스

| 지금 보이는 신호 | 먼저 볼 축 | 왜 이쪽부터 보나 |
| --- | --- | --- |
| `expected single matching bean but found 2`가 뜬다 | `@Primary` / `@Qualifier` 같은 후보 선택 | bean은 이미 등록됐고, 지금 실패는 "하나로 못 고름"에 가깝다 |
| starter를 넣었는데 기본 bean이 아예 안 뜬다 | `@ConditionalOnMissingBean` back-off | user bean이나 다른 조건 때문에 Boot가 기본 bean 등록을 멈췄을 수 있다 |
| `The bean 'x' could not be registered`처럼 같은 이름 충돌이 난다 | bean override / 이름 충돌 | 주입 전에 bean definition 등록 단계에서 먼저 막힌다 |
| 내 bean을 만들었더니 Boot 기본 bean이 사라졌다 | `@ConditionalOnMissingBean`과 조건 평가 로그 | `@Primary`가 아니라 "이미 bean이 있으니 기본값을 만들지 않음"일 가능성이 크다 |
| 테스트에서만 fake bean이 같은 이름으로 들어간다 | bean override 경계와 테스트 전용 설정 | 운영 구조와 테스트 대체 전략을 섞으면 원인을 잘못 분류하기 쉽다 |

## 흔한 오선택

### 1. `found 2 beans`를 보고 overriding부터 켠다

학습자 표현으로는 "같은 타입 bean이 두 개니까 하나를 덮어쓰면 되지 않나요?"가 자주 나온다.  
하지만 이 경우는 이름 충돌이 아니라 후보 선택 문제다. bean 두 개를 등록한 채 기본값 하나를 정할지, 특정 주입 지점만 고를지부터 봐야 한다.

### 2. starter bean이 안 보여서 `@Primary`를 붙인다

"기본 bean이 안 뜨는데 primary를 붙이면 살아나나요?"라는 질문이 여기에 해당한다.  
`@Primary`는 이미 존재하는 후보의 우선순위만 바꾼다. Boot 기본 bean이 아예 등록되지 않았다면 `@ConditionalOnMissingBean`이나 다른 조건이 먼저 원인이다.

### 3. 이름 충돌 메시지를 `@ConditionalOnMissingBean`으로 푼다

"같은 이름 bean이 겹치니까 missing bean 조건을 더 넣어야 하나요?"처럼 읽는 경우다.  
이때는 auto-configuration back-off보다 bean definition 이름 충돌을 먼저 봐야 한다. 등록 자체가 막힌 상태라면 주입 우선순위나 기본 bean 선택 규칙으로는 해결되지 않는다.

### 4. 세 개를 한꺼번에 붙여서 우연히 되기만 기다린다

"일단 `@Primary`도 붙이고 overriding도 켜고 조건도 바꾸면 되겠지"는 학습 비용이 가장 크다.  
문제를 `후보 선택 / 기본 bean 등록 / 이름 충돌` 셋 중 하나로 먼저 자르면 다음에도 같은 로그를 더 빨리 읽을 수 있다.

## 다음 학습

- `found 2` 계열처럼 같은 타입 후보 선택이 핵심이면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)로 간다.
- "내 bean 때문에 Boot 기본 bean이 왜 사라졌지?"가 핵심이면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리](./spring-conditionalonmissingbean-vs-primary-primer.md)를 바로 잇는다.
- "같은 이름 bean이 왜 등록조차 안 되지?"가 핵심이면 [Spring `@Primary` vs Bean Override Primer](./spring-primary-vs-bean-override-primer.md)와 [BeanDefinitionOverrideException Quick Triage](./spring-beandefinitionoverrideexception-quick-triage.md)로 내려간다.
