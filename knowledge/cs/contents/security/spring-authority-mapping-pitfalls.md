# Spring Authority Mapping Pitfalls

> 한 줄 요약: Spring Security에서 JWT 검증은 성공했는데 `403`이 뜬다면, 대개 `claim은 있는데 authority가 비어 있음` 또는 `ROLE_/SCOPE_ mismatch`처럼 `claim -> GrantedAuthority` 매핑과 `hasRole` / `hasAuthority` 문자열 계약이 어긋난 것이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
> - [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [Spring Security Filter Chain](../spring/spring-security-filter-chain.md)
> - [Security README: 기본 primer](./README.md#기본-primer)
> - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: spring authority mapping pitfalls, spring security authority mapping, spring security confusing 403, spring security valid jwt but 403, jwt authenticated but forbidden, jwt claim to authority mapping, JwtAuthenticationConverter 403, JwtGrantedAuthoritiesConverter 403, authorities claim mapping mismatch, scope claim mapping mismatch, roles claim mapping mismatch, groups claim mapping mismatch, ROLE_ prefix mismatch, SCOPE_ prefix mismatch, ROLE_/SCOPE_ mismatch, hasRole vs hasAuthority, hasRole 403, hasAuthority 403, granted authority mismatch, access denied after jwt auth, spring security access denied jwt, custom jwt converter loses scopes, custom jwt converter roles only, roles claim not mapped to ROLE_, scope claim not mapped to SCOPE_, authorityPrefix drift, authoritiesClaimName mismatch, valid token empty authorities, claim은 있는데 authority가 비어 있음, claim은 있는데 authority가 없음, authority가 비어 있음, spring method security 403 jwt, spring resource server authority debug

## 먼저 떠올릴 그림

입문자 기준으로는 이렇게만 먼저 잡으면 된다.

```text
토큰 claim이 있다
-> Spring이 claim을 authority 문자열로 바꾼다
-> guard가 그 authority 문자열을 비교한다
```

여기서 많이 깨지는 첫 문장이 바로 두 가지다.

- `claim은 있는데 authority가 비어 있음`
- `ROLE_/SCOPE_ mismatch`

즉 JWT 안에 재료가 보여도, Spring이 만든 authority가 비어 있거나 guard가 다른 prefix를 찾으면 결과는 `403`이다.

## 이 문서 다음에 보면 좋은 문서

- claim, role, authority, permission 자체의 층위가 먼저 헷갈리면 [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)로 먼저 올라가면 된다.
- `401`과 `403`의 경계부터 다시 잡고 싶으면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)를 보면 된다.
- OAuth `scope`, token `audience`, 내부 app permission을 따로 분리해 읽고 싶으면 [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)으로 이어 가면 된다.
- `role을 바꿨는데 old token이 계속 남는다`, `재로그인 후에야 403이 풀린다` 같은 freshness 문제는 [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)로 이어진다.
- 필터 체인에서 인증이 어디서 끝나고 인가가 어디서 거절되는지 보고 싶으면 [Spring Security Filter Chain](../spring/spring-security-filter-chain.md)을 같이 보면 된다.

---

## 먼저 15초 판별표

`403`이 나왔다는 사실만으로는 "권한이 없다"보다 "문자열 계약이 틀렸다"가 더 흔한 경우가 있다.

| 겉으로 보이는 현상 | 실제로 자주 깨지는 계약 | 왜 헷갈리는가 | 먼저 볼 것 |
|---|---|---|---|
| JWT 서명 검증은 통과했는데 `@PreAuthorize("hasRole('ADMIN')")`가 `403` | authority는 `ADMIN`인데 guard는 `ROLE_ADMIN`을 기대함 | 로그인은 됐으니 role도 자동으로 읽혔다고 착각함 | 실제 `Authentication#getAuthorities()` 값 |
| `claim은 있는데 authority가 비어 있음`처럼 `roles`, `groups`, `scope`는 보이는데 guard는 계속 `403` | converter가 그 claim을 실제 authority로 안 올렸거나, custom converter가 기존 authority를 지움 | claim이 보이면 Spring authority도 자동으로 생긴다고 착각함 | 실제 `Authentication#getAuthorities()`가 비어 있는지부터 확인 |
| token에 `scope=orders.read`가 있는데 `hasAuthority('orders.read')`가 `403`, 즉 `ROLE_/SCOPE_ mismatch`가 의심됨 | Spring이 보는 authority는 보통 `SCOPE_orders.read` | claim 문자열과 authority 문자열을 같은 말로 읽음 | scope claim이 어떤 prefix로 authority가 됐는지 |
| custom `JwtAuthenticationConverter`를 넣은 뒤 scope 기반 endpoint가 전부 `403` | custom converter가 기존 scope 매핑을 덮어써서 `SCOPE_...` authority가 사라짐 | roles 추가만 했다고 생각했는데 default behavior를 교체함 | custom converter가 merge인지 replace인지 |
| `roles`, `groups` claim은 보이는데 `hasRole`은 계속 `403` | 현재 converter가 custom role claim을 authority로 올리지 않음 | claim이 있으면 Spring도 바로 role로 본다고 생각함 | converter가 어떤 claim 이름을 읽는지 |
| `hasAuthority('ROLE_ADMIN')`는 통과하는데 `hasRole('ADMIN')` 쪽만 실패, 혹은 반대 | prefix를 커스터마이즈했는데 annotation/DSL/test가 예전 규칙을 그대로 씀 | prefix를 한 군데만 바꾸고 전 구간이 같이 바뀐다고 착각함 | prefix 설정과 guard 문자열의 일치 여부 |

핵심은 이것이다.

- JWT가 유효하다고 해서 필요한 authority가 생긴 것은 아니다.
- authority가 있어도 guard가 다른 문자열을 찾으면 `403`이다.
- 그래서 Spring `403`은 종종 "권한 모델 자체가 틀렸다"보다 "매핑 표면이 어긋났다"는 신호다.

---

## 왜 `401`이 아니라 `403`으로 보이는가

이 failure는 보통 인증 실패가 아니라 인가 표면 mismatch다.

```text
JWT 서명 / iss / aud / exp 검증 성공
-> Authentication 생성 성공
-> GrantedAuthority 목록 생성
-> hasRole / hasAuthority / method security 검사
-> 기대 문자열이 없어서 deny
-> 외부 응답은 403
```

즉 "token이 valid한데 왜 403이지?"라는 질문이면, 바로 다음 단계는 JWT 파싱보다 authority 문자열 비교다.

---

## 1. custom `JwtAuthenticationConverter`가 기존 scope 매핑을 날려 버린다

가장 흔한 실수는 role claim을 추가하고 싶어서 converter를 커스터마이즈했는데, 원래 있던 scope authority 생성을 같이 잃어버리는 경우다.

문제 코드 예시:

```java
@Bean
JwtAuthenticationConverter jwtAuthenticationConverter() {
    JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
    converter.setJwtGrantedAuthoritiesConverter(jwt ->
        jwt.getClaimAsStringList("roles").stream()
            .map(role -> new SimpleGrantedAuthority("ROLE_" + role))
            .toList()
    );
    return converter;
}
```

이렇게 하면 `roles`는 들어오지만 기존 `SCOPE_...` authority가 사라질 수 있다.
그래서 `hasAuthority("SCOPE_orders.read")`가 갑자기 전부 `403`으로 바뀐다.

보통은 merge가 맞다.

```java
@Bean
JwtAuthenticationConverter jwtAuthenticationConverter() {
    JwtGrantedAuthoritiesConverter scopes = new JwtGrantedAuthoritiesConverter();

    JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
    converter.setJwtGrantedAuthoritiesConverter(jwt -> {
        Set<GrantedAuthority> authorities = new LinkedHashSet<>(scopes.convert(jwt));
        List<String> roles = jwt.getClaimAsStringList("roles");

        if (roles != null) {
            for (String role : roles) {
                authorities.add(new SimpleGrantedAuthority("ROLE_" + role));
            }
        }

        return authorities;
    });
    return converter;
}
```

디버깅할 때는 "roles를 추가했는가?"보다 "scope authority를 보존했는가?"를 먼저 본다.

---

## 2. `claim은 있는데 authority가 비어 있음`

`roles`, `groups`, `authorities` claim이 토큰에 보인다고 해서 Spring이 그 이름을 자동으로 business role로 해석하는 것은 아니다.

자주 생기는 상황:

- IdP는 `roles=["ADMIN"]`를 넣는다.
- 앱은 기본 scope mapping만 믿는다.
- 결과적으로 `Authentication`에는 `SCOPE_...`만 있고 `ROLE_ADMIN`은 없다.
- `hasRole("ADMIN")`는 계속 `403`이다.

이 경우 질문은 "토큰에 role이 있나?"가 아니라 "그 claim이 실제 `GrantedAuthority`로 변환됐나?"여야 한다.

즉 아래 둘은 다르다.

- JWT claim: `roles=["ADMIN"]`
- Spring authority: `ROLE_ADMIN`

중간 변환이 없으면 두 값은 절대로 만나지 않는다.

---

## 3. `hasRole`과 `hasAuthority`는 같은 말이 아니다

이 mismatch 하나만으로도 403이 많이 생긴다.

| 실제 authority 목록 | 통과하는 검사 | 실패하는 검사 |
|---|---|---|
| `ROLE_ADMIN` | `hasRole("ADMIN")`, `hasAuthority("ROLE_ADMIN")` | `hasAuthority("ADMIN")` |
| `ADMIN` | `hasAuthority("ADMIN")` | `hasRole("ADMIN")` |
| `SCOPE_orders.read` | `hasAuthority("SCOPE_orders.read")` | `hasAuthority("orders.read")`, `hasRole("orders.read")` |

기억할 점은 단순하다.

- `hasRole("ADMIN")`는 role 이름을 넣는 표현이다.
- `hasAuthority("ROLE_ADMIN")`는 완성된 authority 문자열을 넣는 표현이다.
- `hasAuthority("orders.read")`는 `SCOPE_` prefix가 이미 제거된 상태를 기대하는 셈이라 자주 틀린다.

팀이 authority vocabulary를 어떻게 정했는지 모르면, guard를 보기 전에 실제 authority 목록부터 캡처하는 편이 빠르다.

---

## 4. `ROLE_/SCOPE_ mismatch`는 보통 prefix 계약 문제다

실무에서 `ROLE_`와 `SCOPE_`를 섞어 읽기 시작하면 디버깅이 어려워진다.

- `ROLE_ADMIN`은 보통 coarse role gate다.
- `SCOPE_orders.read`는 보통 delegated API scope다.

둘 다 authority 문자열이지만 같은 뜻은 아니다.

그래서 아래 같은 코드가 자주 헷갈린다.

```java
@PreAuthorize("hasRole('orders.read')")
public OrderResponse readOrder() { ... }
```

이 코드는 role vocabulary와 scope vocabulary를 섞은 것이다.
`orders.read`가 scope에서 왔다면 보통 `hasAuthority("SCOPE_orders.read")` 쪽이 맞다.

반대로 관리자 role이면 보통 아래 둘 중 하나다.

```java
@PreAuthorize("hasRole('ADMIN')")
@PreAuthorize("hasAuthority('ROLE_ADMIN')")
```

role과 scope를 같은 prefix로 강제로 맞추면 당장은 통과해도, 나중에 문서/테스트/운영 로그에서 "이 문자열이 role인지 scope인지"가 다시 흐려진다.

---

## 5. prefix를 바꿨으면 guard, 테스트, 문서도 같이 바꿔야 한다

일부 팀은 authority prefix를 비우거나 custom prefix를 쓴다.
문제는 converter 설정만 바꾸고 annotation이나 request matcher는 예전 문자열을 계속 쓰는 경우다.

대표 사례:

- authority는 `ADMIN`으로 만들었는데 코드에는 계속 `hasRole("ADMIN")`
- authority는 `PERM_refund.approve`인데 코드에는 `hasAuthority("refund.approve")`
- scope prefix를 바꿨는데 테스트 fixture는 여전히 `SCOPE_orders.read`

이 문제는 설정 한 줄보다 "문자열 계약이 몇 군데 흩어져 있는가"가 핵심이다.

확인 순서는 이렇다.

1. converter가 실제로 무슨 authority 문자열을 내는지 본다.
2. `requestMatchers`, `@PreAuthorize`, 테스트 fixture가 정확히 같은 문자열을 기대하는지 본다.
3. README나 운영 runbook의 예시까지 같은 vocabulary를 쓰는지 확인한다.

---

## 6. 디버깅은 claim이 아니라 authority부터 본다

confusing 403을 가장 빨리 줄이는 체크리스트는 아래다.

1. JWT claim을 본다.
   `scope`, `scp`, `roles`, `groups` 같은 입력이 실제로 무엇인지 확인한다.
2. 현재 `Authentication#getAuthorities()`를 본다.
   claim이 authority로 어떻게 변환됐는지 여기서 끝난다.
3. guard 문자열을 본다.
   `hasRole("ADMIN")`, `hasAuthority("SCOPE_orders.read")`가 실제 authority와 정확히 일치하는지 비교한다.
4. custom converter가 merge인지 replace인지 본다.
   roles를 넣으면서 scopes를 잃어버렸는지 자주 확인한다.
5. `401`인지 `403`인지 다시 구분한다.
   principal이 만들어졌으면 보통 매핑/인가 문제다.

로그는 이 정도만 있어도 충분하다.

```java
Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

log.info("principal={}, authorities={}",
    authentication.getName(),
    authentication.getAuthorities());
```

여기서 authorities가 비어 있거나 기대와 다른 prefix를 쓰면, controller/service를 더 파기 전에 converter와 guard부터 맞추는 편이 빠르다.

---

## 짧은 기억법

- claim은 입력이다.
- authority는 Spring이 비교하는 문자열이다.
- `hasRole("ADMIN")`는 role 이름을 넣는 표현이다.
- `hasAuthority("SCOPE_orders.read")`는 완성된 authority 문자열을 넣는 표현이다.
- valid JWT + wrong authority mapping = 매우 흔한 `403`이다.

## 한 줄 정리

Spring Security의 confusing `403`은 JWT 검증 실패보다 `JwtAuthenticationConverter`, authority prefix, `hasRole` / `hasAuthority` 문자열 계약 불일치에서 자주 나온다. 토큰 claim보다 실제 `GrantedAuthority` 목록을 먼저 보면 원인을 훨씬 빨리 좁힐 수 있다.
