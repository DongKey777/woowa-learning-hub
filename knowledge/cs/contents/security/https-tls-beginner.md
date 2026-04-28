# HTTPS와 TLS 기초

> 한 줄 요약: HTTPS는 HTTP 요청을 "봉투 없이 보내는 메모"에서 "봉인된 봉투에 넣어 보내는 메모"로 바꾸는 것이고, TLS는 그 봉투를 잠그고 서버 신원을 확인하는 규칙이다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
- [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md)
- [네트워크 HTTP 상태·세션·캐시](../network/http-state-session-cache.md)
- [브라우저의 쿠키·세션·JWT 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md)
- [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](../network/http1-http2-http3-beginner-comparison.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: https tls beginner, https가 뭔가요, tls 기초, 자물쇠 아이콘, ssl tls 차이, http vs https, 인증서가 뭔가요, certificate authority beginner, tls handshake 쉽게, 도청 방지, 전송 암호화 입문, https 왜 써야 하나요, 처음 https 뭐예요, 브라우저에서 왜 자물쇠가 보여요, secure cookie 왜 안 붙어요 basics

## 왜 이 문서가 필요한가

처음 HTTPS를 배울 때 자주 섞이는 질문은 비슷하다.

- "HTTPS가 그냥 HTTP 빠른 버전인가요?"
- "TLS랑 SSL이랑 뭐가 다른가요?"
- "자물쇠 아이콘이 있으면 사이트가 완전히 안전한 건가요?"
- "로그인은 되는데 `Secure` 쿠키가 왜 HTTP에서는 안 붙나요?"

입문자는 용어를 외우기 전에 먼저 **무슨 문제를 막으려고 HTTPS를 쓰는지**를 잡아야 한다.
핵심은 "HTTP 메시지를 그냥 흘려보내지 않고, 신원을 확인한 뒤 암호화해서 보낸다"는 한 줄이다.

## 먼저 잡는 멘탈 모델

HTTPS를 택배에 비유하면 이해가 쉽다.

- HTTP: 내용이 그대로 보이는 투명 봉투
- HTTPS: 누가 열어보면 티가 나는 봉인 봉투
- TLS: 봉투를 잠그는 규칙 + "이 주소가 진짜 목적지인지" 확인하는 절차

그래서 HTTPS의 초점은 "웹이 더 고급스럽다"가 아니라 **전송 중 도청, 변조, 서버 사칭을 줄이는 것**이다.

## 이 문서 다음에 보면 좋은 문서

- security 입문 문서 안에서 다른 primer를 다시 고르고 싶으면 [Security README 기본 primer 묶음](./README.md#기본-primer)으로 돌아가면 된다.
- `Secure` 쿠키, proxy/LB 뒤 HTTPS 인식, login 직후 cookie 누락처럼 "TLS는 맞는 것 같은데 브라우저 보안 속성이 꼬인다"는 증상으로 이어지면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)를 보면 된다.
- HSTS, 인증서 검증 체인, MITM 방어를 한 단계 더 깊게 보려면 [HTTPS / HSTS / MITM](./https-hsts-mitm.md)로 이어 가면 된다.

## 핵심 개념

HTTP는 데이터를 텍스트 그대로 전송한다. 중간에 누군가 네트워크를 감청하면 요청·응답 내용을 그대로 볼 수 있다. HTTPS는 HTTP에 **TLS(Transport Layer Security)** 계층을 추가해서 이 문제를 해결한다.

TLS가 보장하는 것은 세 가지다.

- **기밀성**: 전송 중 데이터가 암호화된다.
- **무결성**: 전송 중 데이터가 바뀌면 감지된다.
- **서버 신원 확인**: 브라우저가 "이 서버가 진짜 example.com인지" 확인한다.

## 한눈에 보기

- 질문이 "무엇을 보호하나?"면 HTTPS/TLS의 역할을 본다.
- 질문이 "왜 쿠키가 안 붙지?"면 HTTPS 여부와 `Secure` 속성을 함께 본다.
- 질문이 "왜 자물쇠가 떠도 피싱일 수 있지?"면 서버 신원 확인의 범위를 본다.
- 입문 단계에서는 프로토콜 세부 숫자보다 **어떤 위험을 줄이는지**부터 잡는 편이 덜 헷갈린다.

## 코드로 보는 예시

```
클라이언트                  서버
   |--- ClientHello -------->|   (TLS 핸드셰이크 시작)
   |<-- ServerHello + 인증서--|   (서버가 인증서 전달)
   |--- (인증서 검증) -------->|   (클라이언트가 CA 서명 확인)
   |--- 세션키 교환 ---------->|
   |<-- 세션키 교환 ----------|
   |=== 암호화된 HTTP 통신 ===|   (HTTPS 통신 시작)
```

이 과정을 **TLS 핸드셰이크**라고 한다. 핸드셰이크가 끝나면 세션키로 암호화된 HTTP 메시지를 주고받는다.

브라우저에서 `https://bank.example.com/login`으로 접속하는 장면을 떠올리면 된다.

1. 브라우저가 "암호화 통신 가능?"을 묻는다.
2. 서버가 인증서를 보여 주며 "내가 `bank.example.com`이 맞다"고 증명한다.
3. 브라우저가 이를 검증하면, 그 뒤 로그인 ID/비밀번호를 암호화해서 보낸다.

즉 로그인 폼 자체보다 먼저, **안전한 통로를 만드는 절차**가 선행된다.

## 상세 분해

### 인증서란 무엇인가

인증서는 "이 도메인의 공개키가 맞다"는 제3자의 보증서다. 이 제3자를 **CA(인증 기관, Certificate Authority)**라고 한다. 브라우저에는 신뢰할 수 있는 CA 목록이 내장되어 있어서, 서버가 제출한 인증서가 신뢰된 CA가 서명한 것이면 자물쇠 아이콘을 보여 준다.

### HTTP와 HTTPS의 차이

| 항목 | HTTP | HTTPS |
|---|---|---|
| 전송 방식 | 평문 | TLS 암호화 |
| 포트 | 80 | 443 |
| 도청 가능? | 가능 | 불가 (세션키 없이는) |
| 변조 감지? | 불가 | 가능 |
| 서버 신원 확인? | 불가 | 인증서로 확인 |

처음 읽을 때는 이 표를 이렇게 번역하면 된다.

- HTTP는 "내용이 보여도 괜찮다"는 가정이 깔린다.
- HTTPS는 "내용이 보이면 안 된다"는 가정이 깔린다.
- 그래서 로그인, 결제, 세션 쿠키 같은 민감 정보는 HTTPS가 기본이다.

### SSL과 TLS의 관계

SSL은 TLS의 이전 이름이다. 보안 취약점이 발견돼 SSL은 더 이상 사용하지 않고, 현재는 TLS 1.2 이상이 표준이다. "SSL 인증서"라는 말이 남아 있지만 실제로는 TLS를 쓴다.

## 흔한 오해와 함정

### "HTTPS면 해킹이 불가능하다"

HTTPS는 전송 구간만 보호한다. 서버 내부에서 평문 비밀번호를 저장하거나, SQL 인젝션이 있으면 별도로 뚫린다.

### "자물쇠 아이콘이 있으면 사이트가 안전하다"

자물쇠는 "전송이 암호화됐고 서버가 인증서를 가졌다"는 뜻이지, 그 서버가 악의가 없다는 보증은 아니다. 피싱 사이트도 HTTPS 인증서를 가질 수 있다.

### "개발 환경에서는 HTTP로 해도 된다"

로컬 개발 전용이라면 괜찮지만, 스테이징 이상 환경에서는 HTTPS를 기본으로 하는 것이 좋다. 쿠키의 `Secure` 속성, HSTS 같은 보안 메커니즘이 HTTPS를 전제로 동작한다.

## 처음 헷갈릴 때 보는 빠른 판단표

| 지금 든 질문 | 먼저 떠올릴 답 |
|---|---|
| "HTTPS가 왜 필요한가요?" | 중간 도청, 변조, 서버 사칭을 줄이기 위해 |
| "TLS가 뭐예요?" | HTTPS를 가능하게 하는 암호화/인증 규칙 |
| "SSL이랑 같은 말인가요?" | 지금은 거의 TLS를 뜻하지만, SSL은 옛 이름 |
| "자물쇠면 100% 안전한가요?" | 전송은 보호되지만 사이트 자체의 악성 여부까지 보증하진 않음 |
| "왜 `Secure` 쿠키가 안 붙죠?" | HTTPS가 아니거나, 프록시 뒤에서 HTTPS 인식이 어긋났을 수 있음 |

## 실무에서 쓰는 모습

Spring Boot 서버를 배포할 때 HTTPS는 보통 두 가지 방식으로 처리한다.

- **역방향 프록시(Nginx, ALB 등)에서 TLS 종료**: 외부 요청은 HTTPS로 받고, 내부 서버 간은 HTTP로 통신. 가장 흔한 패턴.
- **서버 자체 TLS 처리**: `application.properties`에 keystore를 설정. 개발/소규모 환경에서 사용.

어느 방식이든 외부에서 서버로 오는 구간은 암호화되어야 한다.

## 더 깊이 가려면

- HSTS와 MITM 공격 심화: [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
- 세션·쿠키와의 연관: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- 브라우저에서 쿠키가 어떻게 오가나를 흐름으로 보고 싶다면: [브라우저의 쿠키·세션·JWT 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md)
- TLS 위에서 HTTP 버전이 어떻게 달라지는지 보고 싶다면: [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](../network/http1-http2-http3-beginner-comparison.md)

## 면접/시니어 질문 미리보기

> Q: HTTP와 HTTPS의 차이를 설명해 보세요.
> 의도: TLS가 무엇을 추가하는지 이해하는지 확인
> 핵심: TLS 암호화 계층이 추가되어 기밀성·무결성·서버 신원 확인이 가능해진다.

> Q: 자물쇠 아이콘이 있으면 항상 안전한가요?
> 의도: HTTPS의 범위를 제대로 이해하는지 확인
> 핵심: 전송 구간만 보호한다. 피싱 사이트도 인증서를 가질 수 있다.

## 한 줄 정리

HTTPS는 TLS로 전송 구간의 도청·변조를 막고 서버 신원을 검증하지만, 서버 내부 보안(저장, 인가, 코드 취약점)은 별도로 챙겨야 한다.
