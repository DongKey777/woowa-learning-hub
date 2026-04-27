# HTTPS와 TLS 기초

> 한 줄 요약: HTTPS는 HTTP 위에 TLS를 씌워 전송 구간의 도청과 변조를 막는 것이고, 브라우저 자물쇠 아이콘은 "서버가 신뢰할 수 있는 인증서를 제시했다"는 표시다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
- [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md)
- [네트워크 HTTP 상태·세션·캐시](../network/http-state-session-cache.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: https tls beginner, https가 뭔가요, tls 기초, 자물쇠 아이콘, ssl tls 차이, http vs https, 인증서가 뭔가요, certificate authority beginner, tls handshake 쉽게, 도청 방지, 전송 암호화 입문, https 왜 써야 하나요, security readme https primer, security beginner route, security primer next step

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

- `https tls beginner`의 첫 기준은 정의, 사용 시점, 흔한 오해를 분리해서 읽는 것이다.
- 코드 예시는 바로 아래 섹션에서 보고, 여기서는 판단 기준만 먼저 잡는다.
- 입문 단계에서는 API 이름보다 어떤 문제를 줄이는지부터 확인한다.

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

### SSL과 TLS의 관계

SSL은 TLS의 이전 이름이다. 보안 취약점이 발견돼 SSL은 더 이상 사용하지 않고, 현재는 TLS 1.2 이상이 표준이다. "SSL 인증서"라는 말이 남아 있지만 실제로는 TLS를 쓴다.

## 흔한 오해와 함정

### "HTTPS면 해킹이 불가능하다"

HTTPS는 전송 구간만 보호한다. 서버 내부에서 평문 비밀번호를 저장하거나, SQL 인젝션이 있으면 별도로 뚫린다.

### "자물쇠 아이콘이 있으면 사이트가 안전하다"

자물쇠는 "전송이 암호화됐고 서버가 인증서를 가졌다"는 뜻이지, 그 서버가 악의가 없다는 보증은 아니다. 피싱 사이트도 HTTPS 인증서를 가질 수 있다.

### "개발 환경에서는 HTTP로 해도 된다"

로컬 개발 전용이라면 괜찮지만, 스테이징 이상 환경에서는 HTTPS를 기본으로 하는 것이 좋다. 쿠키의 `Secure` 속성, HSTS 같은 보안 메커니즘이 HTTPS를 전제로 동작한다.

## 실무에서 쓰는 모습

Spring Boot 서버를 배포할 때 HTTPS는 보통 두 가지 방식으로 처리한다.

- **역방향 프록시(Nginx, ALB 등)에서 TLS 종료**: 외부 요청은 HTTPS로 받고, 내부 서버 간은 HTTP로 통신. 가장 흔한 패턴.
- **서버 자체 TLS 처리**: `application.properties`에 keystore를 설정. 개발/소규모 환경에서 사용.

어느 방식이든 외부에서 서버로 오는 구간은 암호화되어야 한다.

## 더 깊이 가려면

- HSTS와 MITM 공격 심화: [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
- 세션·쿠키와의 연관: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)

## 면접/시니어 질문 미리보기

> Q: HTTP와 HTTPS의 차이를 설명해 보세요.
> 의도: TLS가 무엇을 추가하는지 이해하는지 확인
> 핵심: TLS 암호화 계층이 추가되어 기밀성·무결성·서버 신원 확인이 가능해진다.

> Q: 자물쇠 아이콘이 있으면 항상 안전한가요?
> 의도: HTTPS의 범위를 제대로 이해하는지 확인
> 핵심: 전송 구간만 보호한다. 피싱 사이트도 인증서를 가질 수 있다.

## 한 줄 정리

HTTPS는 TLS로 전송 구간의 도청·변조를 막고 서버 신원을 검증하지만, 서버 내부 보안(저장, 인가, 코드 취약점)은 별도로 챙겨야 한다.
