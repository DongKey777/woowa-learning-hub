# OAuth2 기초: 내 앱이 왜 다른 서비스의 API를 쓸 수 있나

> 한 줄 요약: OAuth2는 사용자가 비밀번호를 공유하지 않고도 제3자 앱이 특정 권한으로 내 자원에 접근할 수 있도록 허가하는 표준 위임 프로토콜이다.

**난이도: 🟢 Beginner**

관련 문서:

- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [Spring Security 기초](../spring/spring-security-basics.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: oauth2 basics, oauth2가 뭔가요, oauth2 입문, 소셜 로그인 원리, 구글 로그인 어떻게 되나, access token 이란, authorization server beginner, resource owner, client credentials beginner, oauth2 흐름 쉽게, 위임 인증 개념, third party access, oauth basics route, auth basics route, auth beginner route, security beginner route, security basics route, first-step oauth primer, security readme oauth primer, oauth authorization code next step, return to security README

## 핵심 개념

"구글로 로그인" 버튼을 눌렀을 때 일어나는 일이 OAuth2다. 사용자가 앱에 구글 비밀번호를 알려주는 대신, 구글이 직접 "이 앱이 이 권한을 써도 되나요?"라고 사용자에게 물어보고 짧은 수명의 토큰을 발급한다.

OAuth2의 핵심 아이디어는 **비밀번호 위임 없는 권한 위임**이다. 앱은 비밀번호를 모르면서도 사용자를 대신해 특정 작업을 할 수 있다.

입문자가 헷갈리는 점: OAuth2는 "로그인"이 아니라 "권한 위임"이다. 로그인(신원 확인)은 그 위에 올라타는 OIDC(OpenID Connect)가 추가로 처리한다.

## 한눈에 보기

| 역할 | 설명 | 예시 |
|---|---|---|
| Resource Owner | 자원의 주인 (사용자) | 구글 계정 소유자 |
| Client | 자원에 접근하려는 앱 | 나의 Spring Boot 앱 |
| Authorization Server | 토큰을 발급하는 서버 | 구글 OAuth 서버 |
| Resource Server | 보호된 자원을 가진 서버 | 구글 Calendar API |

## 상세 분해

### Access Token이란

Authorization Server가 Client에게 발급하는 짧은 수명의 증표다. 이 토큰을 들고 Resource Server에 요청하면 사용자 대신 행동할 수 있다. 비밀번호와 달리 토큰은 범위(scope)와 만료 시간이 제한돼 있다.

### Scope란

토큰이 허용하는 권한의 범위다. `scope=calendar.read`면 캘린더 읽기만 할 수 있고, 이메일 삭제는 불가능하다. 사용자는 앱이 요청한 scope 목록을 보고 허가 여부를 결정한다.

### Grant Type이란

Client가 토큰을 얻는 방법이다. 가장 흔한 패턴은 다음 두 가지다.

- **Authorization Code Grant**: 브라우저 기반 앱. 사용자가 직접 Authorization Server에서 로그인하고 Code를 받아 토큰으로 교환한다. 가장 안전한 패턴.
- **Client Credentials Grant**: 서버-서버 통신. 사용자 없이 앱 자체의 자격증명으로 토큰을 얻는다.

### Refresh Token이란

Access Token이 만료됐을 때 재발급 받는 데 쓰는 수명이 긴 토큰이다. 사용자에게 다시 로그인 요청하지 않아도 된다.

## 흔한 오해와 함정

### "OAuth2를 쓰면 로그인 기능이 완성된다"

OAuth2는 권한 위임 프레임워크다. 신원 확인(로그인, "이 사람이 누구인가")은 OIDC가 담당한다. 순수 OAuth2만으로는 "이 토큰이 누구 것인가"를 신뢰할 수 없다.

### "Access Token을 localStorage에 넣으면 된다"

XSS 공격으로 JavaScript가 실행되면 localStorage의 토큰이 탈취된다. Access Token은 `HttpOnly` 쿠키 또는 메모리에만 두는 것이 더 안전하다.

### "Refresh Token은 아무 데나 저장해도 된다"

Refresh Token은 수명이 길어서 탈취되면 장기 피해가 생긴다. 서버 쪽 세션에 저장하거나, 사용 후 폐기(rotation)하는 패턴을 써야 한다.

## 실무에서 쓰는 모습

Spring Boot에서 "구글로 로그인"을 구현할 때 `spring-boot-starter-oauth2-client` 의존성을 추가하고 `application.yml`에 client-id와 client-secret을 설정한다. Spring Security가 Authorization Code Grant 흐름을 자동으로 처리하므로, 개발자가 직접 토큰 교환 코드를 짤 필요가 없다.

사용자가 "구글로 로그인" 버튼을 누르면 앱이 구글 Authorization Server로 리다이렉트하고, 구글이 인증 후 code를 앱에 돌려준다. 앱은 그 code를 access token으로 교환하고 사용자 세션을 만든다.

## 더 깊이 가려면

- 보안 입문 문서 묶음으로 돌아가기: [Security README 기본 primer 묶음](./README.md#기본-primer)
- Authorization Code Grant 상세 흐름: [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- JWT로 Access Token을 표현하는 방법: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)

## 면접/시니어 질문 미리보기

> Q: OAuth2에서 Access Token과 Refresh Token의 차이는 무엇인가요?
> 의도: 토큰 역할 분리를 이해하는지 확인
> 핵심: Access Token은 짧은 수명으로 Resource Server 접근에 쓰고, Refresh Token은 만료된 Access Token을 재발급 받는 데 쓴다. 역할이 다르므로 보관 위치와 보안 수준도 달라야 한다.

> Q: OAuth2의 scope는 무엇이고 왜 필요한가요?
> 의도: 최소 권한 원칙과의 연결을 이해하는지 확인
> 핵심: scope는 토큰이 허용하는 권한 범위다. 앱이 필요한 것만 요청해야 토큰 탈취 시 피해 범위를 줄일 수 있다.

## 한 줄 정리

OAuth2는 비밀번호 공유 없이 제한된 권한을 위임하는 프로토콜이고, Access Token의 scope와 만료 시간이 피해 범위를 제어한다.
