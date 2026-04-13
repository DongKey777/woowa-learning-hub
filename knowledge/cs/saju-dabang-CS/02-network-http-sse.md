# 02. 네트워크: HTTP, HTTPS, SSE

## CS-study와 연결

- 네트워크 기본: `/Users/idonghun/IdeaProjects/woowa-2026/knowledge/cs/CS-study/contents/network/README.md`

이 문서에서는 그 이론이 사주다방에서 어떻게 쓰이는지 본다.

## 1. HTTP는 어디에 쓰이나

사주다방은 기본적으로 REST API 기반이다.

예:

- `GET /api/auth/session`
- `POST /api/auth/login`
- `GET /api/coins/balance`
- `POST /api/readings/jobs`
- `GET /api/readings/:readingId`

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/api/AuthController.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/api/BillingController.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/api/ReadingController.java`

### GET vs POST를 이 프로젝트로 이해하기

- `GET`: 상태 조회
  - 잔액 조회
  - 세션 확인
  - reading detail 조회
- `POST`: 상태 변경
  - 로그인
  - 운세 job 생성
  - 결제 적립

면접 포인트:

“GET은 조회, POST는 상태 변경이라는 원칙이 실제 API 설계에 반영돼 있습니다.”

## 2. HTTPS는 왜 필요한가

private/prelaunch/test 환경에서도 백엔드는 HTTPS로 연결된다.

이유:

- 토스 앱 WebView에서 보안 연결 요구
- 로그인/결제/세션 정보 보호

관련 파일:

- `/Users/idonghun/IdeaProjects/saju-dabang/infra/single-box/Caddyfile`
- `/Users/idonghun/IdeaProjects/saju-dabang/docs/PRELAUNCH-MINIMAL-INFRA.md`

### DNS와 도메인

- `api-prelaunch.saju-dabang.com`
  - prelaunch Java backend 주소
- Route53이 도메인을 EC2 IP로 연결

면접 포인트:

“도메인은 사람이 읽는 이름이고, DNS가 실제 서버 IP로 연결합니다. 사주다방은 prelaunch 검증용 도메인을 분리해 운영했습니다.”

## 3. SSE는 왜 썼나

운세 생성은 시간이 걸린다. 그래서 프론트가 결과를 기다리는 동안 진행 상황과 부분 결과를 받아야 한다.

사주다방은 `SSE(Server-Sent Events)`를 사용한다.

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/api/ReadingEventController.java`

핵심:

- 서버는 `text/event-stream` 응답
- 클라이언트는 연결을 유지
- 서버가 `progress`, `section`, `completed` 이벤트를 순차적으로 보냄

### 왜 WebSocket이 아니라 SSE인가

이 프로젝트 관점에선:

- 서버 -> 클라이언트 단방향 푸시가 핵심
- 구현이 더 단순
- HTTP 기반이라 디버깅도 쉬움

즉 “서버가 중간 결과를 계속 푸시”하면 충분해서 SSE가 더 적합했다.

## 4. replay 방식은 무슨 의미인가

`ReadingEventController`는 Redis replay list에서 이벤트를 꺼내 전송한다.

이건 네트워크 관점에서 보면:

- 연결이 늦게 붙어도 이미 발생한 이벤트를 일부 복원 가능
- 실시간 스트림 + 재연결 복구를 절충한 방식

관련 코드:

- `replayKey(jobId)` 사용
- `redisTemplate.opsForList().range(replayKey, 0, -1)`

## 5. 면접 답변 예시

**Q. SSE와 WebSocket 차이는? 왜 이 프로젝트에 SSE를 썼나요?**  
A. “SSE는 서버에서 클라이언트로 단방향 스트림을 보낼 때 적합합니다. 사주다방은 운세 생성 중간 결과를 서버가 계속 푸시하는 구조라 SSE가 더 단순하고 적합했습니다. 실제로 `/api/readings/jobs/{jobId}/events`에서 `SseEmitter`를 사용해 progress, section, completed 이벤트를 보냅니다.”
