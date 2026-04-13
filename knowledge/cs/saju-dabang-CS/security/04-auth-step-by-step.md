# 인증 흐름 단계별 분석

## 로그인

1. 프론트가 authorizationCode 획득
2. 서버가 Toss token 교환
3. 사용자 정보 조회/복호화
4. 사용자 upsert
5. 세션 발급

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/application/AuthLoginService.java`

## 세션 확인

1. `Authorization: Bearer ...`
2. Redis 조회
3. miss면 DB fallback
4. 성공 시 principal 생성

## 로그아웃

1. access token revoke
2. 저장 토큰 삭제
3. 세션 삭제

## unlink

1. 토스 unlink callback 수신
2. 토큰 정리
3. 세션 정리

## 면접 포인트

“로그인 성공만이 아니라 refresh, logout, unlink까지 전체 세션 lifecycle을 설계해야 실제 서비스 보안이 된다.”
