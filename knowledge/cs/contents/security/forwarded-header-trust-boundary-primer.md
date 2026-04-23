# Forwarded Header Trust Boundary Primer

> 한 줄 요약: `X-Forwarded-*` 헤더는 클라이언트가 아니라 신뢰한 proxy가 남긴 메모일 때만 의미가 있으며, 아무 요청에서나 믿으면 scheme 판단과 client identity 판단이 공격자 입력으로 바뀐다.

**난이도: 🟢 Beginner**

관련 문서:

- [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
- [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)
- [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md)
- [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)
- [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](../network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
- [Proxy Header Normalization Chain / Trust Boundary](../network/proxy-header-normalization-chain-trust-boundary.md)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: forwarded header trust boundary, x-forwarded-proto spoofing, x-forwarded-for spoofing, trusted proxy only, proxy header beginner, forwarded header basics, client ip wrong behind proxy, redirect becomes http, secure cookie proxy mismatch, X-Forwarded-Host redirect, host preservation load balancer, post-login redirect wrong origin, oauth callback wrong origin, rate limit ip spoofing, internal ip allowlist bypass, why trust forwarded headers, forwarded header 헷갈림

## 핵심 개념

가장 단순한 모델은 "proxy가 앱에게 남기는 메모"다.

사용자는 `https://app.example.com`으로 들어왔지만, TLS가 load balancer에서 끝나면 앱은 내부 HTTP 요청만 볼 수 있다. 이때 proxy는 `X-Forwarded-Proto: https`처럼 "원래 바깥 요청은 HTTPS였다"는 메모를 붙인다. 또 `X-Forwarded-For`로 "원래 client IP는 이것이다"라는 메모도 남긴다.

문제는 이 메모를 **클라이언트도 직접 써서 보낼 수 있다**는 점이다. 그래서 앱은 "헤더가 있다"가 아니라 "내가 아는 proxy가 쓴 헤더인가"를 먼저 확인해야 한다.

## 한눈에 보기

| 헤더 | 앱이 보통 결정하는 것 | 아무나 쓴 값을 믿으면 |
|---|---|---|
| `X-Forwarded-Proto` | 원래 요청 scheme, HTTPS 여부, redirect URL, secure cookie 판단 | HTTP 요청을 HTTPS로 착각하거나, 반대로 HTTPS 흐름이 HTTP redirect로 꺾인다 |
| `X-Forwarded-For` | client IP, rate limit key, audit log, IP allowlist | 공격자가 IP를 바꿔 rate limit을 피하거나 내부망 요청처럼 보이게 만든다 |
| `X-Forwarded-Host` | 외부 host, absolute URL, callback/reset link | 엉뚱한 host로 링크가 만들어지거나 host 기반 정책이 흐려진다 |
| `Forwarded` | 위 정보를 표준 문법으로 묶은 값 | 표준 헤더여도 출처가 불명확하면 여전히 spoofing 입력이다 |

기억할 순서는 하나다.

1. 요청이 어느 peer에서 왔는지 본다.
2. 그 peer가 known proxy인지 확인한다.
3. known proxy가 아니면 `X-Forwarded-*`를 신뢰하지 않는다.

## 상세 분해

### 1. 왜 forwarded header가 필요한가

proxy/LB/ingress가 앞에 있으면 앱이 직접 보는 peer는 사용자가 아니라 proxy다. 따라서 앱은 외부 URL을 만들거나 client IP를 기록하려면 proxy가 전달한 보조 정보가 필요하다.

### 2. "trusted proxy"는 헤더 이름이 아니라 출처다

`X-Forwarded-Proto`라는 이름 자체가 안전한 것은 아니다. 안전한 조건은 "이 요청의 바로 앞 hop이 내가 운영하는 LB, ingress, gateway, reverse proxy인가"다. 보통 IP 대역, private network, mTLS, mesh identity 같은 방식으로 확인한다.

### 3. scheme 판단이 속으면 login과 redirect가 흔들린다

앱이 `X-Forwarded-Proto: https`를 무조건 믿으면 direct HTTP 요청도 secure한 요청처럼 취급될 수 있다. 반대로 proxy가 attacker-supplied `X-Forwarded-Proto: http`를 지우지 않고 넘기면 앱이 `http://...` redirect를 만들고 `Secure` cookie가 다음 요청에 빠질 수 있다.

### 4. client identity 판단이 속으면 보안 정책이 흔들린다

`X-Forwarded-For` 첫 값을 무조건 client IP로 쓰면 공격자는 요청마다 다른 IP를 써서 rate limit을 피할 수 있다. `127.0.0.1`, `10.0.0.5` 같은 값을 넣어 내부 요청처럼 보이게 만들 수도 있다. 그래서 IP allowlist, audit log, abuse throttling에는 반드시 trusted chain 해석이 필요하다.

## 흔한 오해와 함정

- "`X-Forwarded-*`가 있으면 proxy가 붙인 것이다"가 아니다. 인터넷 client도 같은 이름의 헤더를 직접 보낼 수 있다.
- "우리 서비스는 LB 뒤에 있으니 무조건 안전하다"가 아니다. 앱이 direct로 노출된 route, debug port, 잘못 열린 ingress가 있으면 그 경로에서는 헤더가 외부 입력이다.
- "`X-Forwarded-For`의 첫 번째 값이 진짜 client IP다"가 아니다. trusted proxy chain을 정리한 뒤에야 어느 값을 client로 볼지 정할 수 있다.
- "이건 네트워크 설정 문제라 앱 보안과 무관하다"가 아니다. redirect, cookie, rate limit, audit, IP allowlist가 모두 앱의 보안 결정으로 이어진다.

## 실무에서 쓰는 모습

### 안전한 흐름

```text
Client -> Trusted LB -> App

LB:
  외부에서 들어온 X-Forwarded-* 제거
  X-Forwarded-Proto: https 재작성
  X-Forwarded-For: <observed client ip> 누적

App:
  remote peer가 trusted lb인지 확인
  맞으면 forwarded header 해석
  아니면 remote peer 정보만 사용
```

이 구조에서는 클라이언트가 가짜 `X-Forwarded-For`를 넣어도 LB가 지우거나 덮어쓴다. 앱도 LB에서 온 요청일 때만 헤더를 믿는다.

### 위험한 흐름

```http
GET /admin HTTP/1.1
Host: app.example.com
X-Forwarded-For: 127.0.0.1
X-Forwarded-Proto: https
```

앱이 이 값을 그대로 믿으면 외부 요청이 내부 IP와 HTTPS 요청처럼 보일 수 있다. 결과적으로 admin IP allowlist, HTTPS-only redirect, rate limit, audit log가 모두 공격자가 쓴 문자열에 의존하게 된다.

## 더 깊이 가려면

proxy 뒤 login loop와 `Secure` cookie 문제가 먼저 보이면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)를 이어서 읽는다. client IP chain, `Forwarded` 표준 문법, `X-Real-IP`까지 내려가야 하면 [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](../network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)가 다음 단계다.

login 직후 `Location`이나 OAuth `redirect_uri`가 `app-internal`, `localhost`, staging host처럼 wrong origin으로 만들어지면 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)에서 `X-Forwarded-Host`, host preservation, public base URL을 먼저 분리한다.

gateway가 인증한 user/tenant 정보를 `X-Authenticated-User` 같은 내부 header로 넘기는 설계는 [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md)로 넘어간다. 핵심은 다르지 않다. header 값보다 **누가 그 header를 썼는지**가 먼저다.

## 면접/시니어 질문 미리보기

> Q: `X-Forwarded-Proto`를 믿어도 되는 조건은 무엇인가요?
> 핵심: 요청이 known proxy에서 왔고, 그 proxy가 외부 입력을 strip/overwrite한 뒤 쓴 값일 때만 믿는다.

> Q: `X-Forwarded-For` 첫 값을 그대로 rate limit key로 쓰면 왜 위험한가요?
> 핵심: 클라이언트가 첫 값을 조작할 수 있어 IP를 마음대로 바꾸거나 내부망 IP처럼 보이게 만들 수 있다.

> Q: framework에서 `trust proxy` 옵션을 켜면 끝인가요?
> 핵심: 아니다. 어떤 proxy/range를 신뢰할지, direct exposure가 없는지, edge가 헤더를 재작성하는지까지 같이 맞춰야 한다.

## 한 줄 정리

`X-Forwarded-*`는 "요청자가 주장한 사실"이 아니라 "known proxy가 관찰해 다시 쓴 사실"일 때만 scheme과 client identity 판단에 써야 한다.
