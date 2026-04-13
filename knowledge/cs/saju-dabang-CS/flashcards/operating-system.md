# Operating System Flashcards

- Q: worker를 분리한 이유는?
  A: 긴 작업이 API latency를 막지 않게 하기 위해

- Q: reliable queue 핵심 구성은?
  A: execution queue, processing queue, lease, ack, requeue

- Q: stale recovery는 왜 필요한가?
  A: 죽은 worker가 잡고 있던 작업을 복구하기 위해

- Q: virtual thread를 쓴 이유는?
  A: blocking 스타일을 유지하면서 동시성을 확보하기 위해

- Q: producer-consumer 구조란?
  A: producer가 작업을 넣고 consumer가 비동기 처리하는 구조
