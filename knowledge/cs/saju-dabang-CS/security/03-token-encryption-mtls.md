# 토큰 암호화와 mTLS

## 토큰 암호화

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/infra/crypto/DefaultAuthTokenCipher.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/core/src/main/java/com/sajudabang/common/crypto/JavaAesGcmCipher.java`

이유:
- 민감한 토큰을 평문 저장하지 않기 위해

## mTLS

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/infra/toss/MtlsTossOAuthClient.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/shared/infra/toss/JavaTossMtlsHttpClient.java`

## 차이

- HTTPS: 서버 인증
- mTLS: 서버와 클라이언트 모두 인증

## 면접 포인트

“외부 파트너 API와 통신할 때는 HTTPS만으로 부족할 수 있어서 mTLS가 필요하다.”
