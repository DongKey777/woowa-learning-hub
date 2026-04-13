# 05. 보안: 인증, 세션, 암호화

## 1. 인증 구조

사주다방은 두 가지 인증 식별 방식을 같이 쓴다.

- `Bearer` 세션
- `X-Device-Id` 폴백

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/server/common/auth/RequestAuthResolver.java`

이건 실무적으로 자주 나오는 **다중 인증 경로**다.

## 2. 세션은 왜 DB와 Redis를 같이 쓰나

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/application/AuthSessionQueryService.java`

핵심:

1. Redis에서 먼저 찾음
2. miss면 DB `auth_sessions`에서 복구
3. 다시 Redis cache 복원

이건 CS 관점에서 보면:

- 캐시 계층
- durable storage와 cache의 역할 분리
- cache miss fallback

예시로 설명하기 좋다.

## 3. 토큰은 왜 암호화하나

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/core/src/main/java/com/sajudabang/common/crypto/JavaAesGcmCipher.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/infra/crypto/DefaultAuthTokenCipher.java`

토스 access token / refresh token 같은 민감 정보는 그대로 DB에 넣지 않는다.

왜?

- DB 유출 시 피해 최소화
- 민감정보 직접 저장 회피

### AES-GCM 포인트

- 대칭키 암호화
- confidentiality + integrity 보장

즉 “복호화 가능해야 하는 민감값”에 적합하다.

## 4. mTLS는 뭐고 왜 쓰나

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/shared/infra/toss/JavaTossMtlsHttpClient.java`

mTLS는 **서버만 인증하는 일반 TLS보다 더 강하게, 클라이언트 인증서도 같이 확인하는 방식**이다.

토스 API처럼 민감한 파트너 연동에 쓰인다.

즉:

- HTTPS = 서버 신원 보장
- mTLS = 서버 + 클라이언트 둘 다 신원 보장

## 5. unlink / revoke는 왜 중요하나

로그인 성공만 중요한 게 아니다.

연결 해제 시:

- 저장된 토큰 삭제
- 세션 무효화
- redis cache 정리

이게 제대로 안 되면 보안 사고로 이어질 수 있다.

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/application/AuthUnlinkService.java`

## 6. 면접 답변 예시

**Q. 세션을 왜 Redis와 DB에 같이 저장했나요?**  
A. “Redis는 빠른 조회용 cache이고, DB는 durable store입니다. Redis miss가 나더라도 DB에서 세션을 복구해 로그인 상태를 유지할 수 있도록 설계했습니다.”

**Q. 왜 단순 해시가 아니라 AES-GCM을 썼나요?**  
A. “세션 토큰 자체가 아니라, 외부 서비스 access/refresh token은 나중에 다시 써야 해서 복호화 가능해야 합니다. 그래서 무결성까지 보장하는 AES-GCM이 적합했습니다.”
