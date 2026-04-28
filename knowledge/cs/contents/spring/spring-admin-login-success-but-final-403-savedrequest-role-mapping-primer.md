# Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer

> 한 줄 요약: 로그인 성공과 `SavedRequest` 복귀는 "원래 URL로 다시 보내기"까지의 이야기이고, 마지막 `403`은 별도로 남아 있는 역할 매핑 문제라서 `redirect 복귀`와 `ROLE_ADMIN` 검사 실패를 두 단계로 끊어 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)
- [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Security 권한 매핑 함정: role, authority, revoke lag](../security/spring-authority-mapping-pitfalls.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring login success but 403, savedrequest after login 403, admin login restored url forbidden, spring role mapping beginner, role_admin prefix mismatch, hasrole admin 403, 로그인 성공했는데 403, 원래 url 복귀 후 403, savedrequest role mismatch, admin 권한 매핑 오류, spring security 역할 매핑 기초, requestcache 복귀 후 권한 실패, beginner savedrequest 403, why login succeeds but forbidden

## 핵심 개념

이 증상은 처음 보면 한 문장처럼 보인다.

- 로그인도 성공했다.
- 원래 가려던 `/admin/**` URL로도 돌아왔다.
- 그런데 마지막 화면은 `403 Forbidden`이다.

초급자 기준으로는 이 장면을 두 단계로 끊어야 한다.

1. `SavedRequest`가 원래 URL 복귀를 처리했다.
2. 복귀한 그 URL에서 Spring Security가 역할을 다시 검사했고, 여기서 실패했다.

즉 "`로그인 성공` = `관리자 권한 통과`"가 아니다.  
이 문서에서도 용어를 이렇게 고정해 두면 덜 헷갈린다.

| 용어 | 초급 표현 | 여기서 맡는 역할 |
|---|---|---|
| `session` | 서버가 로그인 상태를 기억하는 보관함 | 로그인 성공 뒤 다음 요청에서도 사용자를 다시 찾는 저장소 |
| `SecurityContext` | 이번 요청에서 바로 꺼내 쓰는 로그인 메모 | 지금 `/admin/**`에 들어온 사용자가 누구인지 들고 가는 자리 |
| `SavedRequest` | 로그인 전에 가려던 주소 메모 | 로그인 성공 뒤 원래 관리자 URL로 다시 보내는 힌트 |

즉 로그인 성공 뒤 `403`이 나는 장면은 "보관함에서 로그인 메모는 잘 꺼냈지만, 주소 메모를 따라 돌아간 관리자 URL에서 권한 검사가 막혔다"로 읽으면 된다.

## 한눈에 보기

| 지금 보인 현상 | 실제로 통과한 단계 | 아직 남아 있는 단계 | 먼저 볼 포인트 |
|---|---|---|---|
| `/login`까지 갔다가 로그인 성공 | 인증 단계 | 관리자 권한 검사 | 세션/인증 객체가 만들어졌는가 |
| 로그인 후 원래 `/admin/reservations`로 복귀 | `SavedRequest` 복귀 단계 | `/admin/**` 인가 검사 | 주소 메모가 정상인가 |
| 복귀 직후 최종 `403` | URL 복귀까지는 성공 | `hasRole("ADMIN")` 또는 authority 매핑 실패 | `ROLE_ADMIN`이 실제로 들어 있는가 |

```text
GET /admin/reservations
-> 비로그인
-> SavedRequest에 원래 URL 저장
-> /login 으로 이동
-> 로그인 성공
-> SavedRequest가 /admin/reservations 로 다시 보냄
-> Spring Security가 ADMIN 권한 검사
-> 권한 이름이 안 맞으면 최종 403
```

핵심은 "주소 메모를 따라 복귀했다"와 "관리자 권한까지 통과했다"를 같은 뜻으로 읽지 않는 것이다.

## 처음엔 세 단계를 따로 본다

1. 로그인 성공: 인증 객체가 만들어졌는가
2. 원래 URL 복귀: `SavedRequest`가 `/admin/**`로 다시 보냈는가
3. 최종 권한 통과: 현재 authorities가 `hasRole("ADMIN")` 또는 `hasAuthority(...)` 규칙과 맞는가

처음 배우는 단계에서는 이 세 단계를 섞지 않는 것이 가장 중요하다.

## 증상: 로그인 성공 후 원래 `/admin` URL로 돌아왔는데도 `403`

이 장면은 보통 `SavedRequest`가 망가진 것이 아니다. 오히려 반대로 `SavedRequest`는 주소 메모 역할을 잘 끝낸 경우가 많다.

- 처음 보호 URL을 기억했다.
- 로그인 성공 뒤 그 URL로 다시 보냈다.
- 그다음 요청에서 권한 검사까지 정상적으로 진행됐다.

그래서 마지막 `403`은 "`복귀 로직`이 틀렸다"보다 "`권한 이름이나 역할 매핑이 안 맞는다`" 쪽일 가능성이 높다.

특히 beginner가 자주 섞는 질문은 이것이다.

- "원래 URL로 돌아왔으니 이제 관리자 인증도 끝난 것 아닌가?"
- "로그인 성공 핸들러가 `/admin`으로 보냈는데 왜 또 막히지?"

둘 다 아니다. `/admin/**`는 돌아온 뒤에도 다시 검사한다.

## 상세 분해

### 1. `SavedRequest`는 역할을 올려 주지 않는다

`SavedRequest`는 "로그인 전에 어디를 가려고 했는지"만 기억하는 주소 메모다.  
사용자 권한을 `USER`에서 `ADMIN`으로 바꾸지 않는다.

그래서 일반 사용자 계정으로 로그인해도:

- 원래 `/admin/reservations`로 돌아갈 수는 있지만
- 그 URL에서 `ADMIN` 검사에 실패하면 최종 응답은 `403`이다

### 2. `hasRole("ADMIN")`은 내부적으로 `ROLE_ADMIN`을 찾는다

초급자가 많이 놓치는 지점이다.

```java
.requestMatchers("/admin/**").hasRole("ADMIN")
```

이 설정은 문자열 `"ADMIN"`을 그대로 비교하는 감각이 아니다.  
실제로는 보통 `ROLE_ADMIN` authority가 있는지를 본다.

그래서 아래처럼 어긋날 수 있다.

| 설정/데이터 | 실제 들어 있는 값 | 결과 |
|---|---|---|
| `hasRole("ADMIN")` | `ROLE_ADMIN` | 통과 |
| `hasRole("ADMIN")` | `ADMIN` | 보통 실패 |
| `hasAuthority("ADMIN")` | `ADMIN` | 통과 가능 |
| `hasAuthority("ROLE_ADMIN")` | `ROLE_ADMIN` | 통과 가능 |

즉 `role` 규칙과 `granted authority` 값이 같은 단어처럼 보여도, prefix 규칙이 다르면 `403`이 난다.

### 3. DB 역할, `UserDetails`, 변환기 중 어디선가 이름이 바뀔 수 있다

관리자 권한은 보통 여러 단계를 거친다.

- DB 컬럼에는 `ADMIN`
- `UserDetailsService`에서는 `SimpleGrantedAuthority("ADMIN")`
- 설정은 `hasRole("ADMIN")`

이 조합이면 로그인은 성공해도 마지막 인가에서 실패할 수 있다.

반대로 아래처럼 맞춰야 한다.

- DB 컬럼 `ADMIN`
- `UserDetailsService`에서 `SimpleGrantedAuthority("ROLE_ADMIN")`
- 설정은 `hasRole("ADMIN")`

또는

- DB 컬럼 `ADMIN`
- `UserDetailsService`에서 `SimpleGrantedAuthority("ADMIN")`
- 설정은 `hasAuthority("ADMIN")`

중요한 건 "어느 방식이 더 고급인가"가 아니라 **세 군데 이름이 일관적인가**다.

### 4. 최종 `403`은 인증 실패가 아니라 인가 실패다

로그인 성공 직후 최종 `403`이 났다면, 적어도 이 둘은 이미 어느 정도 성립했다.

- 인증 객체를 만들 수 있었다
- 로그인 후 복귀 흐름도 돌았다

그러므로 첫 질문은 "왜 다시 로그인하지?"가 아니라 "보관함에서 꺼낸 로그인 메모 안 authorities가 무엇이지?"여야 한다.

## 바로 써먹는 체크리스트

| 지금 확인할 항목 | 왜 먼저 보나 |
|---|---|
| 로그인 후 세션/인증 객체가 생겼는가 | 인증 자체는 통과했는지 확인하기 위해 |
| 복귀한 URL이 진짜 `/admin/**`였는가 | `SavedRequest`는 정상인데 대상 URL이 다른 경우를 빼기 위해 |
| 현재 authorities가 `ROLE_ADMIN`인지 `ADMIN`인지 | `hasRole`/`hasAuthority` 규칙과 이름이 맞는지 보려면 이것이 핵심이기 때문 |

초급자 기준으로는 "로그인 성공 로그"보다 **현재 authority 문자열이 무엇인지**가 더 직접적인 단서가 된다.

## 흔한 오해와 함정

- "`SavedRequest`가 `/admin`으로 돌려보냈으니 Security도 관리자라고 인정한 것이다"라고 생각하기 쉽다.  
  아니다. 주소 메모는 복귀만 돕고, 관리자 여부는 그 뒤 로그인 메모의 권한으로 다시 본다.

- "`403`이니 로그인이 사실 실패한 것이다"라고 생각하기 쉽다.  
  아니다. 로그인 실패였다면 보통 `/login` 재이동이나 인증 실패 응답이 먼저 보인다.

- "DB에 `ADMIN` 문자열이 있으니 `hasRole(\"ADMIN\")`도 자동으로 맞는다"라고 생각하기 쉽다.  
  아니다. `ROLE_` prefix 규칙 때문에 `GrantedAuthority`로 바뀌는 순간 이름이 달라질 수 있다.

- "권한이 부족하면 `SavedRequest`가 원래 URL로 복귀하지 않아야 한다"라고 생각하기 쉽다.  
  주소 메모는 복귀까지만 담당하므로, 복귀 후 막혀도 이상한 동작이 아니다.

## 실무에서 쓰는 모습

RoomEscape 스타일 관리자 화면을 예로 들면 이런 흐름이다.

1. 비로그인 사용자가 `/admin/reservations`를 요청한다.
2. Spring Security가 원래 URL을 저장하고 `/login`으로 보낸다.
3. 사용자가 일반 계정으로 로그인한다.
4. 로그인 성공 핸들러 또는 `SavedRequest`가 `/admin/reservations`로 다시 보낸다.
5. 서버는 현재 사용자의 authorities를 꺼내 `ADMIN` 규칙을 검사한다.
6. 이때 값이 `ROLE_ADMIN`이 아니라 `ADMIN`만 들어 있거나, 반대로 설정과 다른 형식이면 최종 `403`이 난다.

짧게 보면 이런 설정-데이터 일치가 중요하다.

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/admin/**").hasRole("ADMIN")
    .anyRequest().permitAll()
);
```

이 설정을 쓴다면 로그인 사용자에게 실제로 `ROLE_ADMIN` authority가 들어오는지 같이 확인해야 한다.

## 더 깊이 가려면

- 먼저 `302 /login`과 `403`의 큰 분기를 다시 고정하고 싶다면 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)로 돌아간다.
- 쿠키, 세션, 로그인 사용자 복원이 `/admin/**` 판단까지 어떻게 이어지는지 다시 묶고 싶다면 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)를 본다.
- 로그인 후 원래 URL 복귀 자체가 왜 생기는지 더 깊게 들어가려면 [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)로 이어 간다.
- `hasRole`, `GrantedAuthority`, `AuthorizationFilter`가 어디서 만나는지 더 정확히 보고 싶다면 [Spring Security Filter Chain](./spring-security-filter-chain.md)을 본다.
- role 이름과 authority 이름이 어디서 어긋나는지 사례 중심으로 더 보고 싶다면 [Security 권한 매핑 함정: role, authority, revoke lag](../security/spring-authority-mapping-pitfalls.md)를 본다.
- 쿠키와 세션 개념이 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)로 한 단계 내려간다.

## 면접/시니어 질문 미리보기

> Q: 로그인 성공 후 원래 관리자 URL로 복귀했는데 왜 `403`이 날 수 있나요?
> 의도: `SavedRequest`와 authorization 분리 확인
> 핵심: 복귀는 `SavedRequest`가 처리하고, 그 뒤 `ADMIN` 역할 검사는 별도로 다시 수행되기 때문이다.

> Q: `hasRole("ADMIN")`과 `hasAuthority("ADMIN")`는 왜 결과가 다를 수 있나요?
> 의도: role prefix 규칙 이해 확인
> 핵심: `hasRole("ADMIN")`은 보통 내부적으로 `ROLE_ADMIN` authority를 기대하기 때문이다.

> Q: 이런 상황에서 가장 먼저 확인할 값은 무엇인가요?
> 의도: 디버깅 우선순위 확인
> 핵심: 현재 인증 객체의 authorities와 `requestMatchers("/admin/**")` 규칙이 같은 이름 체계를 쓰는지다.

## 한 줄 정리

로그인 성공 후 `SavedRequest`가 원래 `/admin/**` URL로 돌려보내는 것과, 그 URL에서 `ROLE_ADMIN` 검사를 통과하는 것은 별개이므로 복귀 직후 `403`이 나면 먼저 역할 매핑 불일치를 의심해야 한다.
