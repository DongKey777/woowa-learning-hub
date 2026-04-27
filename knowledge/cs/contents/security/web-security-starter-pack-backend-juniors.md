# 백엔드 주니어를 위한 웹 보안 스타터 팩

> 한 줄 요약: Spring Security 설정으로 바로 들어가기 전에, 웹 보안은 "전송 구간, 비밀번호 저장, 브라우저 실행, 브라우저 자동 전송, 출처 간 읽기, 시크릿 주입" 여섯 질문으로 먼저 나누면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [HTTPS와 TLS 기초](./https-tls-beginner.md)
- [비밀번호 저장 기초: 왜 해시를 써야 하나](./password-hashing-basics.md)
- [XSS와 CSRF 기초](./xss-csrf-basics.md)
- [CORS 기초](./cors-basics.md)
- [시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유](./secrets-management-basics.md)
- [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- [[survey] Security README: 기본 primer](./README.md#기본-primer)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)

retrieval-anchor-keywords: web security starter pack, backend junior web security, beginner web security route, spring security before deep dive, https password hashing xss csrf cors secrets primer, 웹 보안 스타터 팩, 백엔드 주니어 보안 입문, 스프링 시큐리티 전에 뭐부터, https 비밀번호 해시 csrf xss cors 시크릿, secret config handling beginner, woowacourse backend security starter, security primer bundle, return to security readme, 뭘 먼저 공부해야 하나, 보안 공부를 시작할 때

## 이 문서 다음에 보면 좋은 문서

- `[return]` security 전체 beginner primer 묶음으로 돌아가고 싶으면 [[survey] Security README: 기본 primer](./README.md#기본-primer)으로 간다.
- `[next step]` "로그인 상태가 어떻게 유지되는지"부터 약하면 [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)를 먼저 붙인 뒤 이 문서를 다시 본다.
- `[next step]` Spring Security 설정이나 필터 체인으로 바로 내려가야 한다면, 이 문서의 체크리스트를 확인한 뒤 [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)로 넘어간다.

## 먼저 잡을 mental model

웹 보안은 용어를 외우기 전에 "요청 한 번에서 무엇을 지키는가"로 자르는 편이 쉽다.

| 질문 | 지키는 대상 | 여기서 먼저 보는 주제 |
|---|---|---|
| 요청이 가는 길에서 누가 훔쳐보거나 바꿀 수 있나? | 전송 구간 | HTTPS |
| DB가 유출되면 사용자 비밀번호가 바로 드러나나? | 저장된 인증 정보 | 비밀번호 해싱 |
| 내 페이지에서 공격자 스크립트가 실행될 수 있나? | 브라우저 실행 맥락 | XSS |
| 로그인된 브라우저가 내 의사와 무관하게 상태 변경 요청을 보낼 수 있나? | 브라우저 자동 전송 | CSRF |
| 다른 origin의 프론트엔드가 우리 응답을 읽어도 되나? | 브라우저 출처 경계 | CORS |
| DB 비밀번호, API 키, JWT signing key가 코드나 Git에 남아 있나? | 서버 설정과 시크릿 | secret/config handling |

핵심은 이 여섯 개가 전부 다른 실패라는 점이다. Spring Security는 이 중 일부를 구현하는 도구일 뿐이고, 문제를 먼저 구분하지 못하면 설정만 바꿔도 원인을 놓친다.

## 한 장으로 보는 starter pack

| 주제 | 가장 먼저 떠올릴 질문 | 주니어가 자주 하는 실수 | 먼저 읽을 문서 |
|---|---|---|---|
| HTTPS | 요청 길목에서 누가 내용을 읽거나 바꿀 수 있나? | "HTTPS면 보안 끝"이라고 생각함 | [HTTPS와 TLS 기초](./https-tls-beginner.md) |
| 비밀번호 해싱 | DB 유출 시 원문 비밀번호가 바로 복구되나? | SHA-256이면 충분하다고 생각함 | [비밀번호 저장 기초: 왜 해시를 써야 하나](./password-hashing-basics.md) |
| XSS | 화면에 나온 사용자 입력이 브라우저에서 코드로 실행되나? | 입력 검증만 하면 끝이라고 생각함 | [XSS와 CSRF 기초](./xss-csrf-basics.md) |
| CSRF | 브라우저가 쿠키를 자동으로 보내는가? | CORS와 같은 문제라고 생각함 | [XSS와 CSRF 기초](./xss-csrf-basics.md) |
| CORS | 브라우저가 응답을 JS에 넘겨도 되는가? | Postman에서 되니 서버 문제 아니라고 생각함 | [CORS 기초](./cors-basics.md) |
| secret/config | 민감한 값이 코드, `application.yml`, Git 히스토리에 남아 있나? | `.env`나 properties 파일을 커밋함 | [시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유](./secrets-management-basics.md) |

## 주니어용 읽기 순서

1. [HTTPS와 TLS 기초](./https-tls-beginner.md)
   전송 구간 보안을 먼저 잡아야 `Secure` 쿠키, proxy 뒤 HTTPS 인식, 로그인 흐름 문제를 읽을 수 있다.
2. [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
   브라우저가 무엇을 자동 전송하는지 알아야 CSRF와 CORS를 헷갈리지 않는다.
3. [비밀번호 저장 기초: 왜 해시를 써야 하나](./password-hashing-basics.md)
   로그인 기능을 만들기 전에 "저장"의 기준을 먼저 맞춘다.
4. [XSS와 CSRF 기초](./xss-csrf-basics.md)
   브라우저 안에서 생기는 두 문제를 분리한다.
5. [CORS 기초](./cors-basics.md)
   cross-origin 요청에서 막히는 지점이 브라우저 읽기 제한인지, 인증 실패인지 분리한다.
6. [시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유](./secrets-management-basics.md)
   운영 전에 코드 밖 주입 원칙을 잡는다.

이 순서가 끝나면 Spring Security 문서는 "무슨 기능이 있는가"보다 "어떤 문제를 막기 위해 켜는가" 기준으로 읽을 수 있다.

## 자주 섞이는 말 먼저 분리

- **HTTPS != 비밀번호 저장**: HTTPS는 전송 중 보호이고, 비밀번호 해싱은 저장 후 유출 대비다.
- **XSS != CSRF**: XSS는 브라우저에서 코드가 실행되는 문제이고, CSRF는 브라우저가 쿠키를 자동 전송하는 문제다.
- **CSRF != CORS**: CSRF는 요청이 보내지는 것 자체가 문제이고, CORS는 응답을 자바스크립트가 읽을 수 있느냐의 문제다.
- **CORS != 인가**: `Access-Control-Allow-Origin`을 맞춰도 서버 인가 규칙이 열리는 것은 아니다.
- **config != secret**: 포트, 타임아웃, feature flag는 일반 설정이고, DB 비밀번호, API 키, signing key는 secret이다.
- **Spring Security != 웹 보안 전체**: 필터와 헤더를 잘 켜도, 비밀번호를 평문 저장하거나 시크릿을 Git에 올리면 이미 실패다.

## 작은 예시로 연결하기

Spring Boot로 회원가입과 게시판을 만든다고 가정하면, 보안 질문은 이렇게 나뉜다.

| 장면 | 먼저 챙길 것 | 왜 필요한가 |
|---|---|---|
| 회원가입에서 비밀번호 저장 | bcrypt 같은 느린 해시 | DB 유출 시 원문 비밀번호 노출 방지 |
| 로그인 후 세션 쿠키 발급 | HTTPS + `Secure`/`HttpOnly`/`SameSite` | 전송 중 노출과 브라우저 측 오용을 줄이기 위해 |
| 게시글/댓글 렌더링 | 출력 이스케이프 | 사용자 입력이 `<script>`로 실행되지 않게 하기 위해 |
| 프로필 수정, 결제, 삭제 요청 | CSRF 토큰 또는 적절한 쿠키 전략 | 로그인된 브라우저의 자동 요청 악용 방지 |
| `localhost:3000` 프론트가 `localhost:8080` API 호출 | CORS 허용 origin 설정 | 브라우저가 응답을 JS에 넘기게 하기 위해 |
| `application.yml` 설정 | `${DB_PASSWORD}` 같은 placeholder | 시크릿이 코드와 Git에 남지 않게 하기 위해 |

## Spring Security deep dive로 넘어가도 되는 기준

아래 질문에 답할 수 있으면 Spring Security deep dive를 읽어도 덜 흔들린다.

- 왜 HTTPS를 켜도 XSS나 CSRF가 저절로 해결되지는 않는지 설명할 수 있다.
- 왜 비밀번호를 AES로 "암호화"해서 저장하는 것보다 bcrypt 같은 느린 해시가 맞는지 설명할 수 있다.
- 세션 쿠키 기반 인증에서 CSRF가 왜 중요한지 말할 수 있다.
- CORS 에러가 브라우저에서만 보이고 Postman에서는 재현되지 않는 이유를 안다.
- `.env`, `application.yml`, GitHub Actions secrets 중 무엇이 커밋 가능한 설정이고 무엇이 시크릿인지 구분할 수 있다.
- Spring Security 설정은 "문제 정의 후 구현"이라는 점을 이해하고 있다.

## 다음 handoff

- 브라우저 공격과 Spring Security 필터/헤더의 연결: [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- cookie와 login 흐름 자체가 헷갈리면: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- security primer 전체 맵으로 다시 돌아가려면: [Security README 기본 primer 묶음](./README.md#기본-primer)

## 한 줄 정리

웹 보안 입문은 "HTTPS, 해싱, XSS, CSRF, CORS, secret/config"을 각각 다른 질문으로 분리하는 데서 시작하고, 그다음에야 Spring Security 설정이 왜 필요한지 보인다.
