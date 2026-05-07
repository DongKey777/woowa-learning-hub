---
schema_version: 3
title: Spring Security OPTIONS Primer
concept_id: security/spring-security-options-primer
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids: []
review_feedback_tags:
- spring security options primer
- spring security preflight options
- spring security options permitall
- spring boot cors options 401
aliases:
- spring security options primer
- spring security preflight options
- spring security options permitall
- spring boot cors options 401
- spring security options 403
- preflight blocked by spring security
- permit preflight without opening post
- options request permit actual post authenticated
- corsutils preflight request
- requestmatchers options permitall
- http cors withdefaults
- corsconfiguration source spring security
symptoms: []
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/security/preflight-debug-checklist.md
- contents/security/cors-basics.md
- contents/security/cors-samesite-preflight.md
- contents/security/error-path-cors-primer.md
- contents/security/xss-csrf-spring-security.md
- contents/spring/spring-cors-security-vs-mvc-ownership.md
- contents/spring/spring-security-filter-chain-ordering.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Spring Security OPTIONS Primer 핵심 개념을 설명해줘
- spring security options primer가 왜 필요한지 알려줘
- Spring Security OPTIONS Primer 실무 설계 포인트는 뭐야?
- spring security options primer에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Spring Security OPTIONS Primer를 다루는 primer 문서다. Spring Security에서 preflight `OPTIONS`를 통과시키는 목적은 "실제 API 보호를 푼다"가 아니라 "브라우저의 사전 확인만 막지 않는다"에 있다. 검색 질의가 spring security options primer, spring security preflight options, spring security options permitall, spring boot cors options 401처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Spring Security OPTIONS Primer

> 한 줄 요약: Spring Security에서 preflight `OPTIONS`를 통과시키는 목적은 "실제 API 보호를 푼다"가 아니라 "브라우저의 사전 확인만 막지 않는다"에 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Preflight Debug Checklist](./preflight-debug-checklist.md)
- [CORS 기초](./cors-basics.md)
- [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
- [Error-Path CORS Primer](./error-path-cors-primer.md)
- [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- [Spring CORS: Security vs MVC Ownership](../spring/spring-cors-security-vs-mvc-ownership.md)
- [Spring Security Filter Chain Ordering](../spring/spring-security-filter-chain-ordering.md)

retrieval-anchor-keywords: spring security options primer, spring security preflight options, spring security options permitall, spring boot cors options 401, spring security options 403, preflight blocked by spring security, permit preflight without opening post, options request permit actual post authenticated, corsutils preflight request, requestmatchers options permitall, http cors withdefaults, corsconfiguration source spring security, options 401 spring boot, beginner spring security cors, spring security options primer basics

## 먼저 잡을 mental model

브라우저가 cross-origin `POST`를 보내기 전에 `OPTIONS` preflight를 보내는 장면은, 사용자가 주문 생성 API를 호출한 것이 아니라 브라우저가 "이 요청을 시도해도 되나?"를 먼저 묻는 단계다.

그래서 beginner 규칙은 이 한 줄이면 충분하다.

- preflight `OPTIONS`는 **통과**
- actual `GET`/`POST`/`PUT`는 **원래대로 인증/인가 유지**

즉 `OPTIONS`를 열어 주는 일과 actual API를 보호하는 일은 서로 모순이 아니다.

## 왜 `OPTIONS 401/403`이 자주 나오나

Spring Security는 필터 체인에서 먼저 요청을 본다. 그런데 preflight도 그냥 HTTP 요청이기 때문에, 별도 처리가 없으면 다음처럼 읽힐 수 있다.

- `Authorization` 헤더가 없는 `OPTIONS`니까 익명 요청으로 본다
- 인증이 필요한 `/api/**` 규칙에 걸린다
- 그래서 `401` 또는 `403`을 먼저 돌려준다
- 브라우저는 actual `POST`를 아예 보내지 못한다

핵심은 이 실패가 actual API auth failure와 다르다는 점이다.

## 가장 안전한 beginner 패턴

Spring Security에서는 보통 두 가지를 같이 맞춘다.

| 필요한 것 | 왜 필요한가 | 빠지면 생기는 일 |
|---|---|---|
| `http.cors(...)` 또는 이에 준하는 CORS 연결 | Security가 CORS 정책을 이해하게 만든다 | 필터 체인 앞단에서 preflight가 막히거나 헤더가 불완전해진다 |
| preflight request만 `permitAll()` | 브라우저의 사전 확인만 통과시킨다 | `OPTIONS 401/403`이 나고 actual request가 안 간다 |

Spring Security 6 기준으로 beginner에게 가장 설명하기 쉬운 모습은 아래다.

## 가장 안전한 beginner 패턴 (계속 2)

```java
import java.util.List;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.cors.CorsUtils;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .cors(Customizer.withDefaults())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(CorsUtils::isPreFlightRequest).permitAll()
                .requestMatchers("/api/**").authenticated()
                .anyRequest().permitAll()
            )
            .build();
    }

    @Bean
    CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("https://app.example.com"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
        config.setAllowCredentials(true);

## 가장 안전한 beginner 패턴 (계속 3)

UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return source;
    }
}
```

이 구성의 의미는 단순하다.

- 브라우저 preflight는 통과시킨다
- `/api/**` actual request는 계속 인증을 요구한다
- 허용 origin/method/header는 CORS 정책에서 별도로 제한한다

## `OPTIONS /** permitAll()`은 언제 괜찮고, 언제 덜 좋은가

처음에는 아래처럼 시작하는 팀도 많다.

```java
.requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
```

이 패턴은 많은 API 서버에서 실제로 동작하고, beginner가 증상을 빨리 풀 때는 이해하기 쉽다. 다만 조금 더 안전하게 말하면 `CorsUtils::isPreFlightRequest`가 의도를 더 정확히 표현한다.

| 패턴 | 장점 | 주의점 |
|---|---|---|
| `requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()` | 단순하고 빠르게 읽힌다 | 브라우저 preflight가 아닌 다른 `OPTIONS`도 같이 열 수 있다 |
| `requestMatchers(CorsUtils::isPreFlightRequest).permitAll()` | "preflight만 허용" 의도가 더 정확하다 | Spring CORS 문맥을 함께 알아야 이해가 쉽다 |

beginner-safe 원칙은 이렇다.

- 빠른 응급처치로는 `OPTIONS /** permitAll()`도 가능
- 문서화된 기본 패턴으로는 `preflight만 permitAll()`이 더 낫다

## 하면 안 되는 우회

preflight가 막힌다고 아래처럼 고치면 문제를 옮길 수 있다.

- `/api/**` 전체를 `permitAll()`로 바꾸기
- `web.ignoring()`으로 보호 경로를 필터 체인 밖으로 빼기
- CORS 문제를 고치려고 인증 자체를 끄기
- CSRF 에러와 preflight 에러를 같은 문제로 보고 무조건 `csrf.disable()` 하기

짧게 정리하면:

- preflight는 **허용 규칙의 문제**
- actual API auth는 **보호 규칙의 문제**
- CSRF는 **상태 변경 요청 위조 방어 문제**

서로 다른 층이라서 한 번에 같은 스위치로 해결되지 않는다.

## 자주 헷갈리는 질문

### 1. "`OPTIONS`를 열어 주면 누구나 `POST`도 할 수 있는 것 아닌가요?"

아니다.

- preflight `OPTIONS` 통과는 browser probe를 허용하는 것
- actual `POST /api/**`는 여전히 `.authenticated()`나 권한 규칙을 통과해야 한다

즉 "문 앞에서 안내를 받는 것"과 "건물 안으로 들어가는 것"을 분리해서 보는 편이 맞다.

### 2. "`OPTIONS`에도 `Authorization` 헤더를 보내게 하면 안 되나요?"

브라우저 preflight는 actual request와 목적이 다르다. 보통은 preflight 자체를 인증시키려 하기보다, preflight를 통과시키고 actual request에서 인증을 검사한다.

### 3. "CORS를 켰는데도 왜 계속 `OPTIONS 401`이 나죠?"

아래 둘 중 하나가 흔하다.

- CORS 정책은 있는데 Security filter chain에서 preflight를 아직 permit하지 않았다
- 허용 method/header/origin이 actual 요청 조건과 맞지 않다

이때는 [Preflight Debug Checklist](./preflight-debug-checklist.md) 순서로 다시 보면 된다.

### 4. "세션 로그인 앱인데 preflight 때문에 CSRF를 꺼도 되나요?"

보통 안 된다.

preflight 통과와 CSRF 방어는 다른 문제다. 브라우저 쿠키 기반 세션 앱이라면 actual `POST`/`PUT`/`DELETE` 보호를 위해 CSRF가 여전히 필요할 수 있다. 이 분리는 [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)에서 이어서 보면 된다.

## 증상으로 바로 보기

| Network 장면 | 먼저 읽는 뜻 | 먼저 볼 것 |
|---|---|---|
| `OPTIONS /api/orders 401`, actual `POST` 없음 | Security가 preflight를 먼저 막았을 가능성 | preflight `permitAll`, CORS method/header/origin |
| `OPTIONS 204`, actual `POST 401` | preflight는 통과, 이제 actual auth failure | token/session/login 상태 |
| `OPTIONS 204`, actual `POST 403` | preflight는 통과, 이제 actual authz 또는 CSRF failure | 권한 규칙, ownership, CSRF |
| actual `POST 401/403`인데 프론트는 CORS라고 말함 | auth failure가 error-path CORS에 가려졌을 수 있음 | [Error-Path CORS Primer](./error-path-cors-primer.md) |

## 한 장으로 끝내는 체크리스트

1. `http.cors(...)`가 Security에 연결돼 있는지 본다.
2. preflight request만 `permitAll()` 하는 규칙이 있는지 본다.
3. CORS allowed origin/method/header가 실제 브라우저 요청과 맞는지 본다.
4. `/api/**` actual method 보호 규칙은 그대로 유지되는지 본다.
5. cookie/session 앱이면 CSRF 설정을 별도 문제로 다시 확인한다.

## 다음 문서

- Spring 필터 체인 순서까지 보고 싶으면: [Spring Security Filter Chain Ordering](../spring/spring-security-filter-chain-ordering.md)
- CORS 정책 owner를 Security/MVC 관점에서 나누고 싶으면: [Spring CORS: Security vs MVC Ownership](../spring/spring-cors-security-vs-mvc-ownership.md)
- 증상부터 다시 갈라야 하면: [Preflight Debug Checklist](./preflight-debug-checklist.md)

## 한 줄 정리

Spring Security에서 beginner-safe 패턴은 "preflight `OPTIONS`만 통과시키고, actual API 메서드 보호는 그대로 유지한다"이다.
