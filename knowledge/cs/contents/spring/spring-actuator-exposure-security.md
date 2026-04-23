# Spring Actuator Exposure and Security

> 한 줄 요약: Actuator는 운영에 필요한 내부 정보를 보여 주지만, exposure와 security를 분리해서 설계하지 않으면 가장 유용한 진단 창구가 가장 위험한 공격면이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)
> - [Spring Startup Hooks: `CommandLineRunner`, `ApplicationRunner`, `SmartLifecycle`, and Readiness Warmup](./spring-startup-runner-smartlifecycle-readiness-warmup.md)
> - [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)

retrieval-anchor-keywords: actuator exposure, health endpoint, info endpoint, metrics endpoint, conditions endpoint, management port, exposure include exclude, endpoint security, operational surface

## 핵심 개념

Actuator는 운영 진단용 엔드포인트를 제공한다.

- health
- info
- metrics
- env
- conditions
- beans
- loggers

하지만 이 엔드포인트들은 내부 상태를 드러내므로, exposure 범위와 security 정책을 같이 설계해야 한다.

## 깊이 들어가기

### 1. actuator는 운영용 내부 API다

운영 중 상태를 보려면 actuator가 유용하다.

- health check
- readiness/liveness
- metric 수집
- 조건 평가 확인

### 2. exposure는 무엇을 열지 결정한다

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,conditions
```

이 설정은 노출 범위를 정한다.

### 3. security는 누가 볼 수 있는지 결정한다

노출을 제한해도 인증 없이 접근 가능하면 위험하다.

그래서 exposure와 security는 별개로 봐야 한다.

### 4. management port를 분리할 수도 있다

운영에서는 일반 앱 포트와 management 포트를 분리하기도 한다.

- 앱 트래픽
- 운영 트래픽
- 보안 정책

### 5. 민감한 endpoint는 기본적으로 조심해야 한다

`env`, `beans`, `mappings`, `conditions` 같은 엔드포인트는 내부 정보를 많이 드러낼 수 있다.

이건 디버깅에는 좋지만, 공개 범위는 신중해야 한다.

## 실전 시나리오

### 시나리오 1: health는 공개했는데 conditions까지 열렸다

이 경우 운영 정보가 너무 많이 노출될 수 있다.

### 시나리오 2: 로드밸런서가 health만 본다

이건 흔한 패턴이다.

- health는 public or restricted
- 나머지는 내부 인증 필요

### 시나리오 3: actuator는 열었는데 security chain에 안 걸린다

management endpoint용 별도 보안 정책이 필요할 수 있다.

이건 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)와 같이 봐야 한다.

### 시나리오 4: conditions endpoint를 보니 자동 구성이 왜 빠졌는지 바로 보인다

이건 [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)와 연결된다.

## 코드로 보기

### actuator exposure

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,conditions
```

### security rule

```java
@Bean
SecurityFilterChain managementChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/actuator/**")
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/actuator/health").permitAll()
            .anyRequest().hasRole("OPS")
        )
        .build();
}
```

### custom health indicator

```java
@Component
public class DiskHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        return Health.up().build();
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| public health only | 간단하다 | 정보가 적다 | LB/monitoring |
| selected endpoints | 진단과 안전의 균형 | 관리가 필요하다 | 일반 운영 |
| management port 분리 | 보안 경계가 명확하다 | 인프라가 늘어난다 | 보안 민감 서비스 |
| full exposure | 디버깅이 쉽다 | 위험하다 | 거의 권장하지 않음 |

핵심은 Actuator를 "편한 운영 UI"로 보지 말고, **보안이 필요한 내부 인터페이스**로 보는 것이다.

## 꼬리질문

> Q: Actuator의 exposure와 security는 왜 따로 봐야 하는가?
> 의도: 노출 vs 권한 제어 구분 확인
> 핵심: 열리는 것과 누가 보는 것은 다른 문제다.

> Q: health만 공개하고 나머지는 막는 이유는 무엇인가?
> 의도: 운영 최소 공개 원칙 확인
> 핵심: 모니터링에 필요한 최소 정보만 남기기 위해서다.

> Q: conditions endpoint가 왜 유용한가?
> 의도: Boot 자동 구성 디버깅 이해 확인
> 핵심: 어떤 조건이 켜지고 꺼졌는지 볼 수 있다.

> Q: management port를 분리하면 무엇이 좋아지는가?
> 의도: 운영 경계 이해 확인
> 핵심: 앱 트래픽과 운영 트래픽의 보안 경계를 나눌 수 있다.

## 한 줄 정리

Actuator는 운영 진단에 강력하지만, exposure와 security를 분리해 설계하지 않으면 가장 유용한 내부 엔드포인트가 가장 위험한 노출면이 된다.
