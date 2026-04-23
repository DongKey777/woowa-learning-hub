# io_uring Operational Hazards, Registered Resources, SQPOLL

> 한 줄 요약: `io_uring`은 빠를 수 있지만, SQ/CQ 자체보다 pointer lifetime, registered resource pinning, SQPOLL 특성, CQ consumption discipline을 틀리면 운영에서 훨씬 더 교묘한 장애를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring SQ, CQ Basics](./io-uring-sq-cq-basics.md)
> - [io_uring CQ Overflow, Provided Buffers, IOWQ Worker Placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [io_uring Provided Buffer Rings, Fixed Buffers, Memory Pressure](./io-uring-provided-buffers-fixed-buffers-memory-pressure.md)
> - [io_uring SQPOLL fdinfo Matrix and Worker-Mode Submit-Side Debugging](./io-uring-sqpoll-fdinfo-worker-mode-submit-debugging.md)
> - [io_uring Cancel Scope with Fixed Files and Mixed recv/send/poll Paths](./io-uring-cancel-scope-fixed-files-mixed-ops.md)
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)

> retrieval-anchor-keywords: io_uring hazards, SQPOLL, SqThread, SqThreadCpu, io_uring-sq, IORING_SQ_NEED_WAKEUP, registered buffers, fixed buffers, fixed files, direct descriptors, cancel scope, cancel user_data, cancel_fd, IORING_ASYNC_CANCEL_FD_FIXED, IORING_ASYNC_CANCEL_OP, CQ overflow, pointer lifetime, submit stable, memlock, RLIMIT_MEMLOCK, provided buffers, provided buffer low-water, multishot cancel, request teardown, io_uring operations debugging

## 핵심 개념

`io_uring` 입문 문서만 보면 "SQE 넣고 CQE 받는다"로 단순해 보이지만, 운영 문제는 그 사이의 자원 수명과 polling 모델에서 자주 터진다. 특히 registered buffer/file, SQPOLL, CQ draining은 일반 `read/write` 사고방식과 다르게 관리해야 한다.

- `registered buffers`: 커널이 장기 참조하거나 pinning하는 버퍼다
- `fixed files`: registered file set을 인덱스로 쓰는 방식이다
- `SQPOLL`: 커널 poll thread가 submission queue를 직접 관찰하는 모드다
- `CQ draining`: CQE를 제때 수거하는 운영 discipline이다

왜 중요한가:

- pointer lifetime을 잘못 잡으면 드물게만 터지는 memory corruption/invalid I/O처럼 보일 수 있다
- registered resources는 성능 대신 pinning/memlock/lifecycle 부채를 만든다
- CQ를 늦게 비우면 backpressure가 숨은 곳에서 폭발한다

## 깊이 들어가기

### 1. submit 완료와 operation 완료는 다른 순간이다

`io_uring`에서 많은 초보 버그는 "submit이 끝났으니 이제 메모리를 바꿔도 된다"는 오해에서 나온다.

- 일부 submission-time pointer는 submit 이후 안정성이 줄어들 수 있다
- 하지만 I/O 데이터 버퍼는 completion까지 살아 있어야 하는 경우가 많다
- SQPOLL에서는 pointer lifetime 감각이 더 길어진다

즉 `submit done != data lifetime over`다.

### 2. registered buffers/files는 성능 대신 pinning 부채를 만든다

registered resource의 장점은 분명하다.

- per-I/O overhead 감소
- fixed file index로 lookup 비용 절감
- high-rate path에서 batching 효과 상승

하지만 운영 함정도 있다.

- buffer pinning이 `RLIMIT_MEMLOCK`과 충돌할 수 있다
- huge page 일부만 써도 전체가 pinning될 수 있다
- resource update/unregister가 in-flight I/O 때문에 즉시 해제되지 않을 수 있다

그래서 "등록해 두면 빨라진다"보다 "등록한 자원을 언제까지 누가 쥐고 있나"가 중요하다.

### 3. SQPOLL은 syscall을 줄이지만 수명/권한/CPU 모델을 바꾼다

SQPOLL은 submit syscall을 줄일 수 있지만, 일반 모드와 운영 특성이 다르다.

- polling thread가 queue를 본다
- 커널 버전/설정에 따라 privilege 감각이 달라질 수 있다
- pointer stability 요구와 CPU affinity 고민이 커진다

특히 "가볍게 켜면 자동으로 빨라질 것"처럼 취급하면 안 된다. SQPOLL은 성능 옵션이면서 동시에 운영 모델 변경이다.
submit-side stall을 볼 때 `SqThread`, `SqThreadCpu`, regular ring 대비 scheduler target이 어떻게 달라지는지는 [io_uring SQPOLL fdinfo Matrix and Worker-Mode Submit-Side Debugging](./io-uring-sqpoll-fdinfo-worker-mode-submit-debugging.md)에서 바로 이어서 본다.

### 4. CQ를 늦게 비우면 completion side backpressure가 생긴다

많은 팀이 submit path만 본다. 하지만 completion consumer가 느리면 문제는 CQ에서 생긴다.

- CQE를 늦게 수거한다
- eventfd notification 수와 CQE 수를 1:1로 오해한다
- completion 폭주가 handler backlog로 바뀐다

즉 `io_uring`의 bottleneck은 submit보다 "completion을 누가 어떻게 소비하느냐"에서 더 자주 드러난다.

## 실전 시나리오

### 시나리오 1: 특정 요청에서만 아주 드물게 잘못된 버퍼가 보인다

가능한 원인:

- submit 후 completion 전에 버퍼 수명을 끝냈다
- SQPOLL 환경에서 pointer 안정성 가정을 잘못했다
- registered buffer update 타이밍과 in-flight I/O가 겹쳤다

대응 감각:

- submit/cqe 사이 버퍼 수명을 문서화한다
- reusable buffer pool과 per-request buffer를 섞지 않는다
- fixed buffer update는 inflight 경계와 같이 본다

### 시나리오 2: registered buffer를 켰더니 어떤 노드에서만 이상하게 실패한다

가능한 원인:

- `RLIMIT_MEMLOCK` 제약
- huge page pinning이 예상보다 크다
- buffer가 anonymous/file-backed 조건과 안 맞는다

### 시나리오 3: CPU는 줄었는데 latency는 오히려 들쭉날쭉하다

가능한 원인:

- SQPOLL thread 배치가 나쁘다
- CQ consumer가 일정하지 않다
- batching 효과보다 completion skew가 더 크다

이 경우는 `io_uring` 도입을 "syscall 감소" 하나로만 평가하면 안 된다.

## 코드로 보기

### 운영 체크 감각

```text
SQ path
  -> how long must pointers stay valid?

registered resources
  -> how much memory/file pinning debt exists?

CQ path
  -> who drains completions, and how quickly?
```

### 질문형 체크리스트

```text
Are submitted data buffers alive until completion?
Are fixed resources updated only with inflight safety in mind?
Does SQPOLL change the CPU/ownership model in this service?
Can the completion side fall behind under burst load?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| plain io_uring | batching 이점을 얻기 쉽다 | lifecycle discipline이 여전히 필요하다 | moderate async I/O |
| registered buffers/files | per-I/O overhead를 줄인다 | pinning과 update complexity가 커진다 | very hot path |
| SQPOLL | submit syscall을 더 줄일 수 있다 | 운영 모델과 pointer lifetime 감각이 더 복잡해진다 | highly tuned servers |
| classic epoll + sync ops | 디버깅이 직관적이다 | submit/completion overhead는 남는다 | simpler operations |

## 꼬리질문

> Q: `io_uring_submit()`가 끝나면 버퍼를 바로 재사용해도 되나요?
> 핵심: 항상 그런 것은 아니다. 실제 I/O 데이터 버퍼는 completion까지 안정성이 필요한 경우가 많다.

> Q: registered buffer는 왜 운영에서 위험할 수 있나요?
> 핵심: 성능은 좋아지지만 pinning, memlock, update lifecycle 부채를 만들기 때문이다.

> Q: SQPOLL은 그냥 더 빠른 옵션인가요?
> 핵심: 아니다. syscall 비용을 줄이는 대신 CPU 배치와 lifetime 모델까지 바꾸는 운영 옵션이다.

## 한 줄 정리

`io_uring`의 진짜 운영 난이도는 비동기 I/O 자체보다, "자원 수명을 누가 언제까지 책임지는가"를 일반 syscall 모델보다 훨씬 엄격하게 관리해야 한다는 데 있다.
