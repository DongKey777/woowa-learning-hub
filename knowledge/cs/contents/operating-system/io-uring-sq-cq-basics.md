---
schema_version: 3
title: io_uring SQ CQ Basics
concept_id: operating-system/io-uring-sq-cq-basics
canonical: true
category: operating-system
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 83
review_feedback_tags:
- io-uring-sq
- submission-queue-completion
- queue
- async-io-syscall
aliases:
- io_uring SQ CQ basics
- submission queue completion queue
- async IO syscall reduction
- SQE CQE model
- ring based IO
- context switch reduction
intents:
- definition
- deep_dive
linked_paths:
- contents/operating-system/epoll-kqueue-io-uring.md
- contents/operating-system/io-uring-operational-hazards-registered-resources-sqpoll.md
- contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
- contents/operating-system/ebpf-perf-strace-production-tracing.md
expected_queries:
- io_uring SQ와 CQ는 submission과 completion을 어떻게 분리해?
- SQE CQE model이 syscall과 context switch 비용을 줄이는 방식은?
- epoll과 io_uring의 기본 mental model 차이는 뭐야?
- io_uring basics에서 operational hazards로 넘어가기 전 무엇을 알아야 해?
contextual_chunk_prefix: |
  이 문서는 io_uring의 기본 구조를 submission queue와 completion queue로 I/O 제출과 결과 확인을
  분리해 syscall/context switch 비용을 줄이는 asynchronous ring model로 설명한다.
---
# io_uring SQ, CQ Basics

> 한 줄 요약: io_uring은 submission queue와 completion queue로 I/O 제출과 결과 확인을 분리해 syscall과 context switch 비용을 줄이는 비동기 모델이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [io_uring Operational Hazards, Registered Resources, SQPOLL](./io-uring-operational-hazards-registered-resources-sqpoll.md)
> - [io_uring CQ Overflow, Provided Buffers, IOWQ Worker Placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - [softirq, hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)
> - [page cache thrash vs direct I/O](./page-cache-thrash-vs-direct-io.md)

> retrieval-anchor-keywords: io_uring, SQ, CQ, SQE, CQE, submission queue, completion queue, async I/O, registered buffers, fixed files

## 핵심 개념

`io_uring`은 요청을 제출하는 경로와 완료를 받는 경로를 분리한다. 앱은 submission queue에 작업을 넣고, kernel은 completion queue로 결과를 돌려준다.

- `SQ`: submission queue다
- `CQ`: completion queue다
- `SQE`: submission entry다
- `CQE`: completion entry다

왜 중요한가:

- syscall 횟수를 줄일 수 있다
- I/O가 많은 서버에서 제출/완료 경계를 얇게 만들 수 있다
- 하지만 디버깅과 운영 모델이 더 복잡하다

이 문서는 [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)보다 한 단계 더 낮은 수준에서 `io_uring`의 큐 구조를 본다.

## 깊이 들어가기

### 1. SQ와 CQ는 역할이 다르다

SQ는 "할 일 목록"이고 CQ는 "끝난 일 목록"이다.

- 앱은 SQE를 쌓는다
- 커널은 비동기적으로 처리한다
- CQE로 완료와 에러를 받는다

### 2. ring 구조는 batching에 강하다

`io_uring`의 이득은 요청을 많이 묶을수록 커진다.

- 여러 I/O를 한 번에 제출한다
- 완료도 묶어서 받는다
- syscall 경계가 줄어든다

### 3. registered resources가 성능에 도움을 준다

- fixed file
- registered buffer

이런 기능은 매번 인덱싱과 등록 비용을 줄인다. 대신 운영 복잡도가 높아진다.

### 4. io_uring은 만능이 아니다

- 작은 단순 I/O에서는 이득이 제한적일 수 있다
- 브리징 코드와 오류 처리 비용이 있다
- 커널과 사용자 공간의 책임 경계가 더 어려워진다

## 실전 시나리오

### 시나리오 1: epoll보다 이론상 더 빠른데 체감이 작다

가능한 원인:

- 요청이 너무 작다
- batching이 부족하다
- registered buffer/file 없이 쓰고 있다

### 시나리오 2: CQE를 받는 쪽이 병목처럼 보인다

가능한 원인:

- completion polling이 과하다
- consumer가 CQ를 제때 비우지 못한다
- backpressure를 읽지 못한다

### 시나리오 3: 운영에서 디버깅이 어렵다

가능한 원인:

- syscall trace가 덜 직관적이다
- event loop와 비동기 completion이 섞인다
- 전통적인 read/write 사고방식으로 보면 헷갈린다

이때는 [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)와 같이 봐야 한다.

## 코드로 보기

### 기본 모델

```text
prepare SQE
  -> submit to SQ
  -> kernel processes async
  -> CQE arrives
  -> app consumes completion
```

### 개념적 예시

```c
// 의사 코드
io_uring_submit(&ring);
io_uring_wait_cqe(&ring, &cqe);
```

### 운영 점검 감각

```bash
perf stat -p <pid> -e syscalls:sys_enter_io_uring_enter -- sleep 30
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `epoll` | 익숙하고 단순하다 | 제출 비용이 남는다 | 일반 이벤트 루프 |
| `io_uring` | syscall과 전환 비용을 줄인다 | 복잡하다 | 고성능 서버 |
| fixed resources | 재사용이 빠르다 | 관리가 어렵다 | 대량 I/O |
| 전통적 blocking I/O | 단순하다 | 확장성이 낮다 | 작은 도구/스크립트 |

## 꼬리질문

> Q: SQ와 CQ는 왜 분리되나요?
> 핵심: 제출과 완료를 분리해야 비동기 batching이 쉬워지기 때문이다.

> Q: io_uring이 epoll보다 무조건 좋은가요?
> 핵심: 아니다. 요청 규모와 운영 복잡도를 같이 봐야 한다.

> Q: registered buffer는 왜 도움이 되나요?
> 핵심: 매번 등록하거나 검증하는 비용을 줄일 수 있기 때문이다.

## 한 줄 정리

io_uring은 SQ/CQ 분리로 비동기 제출과 완료를 효율화하지만, batching과 운영 복잡도까지 같이 고려해야 진짜 이득이 난다.
