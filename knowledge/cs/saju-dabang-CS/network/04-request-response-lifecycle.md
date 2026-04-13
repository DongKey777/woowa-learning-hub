# 요청-응답 라이프사이클

## 왜 이 문서를 보나

HTTP를 안다고 해도, 실제 서비스에서 요청 하나가 어디를 거쳐 가는지 설명하지 못하면 면접에서 약하다.

사주다방을 기준으로 “요청이 들어와서 응답이 나가기까지”를 따라간다.

## 예시 1. `GET /api/coins/balance`

### 단계

1. 프론트가 `fetch` 호출
2. 브라우저/WebView가 HTTPS 요청 전송
3. `Caddy`가 reverse proxy
4. Java server의 controller 진입
5. 인증 해석
6. service가 DB 조회
7. JSON 응답 반환

### 관련 코드

- 프론트 호출:
  - `/Users/idonghun/IdeaProjects/saju-dabang/app/src/store/coinStore.api.ts`
- 인증 해석:
  - `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/server/common/auth/RequestAuthResolver.java`
- controller:
  - `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/api/BillingController.java`

## 예시 2. `POST /api/readings/jobs`

이건 더 복잡하다.

### 단계

1. 프론트에서 운세 생성 요청
2. 서버가 입력 검증
3. 기존 결과/활성 job 확인
4. 코인 reserve
5. `reading_jobs`, `llm_logs` 기록
6. worker 모드면 Redis queue 적재
7. `queued` 또는 `completed` 응답

### 관련 코드

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingJobCommandService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingReservationApplicationService.java`

## 예시 3. `GET /api/readings/jobs/{jobId}/events`

### 단계

1. 클라이언트가 SSE 연결
2. 서버가 인증
3. job 소유 여부 확인
4. Redis replay 이벤트 조회
5. 이미 저장된 이벤트를 먼저 보냄
6. terminal event면 스트림 종료

### 관련 코드

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/api/ReadingEventController.java`

## 면접 포인트

“요청 하나가 reverse proxy, 인증, controller, service, DB/Redis를 거쳐 응답되는 흐름을 단계별로 설명할 수 있으면 좋다.”
