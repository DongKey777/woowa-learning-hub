# DNS, HTTPS, mTLS를 사주다방으로 이해하기

## 도메인

- `api-prelaunch.saju-dabang.com`
- `api.saju-dabang.com`

도메인은 사람이 읽는 이름이고, 실제론 DNS가 서버 IP로 연결한다.

## 사주다방 사례

prelaunch 검증 시:
- DNS가 `api-prelaunch.saju-dabang.com`
- 특정 EC2 IP
로 연결됨

즉 프론트는 IP를 몰라도 되고, 도메인만 알면 된다.

## HTTPS

이유:
- 로그인/결제/세션 보호
- 토스 WebView 런타임과 보안 정책 대응

관련 파일:
- `/Users/idonghun/IdeaProjects/saju-dabang/infra/single-box/Caddyfile`

## 실제 코드/구성 스니펫

`Caddyfile`은 외부 HTTPS 요청을 내부 API 컨테이너로 보낸다.

```caddy
{$PRELAUNCH_DOMAIN} {
  encode gzip
  reverse_proxy api:3001
}
```

읽는 포인트:
- 외부에서는 `https://api-prelaunch.saju-dabang.com`
- 내부에서는 `api:3001`
- reverse proxy가 둘 사이를 연결

## mTLS

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/shared/infra/toss/JavaTossMtlsHttpClient.java`

핵심 아이디어는 인증서와 개인키를 직접 로드해서 `SSLContext`를 만드는 것이다.

```java
X509Certificate certificate = loadCertificate(certDir.resolve("saju-dabang-api_public.crt"));
PrivateKey privateKey = loadPrivateKey(certDir.resolve("saju-dabang-api_private.key"));

KeyStore keyStore = KeyStore.getInstance(KeyStore.getDefaultType());
keyStore.load(null, null);
keyStore.setKeyEntry("client", privateKey, new char[0], new java.security.cert.Certificate[]{certificate});
```

## 차이

- HTTPS: 서버 인증
- mTLS: 서버 + 클라이언트 인증

토스 같은 파트너 API는 민감해서 mTLS까지 요구될 수 있다.

## 면접 포인트

“도메인이 뭐냐?”  
- 사람이 읽는 이름
- DNS가 실제 IP에 매핑

“mTLS는 왜 필요했냐?”  
- 토스 파트너 API와 상호 인증을 해야 해서

## 꼬리질문

### Q. IP로 직접 붙으면 안 되나요?

A. 기술적으로는 가능하지만, 환경 교체와 운영이 매우 불편하다. DNS를 쓰면 서버가 바뀌어도 클라이언트는 도메인만 계속 사용할 수 있다.

### Q. HTTPS면 충분한 거 아닌가요?

A. 일반 사용자-facing 통신엔 충분한 경우가 많다. 하지만 파트너 API가 “누가 호출하는지”까지 강하게 확인해야 하면 mTLS가 필요하다.

### Q. reverse proxy는 왜 두나요?

A. TLS 종료, 도메인 처리, gzip, 내부 컨테이너 라우팅을 한 곳에서 정리할 수 있기 때문이다.
