---
schema_version: 3
title: Spring `@ComponentScan` vs `@EntityScan` vs `@EnableJpaRepositories` 결정 가이드
concept_id: spring/componentscan-entityscan-enablejparepositories-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- componentscan-entityscan-enablejparepositories
- componentscan-vs-entityscan
- entityscan-vs-enablejparepositories
- scanbasepackages-jpa-split
aliases:
- '@ComponentScan vs @EntityScan'
- '@EntityScan vs @EnableJpaRepositories'
- component scan entity scan repository scan 차이
- scanbasepackages jpa split
- Not a managed type vs repository bean not found
symptoms:
- scanBasePackages를 넓혔는데 entity나 repository는 여전히 안 잡혀요
- service는 뜨는데 Not a managed type이 나요
- controller는 뜨는데 JpaRepository bean만 못 찾겠어요
intents:
- comparison
- troubleshooting
- design
prerequisites:
- spring/ioc-di-basics
- spring/bean-di-basics
next_docs:
- spring/component-scan-failure-patterns
- spring/jpa-entityscan-enablejparepositories-boundaries
- spring/scanbasepackages-vs-import-autoconfiguration-selection
linked_paths:
- contents/spring/spring-component-scan-failure-patterns.md
- contents/spring/spring-jpa-entityscan-enablejparepositories-boundaries.md
- contents/spring/spring-scanbasepackages-vs-import-autoconfiguration-selection.md
- contents/spring/spring-boot-autoconfiguration.md
confusable_with:
- spring/component-scan-failure-patterns
- spring/jpa-entityscan-enablejparepositories-boundaries
- spring/scanbasepackages-vs-import-autoconfiguration-selection
forbidden_neighbors:
- contents/spring/spring-boot-autoconfiguration.md
expected_queries:
- component scan이랑 entity scan은 언제 갈라서 봐야 해?
- scanBasePackages를 넓혔는데 왜 JPA 쪽은 그대로 깨져?
- Not a managed type이 뜨면 @EntityScan부터 봐야 해?
- repository bean이 없을 때 @EnableJpaRepositories가 필요한 순간은 언제야?
- service는 뜨는데 JPA만 안 뜰 때 어떤 scan을 의심해야 해?
contextual_chunk_prefix: |
  이 문서는 학습자가 Spring multi-module이나 패키지 경계를 만지다가
  component scan과 entity scan과 repository scan을 한 덩어리로 착각해
  어디 annotation을 손대야 할지 못 고르는 상황을 가르는 chooser다.
  scanBasePackages를 넓혔는데 JPA는 왜 안 돼, service는 뜨는데 entity만
  안 잡혀, repository bean not found, Not a managed type, component scan과
  entity scan 차이, @EnableJpaRepositories는 언제 쓰나 같은 자연어 질문이
  이 문서의 세 갈래 결정표에 매핑된다.
---
# Spring `@ComponentScan` vs `@EntityScan` vs `@EnableJpaRepositories` 결정 가이드

## 한 줄 요약

> bean이 안 뜨면 `@ComponentScan`, entity가 managed type이 아니면 `@EntityScan`, `JpaRepository` bean이 없으면 `@EnableJpaRepositories`부터 본다.

## 결정 매트릭스

| 지금 보이는 신호 | 먼저 의심할 경계 | 왜 이쪽부터 보나 |
| --- | --- | --- |
| `@Service`, `@Controller`, `@Configuration` bean이 안 뜬다 | `@ComponentScan` | stereotype bean 탐색 경계가 끊기면 JPA보다 앞단에서 바로 누락된다 |
| `Not a managed type`, entity metadata build 실패가 난다 | `@EntityScan` | entity는 component scan 대상이 아니라 JPA 메타데이터 경계를 따로 탄다 |
| `NoSuchBeanDefinitionException`으로 `JpaRepository` 주입이 실패한다 | `@EnableJpaRepositories` | repository interface discovery가 기본 패키지 밖으로 밀려난 경우가 많다 |
| `scanBasePackages`를 넓혔는데 JPA만 그대로 깨진다 | `@EntityScan` 또는 `@EnableJpaRepositories` | `scanBasePackages`는 component scan alias라서 entity/repository 경계를 같이 넓히지 않는다 |
| shared module을 붙이려다 scan 범위 전체가 흔들린다 | `@Import`/auto-configuration 문서로 이동 | 지금 문제는 scan 종류보다 module 등록 전략 자체일 수 있다 |

## 흔한 오선택

### 1. service가 안 뜨는데 `@EntityScan`부터 붙인다

학습자 표현으로는 "Spring이 bean을 못 찾는데 JPA annotation을 더 붙이면 되나요?"가 자주 나온다.  
이 경우는 entity 문제가 아니라 stereotype bean 탐색이 먼저 끊긴 경우가 많다. `OrderService`나 `AdminController`가 안 뜨면 `@SpringBootApplication` 위치와 `@ComponentScan` 경계를 먼저 본다.

### 2. `Not a managed type`인데 `scanBasePackages`만 더 넓힌다

"scanBasePackages를 `com.example`로 넓혔는데 왜 그대로예요?"라는 질문이 여기에 해당한다.  
이 에러는 대개 entity metadata 등록 실패라서 `@EntityScan` 경계를 따로 맞춰야 한다. component scan을 더 넓혀도 `@Entity`가 자동으로 따라오지 않는다.

### 3. repository bean이 없는데 `@EntityScan`만 추가한다

"entity는 찾게 했는데 `OrderJpaRepository`는 아직도 없어요"라는 식으로 보인다.  
이때는 repository interface discovery가 아직 기본 경계 밖에 있다. `@EnableJpaRepositories` 또는 Boot 기본 repository 경계를 다시 맞춰야 한다.

### 4. 세 annotation을 한 번에 다 붙여 놓고 원인을 구분하지 않는다

"일단 다 넣었는데 왜 되는지 모르겠어요"는 학습 효과가 가장 낮다.  
증상을 `bean 누락 / entity 누락 / repository 누락`으로 먼저 자르면, 다음에 같은 문제가 나와도 어느 축인지 바로 분기할 수 있다.

## 다음 학습

- bean 자체가 왜 안 뜨는지 더 자세히 역추적하려면 [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md)을 본다.
- JPA 경계 함정을 예시와 함께 더 깊게 보려면 [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)을 잇는다.
- shared module 등록 전략까지 섞여 있다면 [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)으로 넘어간다.
