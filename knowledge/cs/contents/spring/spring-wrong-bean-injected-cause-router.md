---
schema_version: 3
title: 원하는 Bean이 안 들어가요 원인 라우터
concept_id: spring/wrong-bean-injected-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/lotto
- missions/shopping-cart
review_feedback_tags:
- bean-selection-boundary
- primary-qualifier-misread
- conditional-backoff-confusion
aliases:
- 원하는 빈이 안 들어감
- 엉뚱한 bean 주입
- 다른 구현체가 주입됨
- primary 붙였는데도 이상함
- qualifier 안 먹는 느낌
- 스프링 빈 선택이 꼬임
symptoms:
- 같은 인터페이스 구현이 여러 개인데 내가 기대한 Bean 대신 다른 구현체가 들어가요
- '@Primary를 붙였는데도 테스트나 실행 환경에서 엉뚱한 Bean이 선택돼요'
- starter 기본 Bean이 들어오는 것 같고 내가 만든 Bean이 안 써져요
- 빈은 등록된 것 같은데 주입 시점에 못 고르거나 다른 Bean으로 연결돼요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/spring-bean-di-basics
next_docs:
- spring/same-type-bean-injection-failure-cause-router
- spring/primary-qualifier-collection-injection
- spring/primary-conditionalonmissingbean-bean-override-decision-guide
- spring/bean-registration-path-decision-guide
- spring/bean-not-found-cause-router
linked_paths:
- contents/spring/spring-same-type-bean-injection-failure-cause-router.md
- contents/spring/spring-primary-qualifier-collection-injection-decision-guide.md
- contents/spring/spring-primary-conditionalonmissingbean-bean-override-decision-guide.md
- contents/spring/spring-bean-registration-path-decision-guide.md
- contents/spring/spring-bean-not-found-cause-router.md
- contents/spring/spring-same-name-bean-collision-cause-router.md
- contents/spring/spring-runtime-strategy-router-vs-qualifier-boundaries.md
- contents/spring/spring-componentscan-entityscan-enablejparepositories-decision-guide.md
confusable_with:
- spring/same-type-bean-injection-failure-cause-router
- spring/primary-qualifier-collection-injection
- spring/primary-conditionalonmissingbean-bean-override-decision-guide
forbidden_neighbors: []
expected_queries:
- 스프링에서 같은 타입 구현이 여러 개인데 왜 내가 생각한 Bean이 아니라 다른 구현이 들어가요?
- '@Primary를 붙였는데도 원하는 구현체가 선택되지 않을 때 어디부터 나눠서 봐야 해?'
- starter가 만든 기본 Bean과 내가 만든 Bean이 섞일 때 원인을 어떻게 분기해?
- Bean은 등록된 것 같은데 주입 단계에서 엉뚱한 구현이 연결되면 어떤 문서를 먼저 봐?
- 실행 환경마다 다른 Bean이 들어오는 것처럼 보일 때 선택 규칙과 등록 경로를 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 학습자가 Spring에서 "원하는 Bean이 안 들어가요", "엉뚱한
  구현체가 주입돼요", "@Primary를 붙였는데도 이상해요", "starter 기본 Bean이
  선택돼요" 같은 자연어 증상을 후보 선택 실패 / 조건부 기본 Bean back-off /
  등록 경로 착오 / 런타임 전략 선택과 주입 선택 혼동 네 갈래로 나누는
  symptom_router다. 같은 타입 여러 개, 다른 구현체 주입, qualifier 안 먹는
  느낌 같은 검색을 원인 문서로 보내는 입구로 사용한다.
---

# 원하는 Bean이 안 들어가요 원인 라우터

## 한 줄 요약

> 원하는 Bean이 안 들어간다는 말은 대개 "Bean이 없어서 실패"보다 "여러 후보 중 무엇을 고르는지", "기본 Bean이 뒤로 물러났는지", "애초에 등록 경로가 달랐는지"를 섞어 본 상태다.

## 가능한 원인

1. **같은 타입 후보가 여러 개인데 선택 규칙을 아직 안 정했다.** 로그에 `expected single matching bean but found 2` 같은 문장이 보이면 가장 먼저 [같은 타입 Bean이 여러 개라 주입이 안 돼요 원인 라우터](./spring-same-type-bean-injection-failure-cause-router.md)와 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)로 간다.
2. **사실은 `@Primary` 문제가 아니라 Boot 기본 Bean back-off나 override 경계다.** `@ConditionalOnMissingBean`, `existing bean`, auto-configuration report가 같이 보이면 [Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드](./spring-primary-conditionalonmissingbean-bean-override-decision-guide.md)가 더 가깝다.
3. **Bean이 어떤 경로로 등록됐는지부터 서로 달랐다.** `@ComponentScan`, `@EntityScan`, `@EnableJpaRepositories`, `@Configuration` 추가 이후부터 증상이 생겼다면 [Spring Bean 등록 경로 결정 가이드](./spring-bean-registration-path-decision-guide.md)와 [Spring `@ComponentScan` vs `@EntityScan` vs `@EnableJpaRepositories` 결정 가이드](./spring-componentscan-entityscan-enablejparepositories-decision-guide.md)로 먼저 자른다.
4. **주입 시점 선택과 런타임 전략 선택을 같은 문제로 묶었다.** `Map<String, Bean>`이나 router 패턴으로 런타임에 고르는 경우를 `@Qualifier` 문제로 읽으면 갈래가 틀어진다. 이때는 [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)를 본다.
5. **실제로는 원하는 Bean이 "없다".** 선택 실패처럼 느껴져도 로그가 `NoSuchBeanDefinitionException`이면 후보 경쟁보다 등록 자체가 실패한 것이다. 그때는 [Spring Bean이 안 보여요 원인 라우터](./spring-bean-not-found-cause-router.md)로 내려간다.

## 빠른 자기 진단

1. 로그에 `found 2 beans`, `NoUniqueBeanDefinitionException`이 보이면 "없음"이 아니라 "여러 개 중 못 고름"이다.
2. condition evaluation report나 starter 설정이 같이 보이면 `@Primary`만 만지기 전에 back-off 문서로 분기한다.
3. 최근 변경이 scan 범위, `@Configuration`, repository 패키지 구조였다면 등록 경로가 바뀐 것이다.
4. 코드가 주입 시점에 하나를 고르는 게 아니라 요청 값에 따라 여러 Bean 중 하나를 꺼내는 구조면 런타임 전략 축으로 봐야 한다.
5. 아예 Bean 조회가 안 되거나 타입 후보 수가 `0`이면 이 문서보다 Bean 미등록 원인 라우터가 먼저다.

## 다음 학습

- 같은 타입 후보 충돌부터 좁히려면 [같은 타입 Bean이 여러 개라 주입이 안 돼요 원인 라우터](./spring-same-type-bean-injection-failure-cause-router.md)를 먼저 본다.
- `@Primary`, `@Qualifier`, 컬렉션 주입 중 무엇이 맞는지 고르려면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)로 이어간다.
- starter 기본 Bean과 내 Bean이 충돌하는지 보려면 [Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드](./spring-primary-conditionalonmissingbean-bean-override-decision-guide.md)를 바로 읽는다.
- scan, repository, configuration 등록 경로가 헷갈리면 [Spring Bean 등록 경로 결정 가이드](./spring-bean-registration-path-decision-guide.md)와 [Spring `@ComponentScan` vs `@EntityScan` vs `@EnableJpaRepositories` 결정 가이드](./spring-componentscan-entityscan-enablejparepositories-decision-guide.md)를 같이 본다.
- 사실은 Bean 자체가 없는 증상이라면 [Spring Bean이 안 보여요 원인 라우터](./spring-bean-not-found-cause-router.md)로 내려간다.
