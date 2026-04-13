# 07. 면접 질문 모음

## 네트워크

### Q1. 사주다방에서 SSE를 왜 사용했나요?
- 운세 생성은 몇 초 이상 걸릴 수 있음
- 중간 진행 상황과 부분 결과를 서버가 푸시해야 함
- 단방향 서버 -> 클라이언트 스트림이면 충분했기 때문에 WebSocket보다 SSE가 적합

### Q2. `api-prelaunch.saju-dabang.com`은 무엇인가요?
- prelaunch 검증용 API 도메인
- DNS(Route53)가 실제 EC2 서버 IP에 연결
- production과 검증 환경을 분리하기 위한 주소

## 데이터베이스

### Q3. 트랜잭션이 왜 중요한가요?
- 결제/코인 적립은 거래 기록, 잔액 변경, 주문 상태, ledger 기록이 함께 반영돼야 함
- 일부만 성공하면 데이터가 깨짐
- 그래서 트랜잭션 경계가 중요

### Q4. 멱등성은 어떻게 보장했나요?
- `orderId`
- `idempotency_key`
- 중복 요청이 와도 한 번만 적립되도록 설계

## 운영체제 / 동시성

### Q5. 왜 worker를 별도 프로세스로 분리했나요?
- 긴 작업이 API 응답을 막지 않게 하기 위해
- producer-consumer 구조로 비동기 처리하기 위해

### Q6. reliable queue가 뭐고 왜 필요한가요?
- worker가 중간에 죽어도 작업이 유실되지 않게
- processing queue, lease, ack/requeue로 복구 가능하게 함

## 보안

### Q7. 세션을 Redis와 DB에 같이 저장한 이유는?
- Redis는 빠른 조회용
- DB는 durable store
- Redis miss 시에도 세션 복구 가능

### Q8. 왜 AES-GCM을 썼나요?
- access/refresh token은 나중에 다시 써야 해서 복호화 가능해야 함
- 무결성까지 함께 보장하는 방식이 필요했음

### Q9. mTLS는 왜 필요했나요?
- 토스 같은 민감한 파트너 API는 서버뿐 아니라 클라이언트 인증서도 확인
- 일반 HTTPS보다 더 강한 신뢰 모델

## 소프트웨어 공학

### Q10. Java로 옮기면서 제일 중요했던 설계 원칙은?
- 책임 분리
- 트랜잭션 경계 명확화
- reading과 billing 사이를 port로 연결
- 레거시 Node는 archive로 보존

## 마지막 정리

사주다방으로 CS를 공부할 때 제일 중요한 건:

**개념만 외우지 말고, 반드시 코드 파일과 같이 보기**

예:

- HTTP/SSE -> `ReadingEventController`
- 트랜잭션 -> `BillingJdbcRepository`
- queue -> `RedisReliableQueue`
- 인증/세션 -> `RequestAuthResolver`, `AuthSessionQueryService`
- 설계 -> `BillingPort`, application service

이렇게 보면 면접에서 “이론만 아는 사람”이 아니라  
**실제 코드에 연결해서 설명할 수 있는 사람**이 됩니다.
