# HTTP와 HTTPS 기초

> 한 줄 요약: HTTP는 평문으로 데이터를 주고받고, HTTPS는 TLS 계층을 추가해 암호화·인증·무결성을 보장한다.

**난이도: 🟢 Beginner**

관련 문서:

- [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
- [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
- [network 카테고리 인덱스](./README.md)
- [CORS 기초](../security/cors-basics.md)

retrieval-anchor-keywords: http https basics, http vs https 차이, https 왜 써야 해요, tls란 뭔가요, ssl tls 입문, 암호화 통신 기초, https 인증서, 평문 암호화 차이, 브라우저 자물쇠 아이콘, beginner https

## 핵심 개념

HTTP(HyperText Transfer Protocol)는 웹에서 클라이언트와 서버가 텍스트, 이미지, JSON 등을 주고받는 규칙이다. 그런데 HTTP는 데이터를 **평문(plaintext)** 으로 전송한다. 같은 네트워크에 있는 누군가가 패킷을 가로채면 내용을 그대로 볼 수 있다. HTTPS는 HTTP에 **TLS(Transport Layer Security)** 계층을 추가해 이 문제를 해결한다.

입문자가 헷갈리는 지점은 HTTPS가 완전히 다른 프로토콜이라고 오해하는 것이다. HTTPS는 HTTP 그대로이고, 그 아래에 TLS라는 암호화 터널이 추가된 구조다.

## 한눈에 보기

| 항목 | HTTP | HTTPS |
|---|---|---|
| 포트 기본값 | 80 | 443 |
| 암호화 | 없음 | TLS |
| 인증서 | 없음 | CA가 서명한 서버 인증서 |
| 데이터 무결성 | 없음 | MAC으로 변조 감지 |
| 속도 오버헤드 | 없음 | TLS handshake 1회 추가 |
| 브라우저 표시 | 경고 또는 없음 | 자물쇠 아이콘 |

## 상세 분해

### TLS가 하는 세 가지 일

- **암호화**: 전송 데이터를 암호화해서 도청해도 내용을 알 수 없다.
- **서버 인증**: 브라우저가 접속하는 서버가 진짜 서버인지 인증서로 확인한다. 피싱 사이트 차단에 도움이 된다.
- **무결성**: 전송 중 데이터가 변조됐는지 감지한다.

### TLS handshake가 언제 일어나나

TCP 3-way handshake가 완료된 직후에 TLS handshake가 추가로 진행된다. 요청 흐름은 이렇다.

```
TCP handshake (SYN / SYN-ACK / ACK)
TLS handshake (인증서 교환, 키 협상)
HTTP 요청/응답
```

TLS handshake는 첫 연결 때만 일어난다. 이후 같은 연결을 재사용하면(keep-alive) handshake 비용은 없다.

### 인증서는 무엇인가

서버가 가진 디지털 문서다. CA(Certificate Authority, 인증 기관)가 "이 도메인의 공개 키가 맞다"고 서명해줬다는 증명이다. 브라우저는 OS나 브라우저에 내장된 CA 목록을 갖고 있어서, 서버 인증서를 받으면 그 CA가 신뢰할 수 있는지 검증한다.

## 흔한 오해와 함정

- "HTTPS는 느리다"는 말은 TLS handshake 때문이지, 연결 이후 데이터 전송 속도가 느린 건 아니다. 커넥션 재사용 시 체감 차이는 거의 없다.
- "HTTP는 개발 환경에서만 괜찮다"는 생각이 있는데, 로컬이라도 쿠키 보안 속성(`Secure`, `HttpOnly`)이나 일부 브라우저 기능이 HTTPS에서만 동작하기 때문에 로컬에서도 HTTPS를 사용하는 편이 점점 권장된다.
- SSL과 TLS를 혼용해서 부르는 경우가 많다. SSL은 구버전이고 현재는 TLS 1.2/1.3을 쓴다. "SSL 인증서"라고 부르는 건 관습이다.

## 실무에서 쓰는 모습

Spring Boot 백엔드 서버를 운영할 때 직접 TLS를 설정하기보다는 앞단에 Nginx나 AWS ALB 같은 로드밸런서를 두고, 거기서 TLS를 종료(TLS termination)한 뒤 내부 서버와는 HTTP로 통신하는 구조가 흔하다. 이 경우 서버 코드에 인증서 설정은 없어도 클라이언트 입장에서는 HTTPS가 된다.

## 더 깊이 가려면

- [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md) — TLS 설정, 인증서 갱신, 프록시에서의 TLS 처리
- [network 카테고리 인덱스](./README.md) — 다음 단계 주제 탐색

## 면접/시니어 질문 미리보기

**Q. HTTP와 HTTPS의 차이를 설명해 주세요.**
HTTP는 데이터를 평문으로 전송하고, HTTPS는 TLS를 추가해 암호화·서버 인증·무결성을 보장한다. 기본 포트는 HTTP가 80, HTTPS가 443이다.

**Q. TLS handshake는 언제 일어나나요?**
TCP 연결이 맺어진 직후, 실제 HTTP 요청이 오가기 전에 일어난다. 인증서 검증과 대칭 키 협상을 여기서 수행한다.

**Q. 인증서가 만료되면 어떻게 되나요?**
브라우저는 경고 화면을 보여주고 사용자가 명시적으로 무시하지 않는 한 접속을 차단한다. 서비스 운영 중에는 인증서 갱신 자동화(예: Let's Encrypt + certbot)를 설정하는 것이 기본이다.

## 한 줄 정리

HTTPS는 HTTP에 TLS를 씌운 것이고, TLS는 암호화·인증·무결성이라는 세 가지 보안 속성을 제공한다.
