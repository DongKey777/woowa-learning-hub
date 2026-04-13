# XSS / CSRF / Spring Security

> 한 줄 요약: XSS는 브라우저에서 우리 코드가 실행되는 문제이고, CSRF는 사용자의 인증 상태를 악용해 요청이 보내지는 문제다. 둘은 원인도 방어도 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)

---

## 핵심 개념

`XSS`는 공격자의 스크립트가 피해자 브라우저에서 실행되는 취약점이다.  
`CSRF`는 피해자의 인증 상태를 이용해 의도치 않은 요청을 보내는 취약점이다.

정리하면:

- XSS는 "내 페이지에서 악성 코드가 실행됨"
- CSRF는 "내가 로그인한 상태를 악용한 요청이 날아감"

둘을 헷갈리면 방어가 엇갈린다.

- XSS는 입력/출력 인코딩, CSP, 템플릿 escaping이 중요하다
- CSRF는 토큰, SameSite, Origin 검증, 요청 방식 제한이 중요하다

---

## 깊이 들어가기

### 1. XSS 종류

- Reflected XSS: 요청 파라미터가 바로 응답에 반사된다
- Stored XSS: DB에 저장된 값이 나중에 렌더링된다
- DOM XSS: 프론트엔드에서 unsafe DOM 조작이 일어난다

### 2. XSS 방어

- 출력 시 escape 한다
- HTML/JS/URL 컨텍스트별 escaping을 분리한다
- `Content-Security-Policy`를 적용한다
- `innerHTML` 같은 위험한 API 사용을 줄인다

### 3. CSRF 방어

CSRF는 cookie-based authentication에서 특히 중요하다.  
브라우저가 자동으로 쿠키를 보내기 때문에, 악성 사이트가 사용자의 의사와 무관한 요청을 유도할 수 있다.

Spring Security에서는 보통 다음을 함께 쓴다.

- CSRF token
- SameSite cookie
- Origin/Referer 검증
- 상태 변경 요청은 POST/PUT/DELETE로 제한

### 4. 세션/JWT와의 관계

- 세션 + cookie: CSRF 방어가 중요하다
- JWT를 localStorage에 저장: XSS에 매우 취약하다
- JWT를 cookie에 저장: CSRF 방어가 다시 중요해진다

즉 "JWT니까 CSRF가 필요 없다"는 말은 틀리기 쉽다.  
저장 방식과 전송 방식까지 같이 봐야 한다.

---

## 실전 시나리오

### 시나리오 1: 게시글 제목이 스크립트로 실행됨

원인:

- 서버가 사용자 입력을 escape하지 않았다
- `innerHTML`로 그대로 렌더링했다

결과:

- 세션 탈취
- 관리자 권한 탈취
- 악성 요청 자동 실행

### 시나리오 2: 로그아웃/송금 API가 외부 사이트에서 호출됨

원인:

- cookie 기반 세션인데 CSRF token이 없다
- SameSite 설정이 약하다

결과:

- 사용자가 원하지 않은 상태 변경 요청이 실행된다

### 시나리오 3: JWT를 localStorage에 넣고 XSS에 털림

원인:

- 저장 위치가 JS 접근 가능하다
- CSP가 없고 출력 escaping이 없다

대응:

- 토큰 저장 위치를 재검토한다
- XSS 방어가 먼저다

### 시나리오 4: CORS와 CSRF를 혼동함

CORS는 브라우저가 다른 origin 응답을 읽는 걸 통제한다.  
CSRF는 브라우저가 자동으로 보내는 요청을 악용하는 문제다.  
둘은 다르다.

---

## 코드로 보기

### 1. Spring Security CSRF 기본 설정

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            )
            .headers(headers -> headers
                .contentSecurityPolicy(csp -> csp.policyDirectives("default-src 'self'"))
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .build();
    }
}
```

### 2. 출력 escaping 예시

```java
public String renderTitle(String title) {
    return HtmlUtils.htmlEscape(title);
}
```

### 3. 상태 변경 요청에 CSRF token 전송

```http
POST /account/email
X-CSRF-TOKEN: 2d7c...
Content-Type: application/json

{"email":"user@example.com"}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| CSRF token | 세션 기반 요청 위조를 막는다 | 구현과 전송 처리가 늘어난다 | cookie/session auth |
| SameSite cookie | 브라우저 레벨에서 도움이 된다 | 모든 공격을 막지는 못한다 | 기본 방어 |
| CSP | XSS 피해를 크게 줄인다 | 정책 튜닝이 필요하다 | HTML 렌더링 서비스 |
| localStorage 저장 | 구현이 쉽다 | XSS에 약하다 | 비권장 |
| HttpOnly cookie | JS로 읽을 수 없어 안전하다 | CSRF 대응이 다시 필요하다 | 브라우저 기반 서비스 |

핵심 판단 기준은 이렇다.

- 브라우저가 인증 상태를 어떻게 들고 다니는가
- 출력 컨텍스트가 HTML/JS/URL 중 무엇인가
- 상태 변경 요청이 외부 origin에서 유도될 수 있는가

---

## 꼬리질문

> Q: XSS와 CSRF의 차이를 한 문장으로 설명하면?
> 의도: 두 공격의 원인과 피해 지점을 구분하는지 확인
> 핵심: XSS는 브라우저에서 코드가 실행되는 문제, CSRF는 인증 상태가 악용되는 문제다.

> Q: JWT를 쓴다고 CSRF가 사라지는가?
> 의도: 저장 위치와 전송 방식까지 보고 있는지 확인
> 핵심: cookie에 저장하면 CSRF가 다시 중요해질 수 있다.

> Q: CSP가 있으면 XSS를 완전히 막을 수 있는가?
> 의도: 단일 방어로 끝내는 사고를 경계하는지 확인
> 핵심: CSP는 강력하지만 escaping을 대체하지는 못한다.

## 한 줄 정리

XSS는 출력과 실행을, CSRF는 인증 상태와 요청 위조를 다루는 문제이므로, Spring Security 설정과 브라우저 보안을 함께 잡아야 한다.
