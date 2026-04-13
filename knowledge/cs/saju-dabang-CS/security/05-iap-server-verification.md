# IAP와 서버 검증

## 왜 서버 검증이 필요한가

클라이언트만 믿으면 안 된다.

이유:
- 클라이언트 조작 가능
- 중복 호출 가능
- orderId 위조 가능

## 사주다방 방식

1. 프론트가 orderId를 백엔드로 보냄
2. 서버가 Toss order status 조회
3. sku/status 검증
4. 적립 or grant 처리

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/application/BillingCreditService.java`

## 검증 포인트

- `tossUserKey` 존재 여부
- `orderId`
- `sku`
- `status`
- grantable 상태인지

## 면접 포인트

“결제는 프론트에서 시작되더라도, 최종 적립 판단은 서버가 해야 한다. 사주다방은 order status를 서버에서 검증한 후 코인을 반영한다.”
