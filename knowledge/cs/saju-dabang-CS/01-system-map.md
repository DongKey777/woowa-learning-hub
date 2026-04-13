# 01. 시스템 맵

## 한눈에 보기

```text
Toss App WebView
  -> app/ (React + Vite + TypeScript)
  -> api-prelaunch.saju-dabang.com
     -> server-java api
     -> server-java worker
     -> postgres
     -> redis
```

## 큰 흐름

### 1. 인증

- 프론트가 토스 로그인 브리지를 통해 로그인
- 백엔드는 토스 OAuth 정보를 받아 사용자와 세션을 저장
- 이후 요청은 `Bearer` 또는 `X-Device-Id`로 식별

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/app/src/store/authStore.api.ts`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/api/AuthController.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/server/common/auth/RequestAuthResolver.java`

### 2. 운세 생성

- 프론트가 `POST /api/readings/jobs` 호출
- 서버는 코인을 확인하고 reserve
- worker 모드면 Redis queue에 적재
- worker가 처리 후 `reading_results` 저장
- 프론트는 SSE 또는 상태 조회로 완료를 감지

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingJobCommandService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/processing/ReadingJobProcessor.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/api/ReadingEventController.java`

### 3. 결제

- 프론트 IAP SDK -> 백엔드 `/api/coins/purchase`, `/api/coins/grant`
- 백엔드는 order 검증 후 `transactions`, `purchase_orders`, `coin_ledger` 반영

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/app/src/hooks/useIAP.purchase.ts`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/api/BillingController.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/infra/persistence/BillingJdbcRepository.java`

## 여기서 공부할 수 있는 CS 주제

- 네트워크: HTTP, HTTPS, DNS, SSE
- 데이터베이스: 트랜잭션, 멱등성, 정합성, 인덱스
- 운영체제: 프로세스, 스레드, 동시성, 큐 소비자
- 보안: 인증, 세션, 암호화, mTLS
- 소프트웨어 공학: 계층 분리, 포트/어댑터, bounded context

## 면접식 요약

“사주다방은 프론트에서 사주 계산을 수행하고, Java 백엔드에서 인증, 결제, 비동기 운세 생성, 영속화를 처리하는 구조입니다. 이 안에 HTTP/SSE, Redis queue, PostgreSQL 트랜잭션, 세션/암호화, 아키텍처 분리 같은 CS 개념이 실제 코드로 녹아 있습니다.”
