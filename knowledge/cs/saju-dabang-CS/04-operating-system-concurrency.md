# 04. 운영체제: 프로세스, 스레드, 동시성, 큐

## CS-study와 연결

- 운영체제 기본: `/Users/idonghun/IdeaProjects/woowa-2026/knowledge/cs/CS-study/contents/operating-system/README.md`

사주다방은 운영체제 이론을 체감하기 좋은 예시가 많다.

## 1. 프로세스와 역할 분리

현재 백엔드는 두 실행 단위가 있다.

- API 서버
- worker

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/SajuDabangServerApplication.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/SajuDabangWorkerApplication.java`

왜 나누나?

- API 요청 처리와 백그라운드 작업을 분리하기 위해
- 긴 작업이 HTTP 응답 지연을 만들지 않게 하기 위해

이건 운영체제 관점에서 **역할이 다른 프로세스를 분리 운영**하는 사례다.

## 2. 동기 vs 비동기

### 동기적 부분

- 로그인
- 잔액 조회
- reading detail 조회

즉 요청하면 바로 응답이 오는 흐름

### 비동기적 부분

- 운세 생성 job
- worker queue 소비
- 중간 progress 이벤트 전송

즉 요청 시점과 실제 완료 시점이 분리된다.

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingJobCommandService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/processing/ReadingJobProcessor.java`

## 3. 왜 queue가 필요한가

운세 생성은 즉시 끝나지 않는다.

그래서 API는:

1. job 생성
2. queue 적재
3. `queued` 응답

worker는:

1. queue 소비
2. LLM 호출
3. 결과 저장
4. 완료 이벤트 발행

이 구조는 **producer-consumer 문제**로 볼 수 있다.

## 4. reliable queue는 무슨 의미인가

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/queue/RedisReliableQueue.java`

핵심:

- execution queue
- processing queue
- lease key
- ack / requeue
- stale processing recovery

이건 단순 queue가 아니라 **실패 복구 가능한 queue**다.

왜 필요하나?

- worker가 잡을 꺼냈다가 죽을 수 있음
- 그러면 job 유실이 생기면 안 됨
- 그래서 processing queue와 lease를 두고 다시 복구 가능하게 만든다

운영체제/동시성 면접에선 이걸:

- 경쟁 상태 방지
- 작업 유실 방지
- at-least-once delivery 비슷한 보장

로 설명할 수 있다.

## 5. virtual thread는 왜 썼나

관련 코드:

- `Thread.startVirtualThread(...)`
- SSE event stream
- queue consumer

Java 21의 virtual thread는 “가벼운 스레드”처럼 생각하면 된다.

왜 좋나?

- 블로킹 코드를 더 단순하게 유지 가능
- WebFlux 같은 복잡한 reactive 전체 전환 없이도 동시성 처리 가능

즉 이 프로젝트는
**복잡한 비동기 요구를, 상대적으로 이해하기 쉬운 블로킹 스타일 + virtual thread로 해결**했다.

## 6. 면접 답변 예시

**Q. 왜 worker를 따로 뒀나요?**  
A. “운세 생성은 시간이 오래 걸릴 수 있고 외부 LLM 호출도 포함됩니다. 그래서 API 프로세스와 분리해 producer-consumer 구조로 만들고, Redis queue를 통해 비동기로 처리했습니다.”

**Q. reliable queue가 왜 필요한가요?**  
A. “worker가 job을 가져간 뒤 죽으면 작업이 유실될 수 있기 때문입니다. 그래서 execution queue와 processing queue를 분리하고 lease/ack/requeue로 복구 가능하게 만들었습니다.”
