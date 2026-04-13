# CSP Nonces / Hashes / Script Policy

> 한 줄 요약: CSP는 XSS를 완전히 막는 장치가 아니라, 브라우저가 허용할 스크립트 실행 경로를 제한하는 정책이다. nonce와 hash는 각각 다른 운영 모델을 가진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)

retrieval-anchor-keywords: CSP, nonce, hash, script-src, strict-dynamic, unsafe-inline, unsafe-eval, XSS mitigation, script policy, inline script, browser policy

---

## 핵심 개념

Content-Security-Policy는 브라우저가 어떤 리소스를 로드하고 실행할지 제한하는 정책이다.  
그중 script policy는 XSS 완화에 가장 직접적이다.

대표적인 방식:

- `nonce`: 응답마다 다른 랜덤 값을 붙여 허용된 inline script만 실행
- `hash`: 특정 inline script의 해시를 허용 목록에 넣음
- `strict-dynamic`: nonce가 있는 script가 추가로 불러오는 script까지 신뢰 범위를 확장

즉 nonce와 hash는 "inline script를 허용할지"를 다르게 다루는 도구다.  
둘 다 좋지만 운영 방식이 다르다.

---

## 깊이 들어가기

### 1. nonce 방식

장점:

- 매 응답마다 다르게 만들 수 있다
- 서버가 렌더링하는 HTML에 잘 맞는다
- 동적으로 주입된 script를 통제하기 쉽다

단점:

- 응답 생성 시점에 nonce를 주입해야 한다
- 캐시와 궁합이 까다롭다
- 템플릿 전 구간에서 nonce 전달이 필요하다

### 2. hash 방식

장점:

- 정적인 inline script에 잘 맞는다
- 캐시 친화적이다
- build-time에 미리 계산할 수 있다

단점:

- script 내용이 조금만 바뀌어도 hash가 달라진다
- 동적인 inline script에는 불리하다
- 빌드 파이프라인과 함께 관리해야 한다

### 3. strict-dynamic은 강하지만 이해를 요구한다

`strict-dynamic`은 nonce/hash가 있는 trusted script가 추가로 로드한 script를 허용한다.

좋은 점:

- loader script를 유연하게 운영할 수 있다
- 서드파티 bootstrap 패턴에 맞는다

위험:

- 잘못 쓰면 신뢰 범위가 생각보다 넓어진다
- 레거시 브라우저 대응이 복잡하다

### 4. unsafe-inline과 unsafe-eval은 마지막 경고다

- `unsafe-inline`: inline script 전반 허용
- `unsafe-eval`: eval류 실행 허용

둘은 편하지만 CSP 방어력을 크게 낮춘다.  
전환기에는 임시로 허용할 수 있어도, 최종 상태로 두면 안 된다.

### 5. CSP는 다른 브라우저 방어와 같이 써야 한다

CSP가 있어도:

- DOM XSS가 완전히 사라지지 않는다
- 의도치 않은 script gadget이 남을 수 있다
- cookie 기반 인증의 CSRF 문제는 별도로 남는다

즉 CSP는 브라우저 방어의 한 층이다.

---

## 실전 시나리오

### 시나리오 1: React/Vue 앱에 inline bootstrap script가 필요함

대응:

- nonce를 발급한다
- HTML 렌더링 시 nonce를 주입한다
- 필요한 script 태그에만 nonce를 붙인다

### 시나리오 2: 레거시 페이지가 정적 inline script를 많이 씀

대응:

- hash 기반 정책으로 점진 전환한다
- script 블록을 줄인다
- build 단계에서 hash를 생성한다

### 시나리오 3: CSP를 넣었는데도 XSS가 난다

대응:

- DOM sink와 template escaping을 다시 본다
- `unsafe-inline` 또는 `unsafe-eval`이 남아 있는지 확인한다
- browser console의 CSP violation report를 수집한다

---

## 코드로 보기

### 1. nonce header 개념

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-abc123'; object-src 'none'
```

### 2. hash header 개념

```http
Content-Security-Policy: script-src 'self' 'sha256-Base64HashValue'
```

### 3. 서버 렌더링 nonce 주입

```java
public String renderPage(HttpServletRequest request) {
    String nonce = cspNonceService.issue(request);
    request.setAttribute("cspNonce", nonce);
    return templateEngine.render("index", Map.of("nonce", nonce));
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| nonce | 동적 페이지에 유연하다 | 템플릿 전파가 필요하다 | SSR, 복합 페이지 |
| hash | 정적 script에 잘 맞는다 | 조금만 바뀌어도 갱신해야 한다 | 정적 bootstrap |
| strict-dynamic | loader 패턴에 강하다 | 이해와 테스트가 필요하다 | 복잡한 프론트 |
| unsafe-inline | 적용이 쉽다 | 방어력이 약하다 | 거의 피해야 함 |

판단 기준은 이렇다.

- 페이지가 동적으로 렌더링되는가
- script가 자주 바뀌는가
- 캐시와 궁합이 중요한가
- inline script를 줄일 수 있는가

---

## 꼬리질문

> Q: nonce와 hash의 차이는 무엇인가요?
> 의도: 동적 허용과 정적 허용의 차이를 아는지 확인
> 핵심: nonce는 응답마다 바뀌고, hash는 고정 script를 허용한다.

> Q: CSP가 있으면 XSS가 완전히 끝나나요?
> 의도: 완화와 근본 제거를 구분하는지 확인
> 핵심: 아니다. XSS 방어의 한 층일 뿐이다.

> Q: unsafe-inline을 왜 피해야 하나요?
> 의도: 정책 약화를 아는지 확인
> 핵심: inline script 전반을 허용해 방어력이 크게 떨어지기 때문이다.

> Q: strict-dynamic은 왜 주의해서 써야 하나요?
> 의도: 신뢰 확장 의미를 아는지 확인
> 핵심: trusted loader가 불러오는 script까지 허용될 수 있기 때문이다.

## 한 줄 정리

CSP의 nonce와 hash는 둘 다 강력하지만, 동적 렌더링과 정적 스크립트라는 운영 조건에 따라 맞는 방식이 다르다.
