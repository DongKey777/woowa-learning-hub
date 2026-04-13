# 테스트 전략

## 사주다방 테스트의 중심

이 프로젝트는 단순 unit test보다 **통합 테스트 가치**가 크다.

이유:
- DB
- Redis
- queue
- 인증
- 결제
- 복구

가 서로 연결돼 있기 때문

## 실제 테스트 포인트

### 1. auth/session
- Redis miss -> DB fallback
- refresh / logout / unlink

### 2. billing
- purchase
- grant
- reserve -> capture -> refund

### 3. reading
- lookup
- job create
- SSE

### 4. worker
- queue consume
- requeue
- stale processing recovery

## 코드 연결

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/test/java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/test/java`

## 실제 코드 관점

예를 들어 billing reserve/capture/refund 테스트는 이렇게 의미가 있다.

- reserve 후 coins 감소 확인
- capture 후 상태 completed 확인
- refund 후 coins 복구 확인

즉 단순 메서드 반환값이 아니라 **DB 상태 전이까지 같이 본다**.

## 왜 unit test만으로 부족한가

사주다방 문제는 대부분 시스템 경계에서 발생한다.

예:
- DB 정합성
- Redis miss
- queue 복구
- IAP 재시도

이건 mock만으로는 놓치기 쉽다.

## 면접 포인트

“사주다방은 순수 unit test보다 통합 테스트가 더 가치 있는 영역이 많았다. 특히 결제와 queue는 실제 의존성을 같이 확인해야 의미가 있다.”

## 꼬리질문

### Q. 그럼 unit test는 의미가 없나요?

A. 아니다. unit test도 중요하다. 다만 이 프로젝트에선 결제/큐/복구처럼 시스템 경계가 중요한 영역이 많아서 통합 테스트 우선순위가 더 높다.

### Q. 왜 Testcontainers가 좋은가요?

A. PostgreSQL/Redis 같은 실제 의존성을 개발 환경과 비슷하게 띄워서 테스트할 수 있기 때문이다. mock보다 실제에 가까운 회귀를 만들 수 있다.

### Q. 어떤 테스트가 제일 중요한가요?

A. 돈과 데이터 정합성에 직결되는 테스트다. 예를 들면 중복 적립 방지, reserve/capture/refund, stale queue recovery 같은 것들이다.
