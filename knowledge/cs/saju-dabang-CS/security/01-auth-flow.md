# 인증 흐름

## 사주다방의 인증

- Bearer 세션 우선
- 없으면 `X-Device-Id` 폴백

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/server/common/auth/RequestAuthResolver.java`

## 실제 코드 스니펫

```java
String authorization = headers.getFirst(HttpHeaders.AUTHORIZATION);
if (authorization != null && authorization.startsWith("Bearer ")) {
  String token = authorization.substring(7);
  Optional<StoredSession> session = authSessionQueryService.resolve(token);
  if (session.isPresent()) {
    return new AuthenticatedPrincipal(session.get().userId(), AuthenticatedPrincipal.AuthKind.BEARER);
  }
}

String deviceId = headers.getFirst("X-Device-Id");
if (deviceId == null || deviceId.length() < 10) {
  throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "authentication required");
}
```

이 코드가 의미하는 것:

1. 로그인 세션이 있으면 Bearer 우선
2. 없으면 device 기반 식별로 폴백
3. 완전 무인증 상태는 막음

## 왜 이렇게 했나

- 로그인 유저와 비로그인 유저 둘 다 처리해야 해서
- 점진적 인증 경험을 만들기 위해

## 장점

- 초반 진입 장벽이 낮음
- 완전 로그인 강제가 아님
- 동시에 로그인 사용자에겐 더 강한 식별 제공

## 단점

- 인증 흐름이 단일 세션 방식보다 복잡
- 정책을 잘못 잡으면 경계가 흐려질 수 있음

## 면접 포인트

“완전 로그인 필수 구조 대신, 서비스 특성상 device fallback과 bearer session을 함께 썼다.”

## 꼬리질문

### Q. deviceId는 인증이라고 볼 수 있나요?

A. 엄밀히 말하면 강한 사용자 인증보다는 식별에 가깝다. 그래서 결제나 실제 토스 계정 연동이 필요한 작업은 Bearer/Toss 세션 쪽을 더 신뢰해야 한다.

### Q. 왜 처음부터 로그인 강제를 하지 않았나요?

A. 서비스 UX 특성상 초기 탐색 경험이 중요했기 때문이다. 다만 결제나 강한 사용자 귀속이 필요한 작업은 로그인으로 승격된다.

### Q. 이 방식의 보안 리스크는?

A. deviceId만으로는 계정 수준 보안을 제공하지 못한다. 그래서 민감 작업은 Bearer/Toss 계정을 기준으로 검증해야 한다.
