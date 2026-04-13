# 프로세스/스레드 모델

## 사주다방의 실행 단위

- API 서버 프로세스
- worker 프로세스

## 왜 분리하나

- 요청 응답과 긴 백그라운드 작업을 분리
- 장애 범위를 줄이기 위해

## 관련 코드

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/SajuDabangServerApplication.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/SajuDabangWorkerApplication.java`

## 사주다방에 맞게 해석하기

### API 프로세스
- 로그인 처리
- 결제 검증
- 운세 job 생성
- 조회 API

### worker 프로세스
- queue 소비
- LLM 호출
- 결과 저장
- 완료 이벤트 발행

즉 API는 짧고 빠른 요청 중심, worker는 오래 걸리는 작업 중심이다.

## 스레드 관점

하나의 프로세스 안에서도 여러 실행 흐름이 존재한다.

예:
- HTTP 요청 처리 스레드
- virtual thread 기반 작업
- Redis 네트워크 I/O

## 실제 코드 포인트

worker는 `SmartLifecycle`로 기동되고, consumer가 virtual thread로 루프를 돈다.

```java
thread = Thread.startVirtualThread(() -> {
  while (running.get()) {
    Optional<ClaimedReadingJob> claimed = queue.claimNext(pollTimeout);
    if (claimed.isEmpty()) {
      continue;
    }
    claimedJob = claimed.get();
    handler.handle(claimedJob);
    claimedJob.ack();
  }
});
```

## 면접 포인트

“서버와 worker를 분리하면 책임이 명확해지고, 긴 작업이 HTTP latency를 막지 않게 할 수 있다.”

## 꼬리질문

### Q. worker를 같은 프로세스 안 스레드로만 돌리면 안 되나요?

A. 가능하지만 장애 격리와 운영 분리가 약해진다. worker가 죽거나 오래 걸려도 API는 살려두는 쪽이 더 안전하다.

### Q. 프로세스를 나누면 단점은 없나요?

A. 배포와 관측, 자원 관리가 더 복잡해진다. 하지만 사주다방처럼 긴 백그라운드 작업이 중요한 서비스에선 장점이 더 크다.

### Q. 그럼 멀티 프로세스와 멀티 스레드를 같이 쓰는 건가요?

A. 맞다. 프로세스 레벨로는 API와 worker를 나누고, 각 프로세스 내부에선 스레드/virtual thread를 사용한다.
