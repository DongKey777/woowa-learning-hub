# HTTP/REST를 사주다방 코드로 이해하기

## 핵심 개념

- HTTP는 요청/응답 기반 통신
- REST는 자원과 행위를 URL + Method로 나누는 스타일
- Method 선택은 “이 요청이 상태를 바꾸는가?”와 강하게 연결된다

## 사주다방 예시

### 조회성 API

- `GET /api/auth/session`
- `GET /api/coins/balance`
- `GET /api/readings`
- `GET /api/readings/:readingId`
- `GET /api/readings/jobs/:jobId`

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/api/AuthController.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/api/BillingController.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/api/ReadingController.java`

### 상태 변경 API

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/coins/purchase`
- `POST /api/coins/grant`
- `POST /api/readings/jobs`

## 왜 이렇게 나누는가

- 조회는 캐시/재시도/이해가 쉬움
- 변경은 부작용이 있으니 명확히 POST로 구분

## 실제 코드 스니펫

`BillingController`를 보면 조회와 변경이 HTTP 메서드로 분리되어 있다.

```java
@GetMapping("/api/coins/balance")
public ResponseEntity<?> balance(@RequestHeader HttpHeaders headers) {
  AuthenticatedPrincipal principal = requestAuthResolver.resolve(headers);
  return ResponseEntity.ok(Map.of("coins", balanceQueryService.getBalance(principal.userId())));
}

@PostMapping("/api/coins/purchase")
public ResponseEntity<?> purchase(
  @RequestHeader HttpHeaders headers,
  @Valid @RequestBody CoinPurchaseRequest request
) {
  AuthenticatedPrincipal principal = requestAuthResolver.resolve(headers);
  return ResponseEntity.ok(
    billingCreditService.purchase(principal.userId(), request.orderId(), request.sku())
  );
}
```

관련 원본:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/api/BillingController.java`

## 코드 스니펫에서 읽어야 할 포인트

### `GET /api/coins/balance`
- 서버 상태를 바꾸지 않음
- 읽기 전용
- 프론트는 잔액 동기화 용도로 반복 호출 가능

### `POST /api/coins/purchase`
- 적립이라는 부작용이 있음
- body로 `orderId`, `sku`를 받음
- 뒤에서 Toss 검증 + DB write가 따라옴

즉 URL만 같아도 “읽는 요청”인지 “상태를 바꾸는 요청”인지에 따라 Method가 달라진다.

## 이 프로젝트에서 REST가 중요한 이유

프론트와 백엔드가 분리되어 있어서 API 계약이 곧 팀 간 약속이 된다.

예:
- 프론트는 `readingId`, `jobId`, `coinsRemaining` 같은 필드를 전제로 동작
- 서버는 이 형식을 안정적으로 유지해야 함

## 공부 포인트

1. “왜 GET인가?”
2. “왜 POST인가?”
3. “응답 필드는 프론트 상태머신과 어떻게 이어지나?”

## 면접 답변 포인트

“사주다방은 조회 API와 상태 변경 API를 명확히 분리했습니다. 예를 들어 운세 생성은 `POST /api/readings/jobs`, 결과 조회는 `GET /api/readings/:readingId`로 나누어 프론트 상태머신과 연결했습니다.”

## 꼬리질문

### Q. 그럼 `POST /api/readings/status`는 왜 조회처럼 보이는데 POST인가요?

A. 요청 body에 여러 hash/category 조합이 들어가고, 조회 대상이 단순 단건 자원이라기보다 계산형 batch status에 가깝기 때문이다. query string보다 body가 자연스럽고, 입력 검증도 쉬워진다.

### Q. GET도 서버 로그를 남기면 상태를 바꾸는 거 아닌가요?

A. 맞다. 하지만 REST에서 말하는 안전성은 보통 비즈니스 상태를 바꾸지 않는다는 의미에 더 가깝다. 로그와 메트릭은 허용되는 부수효과로 보는 경우가 많다.

### Q. 멱등성과 GET/POST는 어떤 관계가 있나요?

A. GET은 보통 멱등적이어야 하고, POST는 멱등적이지 않을 수 있다. 하지만 결제처럼 중요한 POST는 사주다방처럼 `orderId` 기반으로 멱등성을 별도로 보장해야 한다.
