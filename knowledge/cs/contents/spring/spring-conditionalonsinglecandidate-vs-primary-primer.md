# Spring `@ConditionalOnSingleCandidate` vs `@Primary` Primer: activation 조건과 주입 우선순위는 다르다

> 한 줄 요약: `@ConditionalOnSingleCandidate`는 "이 타입을 지금 주입하려 하면 하나로 결정되는가?"를 보고 자동 구성을 켤지 정하는 activation 조건이고, `@Primary`는 이미 등록된 후보들 사이에서 기본 주입 대상을 정하는 규칙이다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `@ConditionalOnSingleCandidate`를 `@Primary`의 다른 이름처럼 오해하는 지점을 끊어 주는 **beginner primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
> - [Spring `@ConditionalOnBean` 경계 노트: activation과 DI 후보 선택은 다르다](./spring-conditionalonbean-activation-vs-di-candidate-selection-primer.md)
> - [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)

retrieval-anchor-keywords: @conditionalonsinglecandidate vs @primary, conditionalonsinglecandidate activation condition, conditionalonsinglecandidate is not injection priority, single candidate can be determined, autowiring would succeed, primary candidate condition, boot auto configuration activation vs injection, conditionalonsinglecandidate multiple beans primary bean, datasource conditionalonsinglecandidate primer, jdbctemplateautoconfiguration single candidate, primary does not activate auto configuration, condition positive but qualifier injection different, beginner spring conditional single candidate, spring autoconfiguration candidate selection boundary, spring conditionalonsinglecandidate vs primary primer basics

## 먼저 mental model

초보자 기준으로는 아래 두 줄만 먼저 잡으면 된다.

- `@ConditionalOnSingleCandidate`: **켜도 되는지**를 본다
- `@Primary`: **기본으로 무엇을 넣을지**를 본다

조금 더 정확히 말하면 `@ConditionalOnSingleCandidate`는 이런 질문이다.

```text
"이 타입을 지금 autowire 하려고 하면
Spring이 하나의 후보를 결정할 수 있나?"
```

그래서 이 annotation은 **주입 규칙 자체**가 아니라,
그 주입이 성공 가능해 보일 때만 자동 구성이나 `@Bean` 등록 경로를 여는 **activation gate**다.

반대로 `@Primary`는 이미 후보가 여러 개 등록된 뒤에 단일 주입 지점에서 기본값 하나를 고르는 규칙이다.

---

## 한눈에 비교

| 구분 | `@ConditionalOnSingleCandidate` | `@Primary` |
|---|---|---|
| 핵심 질문 | "이 타입은 지금 하나로 결정 가능한가?" | "여러 후보 중 기본 후보는 누구인가?" |
| 주된 역할 | auto-configuration / bean 등록 활성화 조건 | 단일 dependency injection 우선순위 |
| 동작 시점 | 조건 평가, 등록 경로를 열기 전 | 실제 생성자/필드/`@Bean` 파라미터 주입 시 |
| 자주 붙는 곳 | Boot auto-configuration 클래스나 `@Bean` | 사용자 bean 정의나 component |
| 여러 후보일 때 | 하나만 있거나, `primary` 후보가 결정되면 통과할 수 있다 | 정확히 하나의 primary candidate면 그 bean이 기본값이 된다 |
| 하지 않는 일 | bean을 주입해 버리지는 않는다 | 꺼져 있던 auto-configuration을 켜지 않는다 |

핵심은 이 한 줄이다.

```text
@ConditionalOnSingleCandidate는 "단일 후보로 결정 가능하면 등록",
@Primary는 "등록된 뒤 단일 주입 기본값 결정"이다.
```

---

## 왜 activation condition인가

Spring Boot 공식 문서 기준으로 `@ConditionalOnSingleCandidate`는

- 지정한 타입의 bean이 이미 있어야 하고
- 그 타입에 대해 single candidate를 결정할 수 있어야 하며
- 여러 bean이 있어도 primary candidate가 정해져 있으면 match할 수 있다

는 조건이다.

즉 이 annotation은 "`@Primary`를 대신 붙이는 법"이 아니라,
**"이 타입을 의존하는 보조 bean을 안전하게 켤 수 있을까?"**를 판단하는 Boot 쪽 조건이다.

초보자 관점에서는 아래처럼 읽으면 된다.

```text
DataSource가 여러 개 있어도
Spring이 기본으로 쓸 하나를 결정할 수 있으면
이 auto-configuration을 켜도 된다.
```

그래서 이름에 `SingleCandidate`가 들어가지만,
"bean이 정확히 하나만 있어야 한다"는 뜻으로만 읽으면 반쯤 틀린다.
여러 개가 있어도 **하나로 결정 가능**하면 통과할 수 있기 때문이다.

---

## 예제 1. 조건은 `@Primary`를 참고할 수 있지만, 둘은 같은 역할이 아니다

아래처럼 자동 구성이 있다고 가정하자.

```java
@AutoConfiguration
@ConditionalOnSingleCandidate(DataSource.class)
public class ReportJdbcAutoConfiguration {

    @Bean
    public ReportJdbcClient reportJdbcClient(DataSource dataSource) {
        return new ReportJdbcClient(dataSource);
    }
}
```

애플리케이션에는 `DataSource`가 두 개 있다.

```java
@Configuration
public class DataSourceConfig {

    @Bean
    @Primary
    public DataSource mainDataSource() {
        return buildMain();
    }

    @Bean
    public DataSource auditDataSource() {
        return buildAudit();
    }
}
```

이 흐름은 이렇게 읽는다.

1. `DataSource` bean은 둘이다.
2. 하지만 `@Primary`가 붙은 `mainDataSource`가 있어 Spring은 기본 단일 후보를 결정할 수 있다.
3. 그래서 `@ConditionalOnSingleCandidate(DataSource.class)`가 통과할 수 있다.
4. 그 결과 `ReportJdbcAutoConfiguration`이 활성화되고 `reportJdbcClient` 등록 경로가 열린다.

여기서 중요한 포인트는 이것이다.

- 조건이 통과한 이유에 `@Primary` 정보가 **참고될 수는 있다**
- 하지만 `@ConditionalOnSingleCandidate` 자체는 여전히 **활성화 조건**이다
- 실제로 bean을 "선택해서 주입하는 규칙" 그 자체가 된 것은 아니다

즉 `@Primary`는 이 조건의 입력 중 하나일 수 있지만,
두 annotation의 역할은 여전히 다르다.

---

## 예제 2. `@Primary`가 있다고 해서 아무 주입 지점이나 같은 bean을 받는 것은 아니다

같은 환경에서 아래 서비스가 있다고 보자.

```java
@Service
public class AuditService {

    public AuditService(@Qualifier("auditDataSource") DataSource dataSource) {
    }
}
```

여기서는 `@ConditionalOnSingleCandidate(DataSource.class)`가 이미 통과했더라도,
`AuditService`는 `mainDataSource`가 아니라 `auditDataSource`를 받는다.

왜냐하면 여기서는 질문이 다르기 때문이다.

- auto-configuration 쪽 질문: "`DataSource`를 하나로 결정할 수 있나?"
- `AuditService` 쪽 질문: "이번 주입 지점은 정확히 어느 `DataSource`여야 하나?"

후자에서는 `@Qualifier`가 더 구체적인 규칙이므로 `@Primary` 기본값보다 우선한다.

즉 `@ConditionalOnSingleCandidate`가 positive match라고 해서
모든 주입 지점이 같은 bean으로 고정되는 것은 아니다.

---

## 가장 흔한 오해

| 헷갈리는 말 | 맞는 해석 |
|---|---|
| "`@ConditionalOnSingleCandidate`는 `@Primary`랑 거의 같다" | 아니다. 전자는 activation condition이고 후자는 injection priority다. |
| "`SingleCandidate`니까 bean이 정확히 1개여야 한다" | 아니다. 여러 개여도 primary candidate가 결정되면 match할 수 있다. |
| "`@ConditionalOnSingleCandidate`가 통과했으니 그 타입 주입은 어디서나 안전하다" | 아니다. 다른 주입 지점은 `@Qualifier`, 이름, generic 등 더 구체적인 규칙에 따라 다를 수 있다. |
| "`@Primary`를 붙이면 관련 auto-configuration이 자동으로 켜진다" | 아니다. 그 auto-configuration이 실제로 이 조건을 쓰는지, 다른 classpath/property 조건은 없는지까지 봐야 한다. |

---

## `@ConditionalOnBean`과는 무엇이 다른가

이 둘도 자주 같이 섞인다.

| 조건 | 묻는 것 |
|---|---|
| `@ConditionalOnBean(DataSource.class)` | "`DataSource`가 있나?" |
| `@ConditionalOnSingleCandidate(DataSource.class)` | "`DataSource`를 지금 하나로 결정할 수 있나?" |

즉 `@ConditionalOnBean`은 **존재 여부**에 가깝고,
`@ConditionalOnSingleCandidate`는 **단일 후보 결정 가능성**까지 본다.

그래서 `DataSource`가 둘인데 `@Primary`가 없으면:

- `@ConditionalOnBean(DataSource.class)`는 통과할 수 있다
- `@ConditionalOnSingleCandidate(DataSource.class)`는 실패할 수 있다

이 차이를 먼저 잡아 두면 condition report를 읽을 때 훨씬 덜 헷갈린다.

---

## 디버깅 순서

1. target auto-configuration이 정말 `@ConditionalOnSingleCandidate`를 쓰는지 본다.
2. condition report에서 positive/negative match를 먼저 확인한다.
3. negative면 해당 타입 bean이 아예 없는지, 여러 개인데 primary candidate를 못 정하는지 본다.
4. positive인데 다른 서비스 주입이 기대와 다르면 그건 주입 지점의 `@Qualifier`/이름/타입 규칙 문제로 분리해서 본다.
5. "`found 2`" 같은 오류가 난다면 auto-configuration 조건과 실제 injection point를 같은 문제로 뭉개지 말고 각각 본다.

짧게 보면 이 순서다.

```text
조건이 켜졌는가?
-> 어떤 bean이 기본 단일 후보로 보였는가?
-> 특정 주입 지점은 또 어떤 규칙을 쓰는가?
```

---

## 언제 무엇을 떠올리면 되나

| 내가 궁금한 것 | 먼저 떠올릴 도구 |
|---|---|
| "이 자동 구성이 왜 안 켜졌지?" | `@ConditionalOnSingleCandidate` 같은 activation condition |
| "같은 타입 후보가 여러 개인데 기본값은 누구지?" | `@Primary` |
| "이번 생성자 파라미터는 꼭 저 bean이어야 한다" | `@Qualifier` |
| "조건은 통과했는데 다른 곳 주입이 왜 다르지?" | injection point별 규칙이 다를 수 있음을 먼저 의심 |

---

## 꼬리질문

> Q: `@ConditionalOnSingleCandidate`를 한 줄로 설명하면?
> 의도: activation condition으로 이해하는지 확인
> 핵심: 지정한 타입이 이미 존재하고, Spring이 그 타입을 단일 후보로 결정할 수 있을 때만 bean/auto-configuration을 활성화하는 조건이다.

> Q: `SingleCandidate`인데 bean이 2개 있어도 통과할 수 있나?
> 의도: "정확히 1개" 오해를 분리
> 핵심: 그렇다. 여러 후보 중 primary candidate를 결정할 수 있으면 통과할 수 있다.

> Q: 조건이 통과했는데 어떤 서비스는 다른 bean을 받는 이유는?
> 의도: activation과 injection을 분리하는지 확인
> 핵심: condition은 등록을 켤 뿐이고, 각 주입 지점의 실제 선택은 `@Qualifier`, 이름, generic 같은 일반 주입 규칙이 다시 결정한다.

## 한 줄 정리

`@ConditionalOnSingleCandidate`는 `@Primary`의 별칭이 아니라, "`이 타입을 지금 autowire 하면 하나로 정해질 수 있는가?`"를 보고 자동 구성을 켤지 판단하는 activation 조건이다. `@Primary`는 그 이후 실제 단일 주입에서 기본 후보를 정하는 규칙이다.
