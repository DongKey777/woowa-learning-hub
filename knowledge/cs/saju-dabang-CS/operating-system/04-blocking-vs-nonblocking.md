# Blocking vs Non-Blocking

## 개념

- blocking: 작업 끝날 때까지 기다림
- non-blocking: 기다리지 않고 다음 작업 진행

## 사주다방에서의 사례

### HTTP 요청 처리

Spring MVC는 기본적으로 요청 단위 처리 관점에서 blocking 스타일로 이해해도 된다.

### worker queue 소비

`claimNext()`는 queue에서 작업을 기다린다.

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/queue/RedisReliableQueueConsumer.java`

이건 blocking 성격이 있지만, virtual thread 위에서 돌기 때문에 전체 구조 복잡도를 낮출 수 있다.

## 왜 reactive로 안 갔나

이 프로젝트는:
- SSE는 필요하지만
- 전체를 reactive로 밀 정도로 규모가 크진 않다

그래서 “blocking 스타일 + virtual thread”가 더 이해하기 쉽고 운영도 단순하다.

## 면접 포인트

“논블로킹이 항상 정답은 아니다. 사주다방은 요구사항과 팀 이해도를 고려해 MVC + virtual thread 쪽이 더 적합했다.”
