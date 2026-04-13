# SSE와 Replay를 사주다방으로 이해하기

## 개념

SSE(Server-Sent Events)는 서버가 클라이언트에 단방향 이벤트 스트림을 보내는 방식이다.

## 사주다방에서 필요한 이유

운세 생성은 즉시 끝나지 않는다.

중간에 필요한 것:
- `progress`
- `section`
- `completed`

즉 프론트는 “계속 상태를 받아야” 한다.

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/api/ReadingEventController.java`

## 사주다방의 SSE 특징

### 1. 실시간 스트림

서버는 `SseEmitter`로 이벤트를 전송한다.

### 2. replay

Redis list에 이벤트를 잠깐 저장했다가, 연결이 늦게 붙은 클라이언트가 가져갈 수 있게 한다.

코드:
- `JobEventKeys.replayKey(jobId)`
- `redisTemplate.opsForList().range(replayKey, 0, -1)`

### 3. terminal event

이벤트가 다음 중 하나면 스트림 종료:
- `completed`
- `failed`
- `refunded`
- `cancelled`

## CS 관점

이건 단순 실시간 통신이 아니라:
- 네트워크 지연
- 재연결
- 이벤트 유실 보정

을 고려한 설계다.

즉 “SSE + replay”는 **네트워크가 완벽하지 않다는 전제를 반영한 구조**다.

## 면접 포인트

“왜 WebSocket이 아니라 SSE인가?”  
- 서버 -> 클라이언트 단방향이면 충분
- 구현이 단순
- HTTP 기반이라 운영과 디버깅이 쉬움

“replay는 왜 필요한가?”  
- 연결이 늦게 붙거나 끊겼다가 복구될 때 이미 발생한 이벤트를 일부 복원하기 위해
