# Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer

> 한 줄 요약: RoomEscape 스타일 관리자 페이지에서는 브라우저가 쿠키를 보내고, 서버가 세션에서 로그인 사용자를 찾고, Spring Security가 그 사용자의 관리자 권한을 확인하는 순서로 `/admin/**` 접근이 결정된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)
- [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring admin session cookie flow, admin login cookie session primer, roomescape admin auth beginner, browser cookie to spring session, jsessionid basics spring, admin endpoint authentication flow, 쿠키 세션 로그인 흐름 spring, 처음 배우는데 admin 인증, cookie 있는데 왜 다시 로그인, session id로 사용자 찾기, admin 302 login before 403, spring security session beginner, savedrequest basics spring, securitycontext 뭐예요, savedrequest 처음

## 핵심 개념

이 주제는 처음부터 용어로 들어가면 잘 안 잡힌다. 먼저 장면으로 보면 된다.

- 브라우저는 로그인 뒤 받은 쿠키를 다음 요청에 다시 보낸다.
- 서버는 그 쿠키 안의 세션 식별자(`JSESSIONID` 같은 값)로 "누가 로그인했는지"를 찾는다.
- Spring Security는 찾은 사용자가 `/admin/**`에 들어갈 자격이 있는지 확인한다.

즉 초급자 기준 큰 그림은 "`쿠키`는 브라우저가 들고 가는 표식", "`세션`은 서버가 로그인 상태를 기억하는 보관함", "`SecurityContext`는 이번 요청에서 바로 꺼내 쓰는 로그인 메모", "`SavedRequest`는 로그인 전에 가려던 주소 메모"다.

## 한눈에 보기

| 단계 | 브라우저/서버에서 실제로 하는 일 | 초급자 질문 |
|---|---|---|
| 로그인 성공 | 서버가 `Set-Cookie`로 세션 식별자를 내려준다 | "로그인 후 브라우저가 뭘 저장하지?" |
| 다음 관리자 요청 | 브라우저가 `Cookie` 헤더로 식별자를 다시 보낸다 | "왜 비밀번호를 다시 안 보내도 되지?" |
| 세션 조회 | 서버가 세션 저장소에서 로그인 사용자를 찾는다 | "쿠키만 있으면 바로 로그인인 건가?" |
| 요청 안 로그인 메모 복원 | Spring Security가 세션에서 `SecurityContext`를 꺼내 이번 요청 사용자 정보를 잡는다 | "로그인 정보는 어디서 바로 꺼내 쓰지?" |
| 권한 확인 | Spring Security가 `ADMIN` 여부를 검사한다 | "로그인은 됐는데 왜 `/admin`이 막히지?" |
| 로그인 전 주소 메모 사용 | 비로그인 상태였다면 `SavedRequest`로 원래 `/admin/**` 주소로 다시 보낼 수 있다 | "로그인 후 왜 아까 가던 관리자 화면으로 돌아가지?" |

비로그인 상태에서 먼저 `/admin/reservations`를 눌렀다면 Spring Security는 그 원래 URL을 `SavedRequest`처럼 잠깐 기억해 두었다가 로그인 성공 뒤 다시 보내 줄 수 있다. 초급자 기준으로는 "쿠키/세션은 로그인 상태를 이어 주고, `SavedRequest`는 로그인 후 돌아갈 주소를 기억한다"까지 같이 묶어 두면 된다.

```text
브라우저 로그인 성공
-> Set-Cookie: JSESSIONID=...

브라우저가 /admin/reservations 요청
-> Cookie: JSESSIONID=...
-> 서버가 세션에서 사용자 조회
-> Spring Security가 이번 요청용 로그인 메모(SecurityContext) 복원
-> Spring Security가 ADMIN 권한 확인
-> 통과면 controller, 실패면 302 /login 또는 403
```

핵심은 "쿠키가 곧 로그인 정보 그 자체"라고 보기보다, "쿠키는 서버가 세션을 다시 찾도록 돕는 표식"으로 보는 것이다.

## 용어를 한 번에 맞추기

초급자에게는 세 용어를 한 줄씩 고정해 두는 편이 덜 헷갈린다.

| 용어 | 초급 표현 | 여기서 맡는 역할 |
|---|---|---|
| `session` | 서버가 로그인 상태를 기억하는 보관함 | 쿠키가 가리키는 서버 쪽 저장소 |
| `SecurityContext` | 이번 요청에서 바로 꺼내 쓰는 로그인 메모 | 현재 요청 사용자가 누구인지 들고 가는 자리 |
| `SavedRequest` | 로그인 전에 가려던 주소 메모 | 로그인 성공 뒤 원래 `/admin/**`로 복귀시키는 힌트 |

즉 흐름은 "브라우저가 쿠키를 보낸다 -> 서버가 `session` 보관함을 찾는다 -> Spring Security가 그 안의 로그인 메모(`SecurityContext`)를 꺼내 쓴다 -> 비로그인 상태였다면 주소 메모(`SavedRequest`)를 참고해 다시 보낸다"로 읽으면 된다.

## 상세 분해

### 1. 로그인 직후 브라우저가 기억하는 것은 보통 쿠키다

RoomEscape 관리자 로그인 화면에서 아이디와 비밀번호를 제출하면, 서버는 로그인 성공 사실을 서버 쪽 세션에 기록하고 브라우저에는 쿠키를 내려준다.

이때 브라우저가 저장하는 것은 흔히 다음 둘 중 하나다.

- 세션 ID가 들어 있는 쿠키
- 로그인 유지에 필요한 다른 보조 쿠키

초급자는 여기서 "브라우저가 사용자 객체 전체를 저장하나?"라고 착각하기 쉽다. 보통은 아니다. 서버가 다시 찾을 수 있는 식별자 쪽에 가깝다.

### 2. 관리자 요청마다 브라우저는 쿠키를 자동으로 다시 보낸다

그다음 사용자가 `GET /admin/reservations`를 열면 브라우저는 이전 로그인 때 받은 쿠키를 자동으로 실어 보낸다.

그래서 사용자는 관리자 페이지를 열 때마다 아이디와 비밀번호를 다시 입력하지 않아도 된다.  
브라우저가 "이전에 로그인했던 흔적"을 매 요청에 같이 보내기 때문이다.

여기서 중요한 초급 감각은 이것이다.

- 로그인 폼 제출은 한 번이지만
- 쿠키 전송은 관리자 요청마다 반복된다

### 3. 서버는 쿠키 값으로 세션을 찾고, 그 안에서 로그인 사용자를 꺼낸다

서버는 쿠키를 받았다고 바로 "관리자 통과"로 결론 내리지 않는다. 먼저 그 쿠키 값으로 세션 저장소를 조회한다.

- 세션이 있으면 "어떤 사용자가 로그인했는지"를 복원한다
- 세션이 없거나 만료됐으면 익명 사용자처럼 본다

그래서 `cookie 있는데 다시 로그인` 같은 증상이 생길 수 있다.  
쿠키 자체는 브라우저에 남아 있어도, 서버 쪽 세션이 사라졌다면 다음 요청에서는 로그인 사용자를 복원하지 못한다.

### 4. Spring Security는 "로그인됨"과 "관리자임"을 따로 본다

로그인 사용자를 찾았다고 바로 `/admin/**`가 열리는 것은 아니다.

Spring Security는 보통 두 질문을 순서대로 본다.

1. 이 요청이 누구인지 확인됐는가
2. 그 사용자가 `ADMIN` 권한을 가졌는가

그래서 결과가 둘로 갈린다.

- 세션을 못 찾았거나 비로그인이면: 보통 로그인 쪽으로 보내거나 `401` 성격 응답
- 로그인은 됐지만 `ADMIN`이 아니면: `403`

즉 "인증"과 "인가"를 한 번에 뭉개면 `/admin` 문제를 자꾸 잘못 짚게 된다.

## 흔한 오해와 함정

- "쿠키가 있으니 로그인은 무조건 살아 있다"라고 생각하기 쉽다.  
  아니다. 서버 세션이 만료되었거나 찾지 못하면 쿠키가 있어도 다음 요청은 익명처럼 처리될 수 있다.

- "세션이 로그인 상태를 기억하니 Spring Security는 별개다"라고 생각하기 쉽다.  
  실제로는 Spring Security가 그 세션 기반 로그인 상태를 읽고, 이번 요청용 로그인 메모(`SecurityContext`)로 꺼낸 뒤 `/admin/**` 접근 여부를 판단한다.

- "`SavedRequest`도 로그인 사용자 정보가 들어 있는 곳인가?"라고 생각하기 쉽다.  
  아니다. `SavedRequest`는 로그인 정보가 아니라 "원래 어디로 가려 했는지"를 기억하는 주소 메모다.

- "`/admin`이 막혔으니 세션이 깨졌다"라고 바로 결론 내리기 쉽다.  
  이미 로그인은 됐지만 `ADMIN` 권한이 없어서 `403`인 경우도 많다.

- "로그인 후 원래 `/admin`으로 돌아왔으니 세션과 권한이 모두 끝까지 통과했다"라고 생각하기 쉽다.  
  실제로는 `SavedRequest`가 복귀만 도와준 뒤, 돌아온 URL에서 다시 `ADMIN` 권한 검사를 하므로 마지막에 `403`이 날 수도 있다.

- "로그인 성공 후 컨트롤러가 직접 쿠키를 계속 처리하나?"라고 생각하기 쉽다.  
  대부분의 흐름은 컨트롤러보다 앞단의 보안/서블릿 계층에서 자동으로 이어진다.

## 실무에서 쓰는 모습

RoomEscape 스타일 백오피스를 예로 들면 이런 흐름이다.

1. 관리자가 로그인 폼을 제출한다.
2. 서버는 로그인 성공 후 세션을 만들고 브라우저에 세션 쿠키를 보낸다.
3. 브라우저가 `GET /admin/reservations`를 호출할 때 그 쿠키를 자동 전송한다.
4. Spring Security는 세션에서 로그인 사용자를 복원한다.
5. 로그인 전에 막혔던 원래 관리자 URL이 있었다면 `SavedRequest`를 참고해 그 URL로 다시 복귀시킨다.
6. 사용자가 `ADMIN`이면 관리자 컨트롤러로 보낸다.
7. 비로그인이면 로그인 페이지 redirect나 인증 실패 응답으로 간다.
8. 로그인은 됐지만 권한이 부족하면 `403`으로 끝난다.

짧은 설정을 볼 때도 같은 흐름으로 읽으면 된다.

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/admin/**").hasRole("ADMIN")
    .anyRequest().permitAll()
);
```

이 설정은 "관리자 URL은 controller에서 따로 막자"가 아니라, "보안 계층에서 세션 기반 로그인 상태와 관리자 권한을 보고 먼저 결정하자"에 가깝다.

## 더 깊이 가려면

- `Filter`, security chain, interceptor가 어디서 갈리는지 먼저 보고 싶다면 [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)로 간다.
- `302 /login`과 `403`이 왜 갈리는지가 더 궁금하면 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)로 이어 간다.
- 로그인 후 원래 관리자 URL로 복귀하는 흐름이 섞이면 [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)를 본다.
- `session`, `SecurityContext`, `SavedRequest` 세 단어가 한 장면에서 섞여 헷갈리면 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)에서 "로그인 메모"와 "주소 메모"를 먼저 분리한다.
- 쿠키와 세션 개념 자체가 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)로 한 단계 내려가 다시 맞춘다.

## 면접/시니어 질문 미리보기

> Q: 브라우저가 관리자 로그인 상태를 다음 요청까지 어떻게 이어 가나요?
> 의도: cookie와 session 역할 분리 확인
> 핵심: 브라우저는 쿠키를 보내고, 서버는 그 값으로 세션을 찾아 로그인 사용자를 복원한다.

> Q: 세션 쿠키가 있는데도 왜 다시 `/login`으로 갈 수 있나요?
> 의도: cookie 존재와 session 유효성 구분 확인
> 핵심: 쿠키는 남아 있어도 서버 세션이 만료되었거나 찾히지 않으면 인증 상태를 복원하지 못할 수 있다.

> Q: 로그인은 되었는데 `/admin/**`가 `403`인 이유는 무엇인가요?
> 의도: authentication과 authorization 분리 확인
> 핵심: 세션으로 사용자는 확인됐지만 `ADMIN` 권한 검사가 실패했기 때문이다.

## 한 줄 정리

Spring 관리자 인증 흐름은 "브라우저가 쿠키를 보내고, 서버가 세션에서 로그인 사용자를 찾고, Spring Security가 관리자 권한을 확인한다"는 세 단계로 잡으면 초급자도 `/admin/**` 문제를 덜 헷갈린다.
