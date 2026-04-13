# CSP Report-Only Rollout / Violation Feedback

> 한 줄 요약: CSP는 처음부터 강제하면 깨질 수 있으므로, report-only로 위반을 관찰하고 점진적으로 정책을 강화하는 rollout이 실무적이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CSP Nonces / Hashes / Script Policy](./csp-nonces-vs-hashes-script-policy.md)
> - [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)

retrieval-anchor-keywords: CSP report-only, Content-Security-Policy-Report-Only, violation report, rollout, script-src, frame-ancestors, strict CSP, browser telemetry, policy hardening

---

## 핵심 개념

CSP(Content-Security-Policy)는 브라우저가 어떤 리소스를 허용할지 정하는 정책이다.  
하지만 보안 정책을 한 번에 강제하면 레거시가 깨질 수 있다. 그래서 `report-only`가 중요하다.

`report-only`의 역할:

- 위반을 실제 차단하지 않고 관찰한다
- 어떤 script/style/frame가 문제인지 찾는다
- rollout 전에 깨질 지점을 미리 발견한다

즉 CSP rollout은 "정책을 더한다"가 아니라 "정책을 관찰하며 강화한다"다.

---

## 깊이 들어가기

### 1. report-only의 목적

처음부터 강제하면 다음 문제가 생긴다.

- inline script가 많아 앱이 깨진다
- 서드파티 widget이 작동하지 않는다
- 스타일이나 iframe이 사라진다

report-only는 이런 영향 범위를 먼저 본다.

### 2. violation report는 운영 신호다

브라우저가 위반을 보고하면 다음을 알 수 있다.

- 어떤 page가 위반했는가
- 어떤 directive가 깨졌는가
- 어떤 resource URL이 문제였는가

이 데이터를 모으면 정책을 수축시킬 수 있다.

### 3. rollout은 단계적으로 해야 한다

권장 순서:

1. report-only로 시작
2. 위반 빈도가 높은 경로를 정리
3. `script-src`, `frame-ancestors`, `object-src`부터 강화
4. 일부 페이지에만 enforce
5. 전체 enforce

### 4. report endpoint도 안전해야 한다

violation report는 외부에서 들어오는 입력이다.

- 크기가 클 수 있다
- 빈도가 많을 수 있다
- 스팸성 데이터가 들어올 수 있다

따라서 rate limit과 저장 한도를 둬야 한다.

### 5. 정책이 너무 느슨하면 report-only만 남는다

운영 편의 때문에 영원히 report-only에 머무르면 안 된다.

- 경고만 쌓인다
- 실제 방어는 생기지 않는다

그래서 rollout deadline을 정해야 한다.

---

## 실전 시나리오

### 시나리오 1: 레거시 앱이 inline script를 너무 많이 씀

대응:

- report-only로 위반을 먼저 수집한다
- nonce 또는 hash로 전환한다
- inline script를 줄인다

### 시나리오 2: CSP를 enforce했더니 third-party widget이 깨짐

대응:

- 필요한 host만 allowlist에 넣는다
- widget을 isolated iframe으로 분리한다
- 예외를 최소화한다

### 시나리오 3: violation report가 너무 많이 들어옴

대응:

- report endpoint에 rate limit을 둔다
- 샘플링을 적용한다
- 중복 위반을 집계한다

---

## 코드로 보기

### 1. report-only header

```http
Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self' 'nonce-abc'; report-uri /csp-report
```

### 2. enforce로 전환

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-abc'; object-src 'none'; frame-ancestors 'none'
```

### 3. report 수집 개념

```java
public void handleCspReport(CspReport report) {
    rateLimiter.assertAllowed("csp-report:" + report.page(), 100, Duration.ofMinutes(1));
    cspViolationStore.save(report.sanitized());
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| report-only | 안전하게 관찰한다 | 실제 방어는 안 된다 | 초기 rollout |
| partial enforce | 일부 경로부터 적용 가능 | 정책 일관성이 떨어질 수 있다 | 전환기 |
| full enforce | 방어력이 높다 | 레거시가 깨질 수 있다 | 충분히 정리된 앱 |
| overly loose policy | 쉽다 | 방어력이 약하다 | 피해야 함 |

판단 기준은 이렇다.

- inline script가 얼마나 남아 있는가
- report endpoint를 운영할 수 있는가
- 언제 enforce로 바꿀 것인가
- 위반 데이터를 실제로 정리할 수 있는가

---

## 꼬리질문

> Q: CSP report-only는 왜 필요한가요?
> 의도: 안전한 rollout의 목적을 아는지 확인
> 핵심: 실제 차단 전에 위반과 영향 범위를 관찰하기 위해서다.

> Q: violation report는 무엇을 알려주나요?
> 의도: 관측 신호를 이해하는지 확인
> 핵심: 어떤 directive와 resource가 위반됐는지 보여준다.

> Q: report-only만 계속 두면 안 되는 이유는 무엇인가요?
> 의도: 경고와 방어의 차이를 아는지 확인
> 핵심: 실제 보안 방어가 생기지 않기 때문이다.

> Q: report endpoint도 왜 보호해야 하나요?
> 의도: 브라우저 telemetry도 공격면이라는 점을 아는지 확인
> 핵심: 대량 spam과 abuse가 가능하기 때문이다.

## 한 줄 정리

CSP report-only는 정책을 안전하게 관찰하는 전환 단계이고, 위반 데이터는 최종 enforce를 위한 운영 신호다.
