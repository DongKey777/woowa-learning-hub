# 실패 복구 라이프사이클

## 왜 중요한가

실서비스는 항상 실패한다.

문제는 실패 자체보다,
**실패 후 상태가 어떻게 남느냐**다.

## 사주다방 복구 지점

### 1. worker crash

- processing queue
- lease key
- stale recovery

### 2. 운세 생성 실패

- reserved -> refunded
- error_message 남김
- job 상태 terminal 전환

### 3. IAP 미결 주문

- pending order recovery
- grant 재시도

## 관련 코드

- queue recovery: `RedisReliableQueue`
- refund 흐름: `ReadingRefundApplicationService`
- IAP recovery: 프론트 `useIAP.recovery.ts`, 서버 billing grant

## 면접 포인트

“좋은 시스템은 성공 흐름보다 실패 복구 흐름이 더 중요하다. 사주다방은 queue, 코인, IAP 모두 복구 경로를 별도로 설계했다.”
