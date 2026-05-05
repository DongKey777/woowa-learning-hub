---
schema_version: 3
title: 같은 이름 Bean 충돌 원인 라우터
concept_id: spring/same-name-bean-collision-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
  - bean-name-collision
  - test-bean-override-boundary
  - conditional-backoff-vs-override
aliases:
- same bean name collision
- duplicate bean name startup
- BeanDefinitionOverrideException 원인
- overriding is disabled spring boot
- the bean could not be registered
- 같은 이름 빈 충돌
- bean 이름 중복으로 앱이 안 뜸
symptoms:
- startup 로그에 The bean 'paymentClient' could not be registered because a bean with that name has already been defined가 뜬다
- overriding is disabled가 나오면서 앱이 시작 전에 멈춘다
- 설정 클래스를 하나 더 추가했더니 같은 bean 이름 충돌 에러가 난다
- 테스트용 설정을 붙인 뒤부터 운영 bean과 이름이 겹친다고 나온다
intents:
- symptom
- troubleshooting
prerequisites:
- spring/bean-di-basics
next_docs:
- spring/spring-primary-vs-bean-override-primer
- spring/primary-conditionalonmissingbean-bean-override-decision-guide
- spring/bean-registration-path-decision-guide
- spring/same-type-bean-injection-failure-cause-router
linked_paths:
- contents/spring/spring-beandefinitionoverrideexception-quick-triage.md
- contents/spring/spring-primary-vs-bean-override-primer.md
- contents/spring/spring-primary-conditionalonmissingbean-bean-override-decision-guide.md
- contents/spring/spring-allow-bean-definition-overriding-test-boundaries-primer.md
- contents/spring/spring-bean-naming-qualifier-rename-pitfalls-primer.md
- contents/spring/spring-bean-registration-path-decision-guide.md
- contents/spring/spring-same-type-bean-injection-failure-cause-router.md
confusable_with:
- spring/same-type-bean-injection-failure-cause-router
- spring/bean-not-found-cause-router
- spring/spring-primary-vs-bean-override-primer
forbidden_neighbors:
- contents/spring/spring-same-type-bean-injection-failure-cause-router.md
- contents/spring/spring-bean-not-found-cause-router.md
expected_queries:
- Spring에서 같은 이름 bean 충돌이 나면 어디부터 봐야 해?
- BeanDefinitionOverrideException이 뜰 때 등록 충돌인지 back-off인지 어떻게 가르지?
- overriding is disabled가 보이면 설정을 켜기 전에 무엇을 확인해야 해?
- 테스트 설정을 붙였더니 duplicate bean name이 날 때 어떤 축으로 나눠 봐야 해?
- "@Primary 문제랑 bean 이름 충돌 문제를 어떻게 빠르게 구분해?"
contextual_chunk_prefix: |
  이 문서는 Spring startup에서 같은 이름 bean 충돌, duplicate bean
  name, BeanDefinitionOverrideException, The bean could not be
  registered, overriding is disabled 같은 학습자 증상을 실제 이름
  중복 / 테스트 override 섞임 / auto-configuration back-off 오독 /
  후보 선택 문제 오해로 나누는 symptom_router다. 앱이 시작 전에 멈춤,
  설정 클래스 추가 후 bean 이름이 겹침, @Primary로 풀릴 것 같다는
  자연어 검색을 올바른 다음 문서로 보내는 입구로 쓴다.
---

# 같은 이름 Bean 충돌 원인 라우터

## 한 줄 요약

> `BeanDefinitionOverrideException`은 대개 "주입 대상을 못 골랐다"보다 같은 이름 자리를 두 선언이 같이 차지하려는 상황이라서, 먼저 진짜 이름 충돌인지 back-off 오독인지부터 자르는 편이 빠르다.

## 가능한 원인

1. **실제로 같은 이름을 두 군데서 만들고 있다.** `@Bean` 메서드명 복붙, 명시적 `@Bean("name")`, component scan 이름이 겹치면 등록 단계에서 바로 막힌다. 이 갈래는 [BeanDefinitionOverrideException Quick Triage](./spring-beandefinitionoverrideexception-quick-triage.md)와 [Spring Bean 등록 경로 결정 가이드](./spring-bean-registration-path-decision-guide.md)로 이어진다.
2. **테스트 override 설정이 운영 설정과 섞였다.** `@TestConfiguration`, test profile, fake bean 교체 의도가 앱 전체 설정으로 번지면 "원래는 테스트에서만 바꾸려던 이름"이 충돌로 보일 수 있다. 이 경우는 [Spring `spring.main.allow-bean-definition-overriding` Boundaries Primer](./spring-allow-bean-definition-overriding-test-boundaries-primer.md)를 먼저 본다.
3. **사실은 override 예외가 아니라 auto-configuration back-off를 잘못 읽고 있다.** `existing bean`, `@ConditionalOnMissingBean did not match`는 충돌 후 패배보다 기본 bean이 애초에 안 만들어진 경우에 가깝다. 이 축은 [Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드](./spring-primary-conditionalonmissingbean-bean-override-decision-guide.md)로 내려간다.
4. **후보 선택 문제를 이름 충돌로 착각하고 있다.** 로그가 `found 2 beans`라면 같은 이름 충돌이 아니라 여러 후보 중 하나를 못 고른 상황이다. 이때는 [같은 타입 Bean이 여러 개라 주입이 안 돼요 원인 라우터](./spring-same-type-bean-injection-failure-cause-router.md)로 가야 한다.

## 빠른 자기 진단

1. 로그에 `The bean 'x' could not be registered`나 `overriding is disabled`가 보이면 이 문서 경로가 맞다. 반대로 `found 2 beans`가 보이면 [같은 타입 Bean이 여러 개라 주입이 안 돼요 원인 라우터](./spring-same-type-bean-injection-failure-cause-router.md)로 간다.
2. 최근 변경이 `@Bean` 메서드 rename, 새 `@Configuration` 추가, component scan 범위 확장이라면 이름 중복 가능성이 가장 높다. 이 경우 [Spring Bean 이름 규칙과 rename 함정 입문](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)과 [Spring Bean 등록 경로 결정 가이드](./spring-bean-registration-path-decision-guide.md)를 같이 본다.
3. 테스트에서만 깨지고 `@TestConfiguration`, test properties, fake client 교체가 보이면 운영 충돌이라기보다 테스트 override 경계일 수 있다. 그때는 [allow-bean-definition-overriding Boundaries Primer](./spring-allow-bean-definition-overriding-test-boundaries-primer.md)로 먼저 분기한다.
4. 예외 없이 condition report에만 `existing bean`이 보이면 충돌이 아니라 back-off다. 이 경우 [Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드](./spring-primary-conditionalonmissingbean-bean-override-decision-guide.md)로 이동한다.

## 다음 학습

- 이름 충돌과 후보 선택을 한 장으로 분리하려면 [Spring `@Primary` vs Bean Override Primer](./spring-primary-vs-bean-override-primer.md)를 본다.
- 등록 경로 자체를 정리하고 싶으면 [Spring Bean 등록 경로 결정 가이드](./spring-bean-registration-path-decision-guide.md)로 이어간다.
- Boot 기본 bean back-off까지 한 번에 나누고 싶으면 [Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드](./spring-primary-conditionalonmissingbean-bean-override-decision-guide.md)를 다음 문서로 고른다.
