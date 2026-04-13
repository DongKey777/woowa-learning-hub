# 운영체제/동시성 예상 답변

## Q. 왜 worker를 따로 뒀나요?

### 30초 답변

“운세 생성은 시간이 오래 걸리고 외부 LLM 호출도 포함되기 때문에 API 요청 처리와 분리했습니다.”

### 2분 답변

“API는 빠르게 `queued` 응답을 반환하고, 실제 생성은 worker가 처리하는 producer-consumer 구조를 사용했습니다. 이렇게 하면 HTTP latency를 낮추고, 장애가 나더라도 API와 worker의 영향 범위를 분리할 수 있습니다.”

### 5분 답변

“사주다방에서 worker 분리는 단순 성능 최적화가 아니라 책임 분리의 문제입니다. API 서버는 로그인, 결제, 조회 같은 짧은 요청을 빠르게 처리해야 합니다. 반면 운세 생성은 외부 LLM 호출, 결과 저장, 이벤트 발행까지 포함하는 긴 작업입니다.

이 둘을 같은 실행 흐름에 두면 HTTP 응답이 느려지고, 긴 작업 실패가 API 전체 안정성에도 영향을 줄 수 있습니다. 그래서 API는 job을 만들고 queue에 넣는 producer 역할만 하고, worker는 queue를 소비해서 실제 생성을 수행하는 consumer 역할을 맡도록 분리했습니다.

운영체제 관점에서는 프로세스 분리와 동시성 관리의 사례로 볼 수 있습니다. 프로세스를 분리하면 장애 격리가 쉬워지고, worker 내부에서는 virtual thread 같은 가벼운 동시성 모델을 사용해 복잡도를 낮출 수 있습니다. 사주다방은 이런 선택을 통해 요청 지연과 백그라운드 작업을 분리했습니다.”

### 꼬리질문

- worker를 같은 프로세스 안 스레드로 두면 안 되나?
- queue 유실은 어떻게 막았나?
- virtual thread를 왜 썼나?

## Q. reliable queue가 왜 필요한가요?

### 30초 답변

“worker가 작업을 가져간 뒤 죽어도 job이 유실되면 안 되기 때문입니다. execution queue, processing queue, lease, requeue 구조를 사용했습니다.”

### 2분 답변

“사주다방 worker는 Redis queue를 단순 pop으로 쓰지 않고, processing queue와 lease를 둡니다. 작업 중 프로세스가 죽으면 stale recovery가 processing queue의 작업을 다시 execution queue로 돌려보냅니다. 그래서 유실 가능성을 낮추고 복구 가능한 구조를 만들었습니다.”

### 5분 답변

“실서비스에서 queue를 쓸 때 가장 위험한 건 작업을 가져간 worker가 중간에 죽는 경우입니다. 단순 pop만 쓰면 작업이 메모리에서 사라져 유실될 수 있습니다. 사주다방은 이런 상황을 막기 위해 execution queue와 processing queue를 분리했습니다.

작업을 가져가면 processing queue로 옮기고 lease를 남깁니다. 이 lease는 현재 누가 처리 중인지를 보여주는 표시입니다. 정상 완료 시 ack로 정리하고, 실패 시 requeue로 다시 execution queue로 돌려보냅니다. 오래된 lease가 남아 있으면 stale recovery가 이를 감지해 재처리 가능하게 만듭니다.

이건 운영체제/동시성 질문에서 producer-consumer, 장애 복구, at-least-once delivery에 가까운 실전 예시로 설명할 수 있습니다. 완전한 exactly-once는 어렵지만, 멱등성과 상태 전이를 함께 두면 실무적으로 충분히 안전한 구조를 만들 수 있다는 점도 같이 말하면 좋습니다.”
