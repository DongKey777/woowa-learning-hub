---
schema_version: 3
title: epoll, kqueue, io_uring
concept_id: operating-system/epoll-kqueue-io-uring
canonical: false
category: operating-system
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- readiness-vs-completion
- event-api-selection
- epoll-edge-trigger-drain
aliases:
- epoll kqueue io_uring comparison
- readiness vs completion io
- event notification api chooser
- epoll vs io_uring
- kqueue vs epoll
- io_uring adoption tradeoff
- linux event loop kernel api
- 많은 연결 io api 선택
- 이벤트 루프 커널 인터페이스 비교
- readiness model completion model 차이
symptoms:
- 연결 수가 많아질 때 epoll, kqueue, io_uring 중 무엇을 먼저 떠올려야 할지 모르겠어요
- event loop 이야기를 들으면 readiness 모델과 completion 모델이 한꺼번에 섞여요
- io_uring이 무조건 최신 정답처럼 보이는데 언제 과한 선택인지 판단이 안 돼요
intents:
- comparison
- design
prerequisites:
- operating-system/io-models-and-event-loop
- operating-system/syscall-user-kernel-boundary
next_docs:
- operating-system/epoll-level-edge-oneshot-wakeup-semantics
- operating-system/io-uring-operational-hazards-registered-resources-sqpoll
- operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement
linked_paths:
- contents/operating-system/io-models-and-event-loop.md
- contents/operating-system/epoll-level-edge-oneshot-wakeup-semantics.md
- contents/operating-system/io-uring-operational-hazards-registered-resources-sqpoll.md
- contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md
- contents/operating-system/timerfd-epoll-timer-integration.md
- contents/operating-system/eventfd-signalfd-epoll-control-plane-integration.md
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
confusable_with:
- operating-system/io-models-and-event-loop
- operating-system/epoll-level-edge-oneshot-wakeup-semantics
- operating-system/io-uring-operational-hazards-registered-resources-sqpoll
forbidden_neighbors:
expected_queries:
- 대량 연결 서버에서 epoll이랑 io_uring을 어떤 기준으로 비교해야 해?
- kqueue까지 포함해서 이벤트 통지 API 선택 기준을 한 번에 정리해줘
- readiness 기반 event loop와 completion 기반 io_uring 차이를 운영 관점에서 설명해줘
- 커넥션 수가 많을 때 최신 API를 바로 고르기 전에 무엇부터 봐야 해?
- epoll, kqueue, io_uring을 입문자가 혼동하지 않게 구분해줘
contextual_chunk_prefix: |
  이 문서는 운영체제 학습자가 대량 연결 서버에서 epoll, kqueue,
  io_uring 중 어느 커널 이벤트 경로가 맞는지 결정하게 돕는 chooser다.
  준비 신호만 모으는 방식, 완료 통지를 나중에 수거하는 방식, BSD 계열
  이벤트 묶음, syscall 왕복 줄이기, wakeup 비용과 배치 제출, 최신
  인터페이스가 항상 이득은 아님 같은 자연어 paraphrase가 본 문서의
  선택 기준에 매핑된다.
---
# epoll, kqueue, io_uring

> 한 줄 요약: 많은 연결을 다룰 때는 `blocking`을 줄이는 것보다, 커널이 I/O 준비 완료를 더 싸게 알려주도록 구조를 바꾸는 게 핵심이다.
>
> 문서 역할: 이 문서는 operating-system 운영 cluster 안에서 **이벤트 통지 API와 커널 인터페이스 선택**을 다루는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [I/O 모델과 이벤트 루프](./io-models-and-event-loop.md)
> - [epoll Level-Triggered, Edge-Triggered, ONESHOT Wakeup Semantics](./epoll-level-edge-oneshot-wakeup-semantics.md)
> - [io_uring Operational Hazards, Registered Resources, SQPOLL](./io-uring-operational-hazards-registered-resources-sqpoll.md)
> - [io_uring CQ Overflow, Provided Buffers, IOWQ Worker Placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)
> - [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - [file descriptor, socket, syscall cost](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Virtual Threads(Project Loom)](../language/java/virtual-threads-project-loom.md)
> - [gRPC vs REST](../network/grpc-vs-rest.md)

> retrieval-anchor-keywords: epoll, kqueue, io_uring, EPOLLET, EPOLLONESHOT, level triggered, edge triggered, completion queue, readiness model, async I/O

## 이 문서 다음에 보면 좋은 문서

- I/O 모델 전체 맥락은 [I/O Models and Event Loop](./io-models-and-event-loop.md)로 되돌아가면 좋다.
- `epoll` 세부 wakeup 함정은 [epoll Level-Triggered, Edge-Triggered, ONESHOT Wakeup Semantics](./epoll-level-edge-oneshot-wakeup-semantics.md)에서 이어진다.
- `io_uring` 운영 함정은 [io_uring Operational Hazards, Registered Resources, SQPOLL](./io-uring-operational-hazards-registered-resources-sqpoll.md)로 이어진다.

---

## 핵심 개념

`epoll`, `kqueue`, `io_uring`은 모두 "I/O가 준비되었을 때 알려주는 방법"을 제공하지만, 구현 철학이 다르다.

- `epoll`: Linux의 대표적 I/O 다중화 API. 준비된 fd만 효율적으로 추려준다.
- `kqueue`: BSD/macOS 계열의 이벤트 통지 API. fd뿐 아니라 타이머, 시그널 등 다양한 이벤트를 함께 다룬다.
- `io_uring`: Linux의 비교적 최신 비동기 I/O 인터페이스. submit/completion queue를 통해 syscall 수를 줄이고 커널-유저 경계를 더 얇게 만든다.

왜 중요한가:

- 커넥션 수가 많아지면 `read()`를 모든 소켓에 반복 호출할 수 없다.
- 스레드를 무작정 늘리면 컨텍스트 스위칭 비용이 커진다.
- 이벤트 루프, 리액티브 서버, 가상 스레드 모두 결국 이 계층을 이해해야 한다.

---

## 깊이 들어가기

### 1. `select`와 `poll`의 한계

초기 I/O 다중화는 `select`, `poll`이었지만 큰 규모에서는 한계가 있다.

- 검사 범위가 커질수록 비용이 늘어난다.
- ready fd만 효율적으로 추적하기 어렵다.
- 이벤트가 적어도 매번 전체 목록을 훑는 구조가 비싸다.

이 문제를 풀기 위해 `epoll`과 `kqueue`가 나왔다.

### 2. `epoll`의 핵심

`epoll`은 Linux에서 관심 있는 fd를 등록해두고, 준비된 fd만 돌려준다.

핵심 포인트:

- `epoll_ctl()`로 관심 fd를 등록/삭제
- `epoll_wait()`로 준비된 이벤트를 수신
- level-triggered와 edge-triggered 모드를 선택

Edge-triggered는 이벤트 폭주를 줄일 수 있지만, 읽어야 할 데이터를 끝까지 비우지 않으면 이벤트를 놓칠 수 있다.

### 3. `kqueue`의 핵심

`kqueue`는 fd 이벤트뿐 아니라 타이머, 프로세스 종료, 시그널까지 통합적으로 처리할 수 있다.

운영 감각에서는 다음이 중요하다.

- 이벤트 모델이 하나로 통합되면 서버 루프가 단순해질 수 있다.
- 하지만 OS마다 API와 semantics가 다르므로 이식성이 떨어질 수 있다.

### 4. `io_uring`의 핵심

`io_uring`은 submit queue와 completion queue를 분리해 비동기 작업을 등록하고 결과를 나중에 받는다.

장점:

- syscall 횟수를 줄이기 쉽다
- 배치 처리에 유리하다
- 고성능 서버에서 I/O 경로를 더 얇게 만들 수 있다

주의점:

- 모든 드라이버/파일시스템에서 동일하게 이점이 나는 것은 아니다
- 학습 곡선이 높다
- 디버깅이 단순 `read()/write()`보다 어렵다

---

## 실전 시나리오

### 시나리오 1: 커넥션은 적지 않은데 CPU가 I/O 대기보다 syscall에서 소모됨

원인 후보:

- 작은 단위의 `read()/write()` 반복
- 이벤트 루프가 아닌 스레드 풀 기반의 과도한 blocking 처리
- fd 수 대비 컨텍스트 스위칭과 wakeup 비용 증가

진단:

```bash
strace -c -p <pid>
perf top
ss -tanp | head
```

### 시나리오 2: Edge-triggered `epoll`에서 읽기 누락

이벤트를 한 번만 받고, 버퍼를 끝까지 비우지 않아서 후속 이벤트가 안 들어오는 버그다.

해결:

- fd를 `EAGAIN`이 나올 때까지 읽는다
- 루프에서 부분 읽기/부분 쓰기를 명시적으로 처리한다

### 시나리오 3: `io_uring` 도입 후 예상보다 성능 향상이 작음

가능한 이유:

- 워크로드가 실제로는 network-bound가 아니라 DB-bound
- 작은 요청이 너무 많아 batching 이점이 제한적
- 파일시스템/커널 버전/드라이버 특성상 이득이 작음

즉, `io_uring`은 만능이 아니라 **I/O 제출 비용과 컨텍스트 전환을 줄이는 도구**다.

---

## 코드로 보기

### `epoll` 루프의 전형적인 형태

```c
int epfd = epoll_create1(0);
struct epoll_event ev = {.events = EPOLLIN, .data.fd = listen_fd};
epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

while (1) {
    struct epoll_event events[128];
    int n = epoll_wait(epfd, events, 128, -1);
    for (int i = 0; i < n; i++) {
        if (events[i].data.fd == listen_fd) {
            int client_fd = accept(listen_fd, NULL, NULL);
            // client_fd를 non-blocking으로 전환 후 등록
        } else {
            // read/write를 EAGAIN까지 처리
        }
    }
}
```

### `io_uring`의 사고방식

```c
// 의사 코드
submit(read, fd1, buffer1);
submit(write, fd2, buffer2);
submit(timeout, 10ms);

while (cq = get_completions()) {
    handle(cq);
}
```

핵심은 "등록하고, 나중에 결과를 받는" 구조다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `select`/`poll` | 단순하다 | 큰 fd 집합에서 비싸다 | 학습/레거시 |
| `epoll` | Linux에서 효율적이다 | Edge-triggered 실수가 잦다 | 일반적인 고동시성 서버 |
| `kqueue` | 이벤트 종류가 풍부하다 | BSD 전용 감각이 필요하다 | BSD/macOS 환경 |
| `io_uring` | syscall과 전환 비용을 줄이기 좋다 | 디버깅/호환성/학습 비용 | 최신 Linux 고성능 서버 |

`epoll`과 `kqueue`는 이벤트 다중화, `io_uring`은 비동기 제출/완료 모델에 더 가깝다. 이 차이를 이해해야 "왜 어떤 서버는 event loop로 충분하고, 어떤 서버는 더 낮은 레벨의 비동기 I/O가 필요한가"를 설명할 수 있다.

---

## 꼬리질문

> Q: `epoll`이 `select`보다 왜 효율적인가요?
> 의도: 준비된 fd만 추적하는 구조를 이해하는지 확인
> 핵심: 매번 전체 fd를 순회하지 않고 ready 이벤트 중심으로 처리한다.

> Q: Edge-triggered를 쓰면 뭐가 어려운가요?
> 의도: 이벤트 누락 가능성을 아는지 확인
> 핵심: `EAGAIN`까지 버퍼를 비워야 하고, 부분 읽기/쓰기 처리가 필수다.

> Q: `io_uring`이 `epoll`보다 무조건 좋은가요?
> 의도: 최신 기술을 만능으로 오해하지 않는지 확인
> 핵심: 워크로드, 커널 버전, 디버깅 비용, 드라이버 지원에 따라 다르다.

---

## 한 줄 정리

많은 I/O를 처리할 때는 스레드를 늘리는 것보다, 커널이 준비 완료 이벤트를 싸게 알려주도록 루프를 설계하는 편이 더 중요하다.
