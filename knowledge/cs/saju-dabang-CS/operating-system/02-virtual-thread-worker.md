# Virtual Thread와 Worker

## 개념

Java 21 virtual thread는 상대적으로 가벼운 스레드 실행 모델이다.

## 사주다방에서 사용된 곳

- SSE 스트림 처리
- Redis queue consumer

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/api/ReadingEventController.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/queue/RedisReliableQueueConsumer.java`

## 왜 좋은가

- blocking 코드 스타일 유지 가능
- reactive stack 전체 도입 없이 동시성 확보 가능

## 면접 포인트

“사주다방은 WebFlux 대신 virtual thread + MVC/SSE를 택해 복잡도를 낮췄다.”
