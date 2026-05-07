---
schema_version: 3
title: io_uring Provided Buffer Ring Head Resync CQ Overflow Worker Handoff
concept_id: operating-system/io-uring-provided-buffer-ring-head-resync-cq-overflow-worker-handoff
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- io-uring-provided
- buffer-ring-head
- resync-cq-overflow
- io-uring-buf
aliases:
- io_uring buf ring head resync
- IORING_REGISTER_PBUF_STATUS head
- CQ overflow partial drain
- worker handoff ledger
- kernel-owned app-owned ready-to-readd
- cached_head recovery
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md
- contents/operating-system/io-uring-provided-buffer-bid-leak-enobufs-diagnostics.md
- contents/operating-system/io-uring-fdinfo-pbuf-status-enobufs-reconciliation-playbook.md
- contents/operating-system/io-uring-recv-bundle-recvmsg-multishot-buffer-ring-head-recycling.md
- contents/operating-system/io-uring-multishot-cancel-rearm-drain-shutdown.md
symptoms:
- CQ overflow나 partial drain 뒤 local cached_head와 kernel frontier가 어긋난다.
- worker handoff 중 outstanding slot 상태를 복원하지 못해 buffer를 중복 recycle하거나 잃는다.
- io_uring_buf_ring_head 값만 보고 app-owned tail bid ledger를 복원했다고 착각한다.
expected_queries:
- io_uring_buf_ring_head로 cached_head를 resync할 때 무엇이 복원되고 무엇은 안 돼?
- CQ overflow와 partial drain 뒤 provided buffer ledger를 어떻게 다시 세워?
- kernel-owned app-owned ready-to-readd 상태를 worker handoff 후 어떻게 맞춰?
- PBUF_STATUS는 kernel frontier만 알려 준다는 말이 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 io_uring_buf_ring_head와 PBUF_STATUS가 kernel의 next consume cursor를 알려주지만
  CQ overflow, partial drains, worker handoff 뒤 outstanding slot 상태까지 복원해 주지는
  않는다는 점을 설명한다. drained CQE와 worker ledger를 함께 맞춘다.
---
# io_uring provided-buffer ring head resync after CQ overflow, partial drains, worker handoff

> 한 줄 요약: `io_uring_buf_ring_head()`는 `IORING_REGISTER_PBUF_STATUS`로 kernel의 "다음 consume cursor"를 다시 읽어 로컬 `cached_head`를 복구하는 control-plane API다. 하지만 이 값은 **kernel frontier만** 알려 주므로, CQ overflow 뒤 backlog, partial drain, CQ-to-worker handoff 이후 outstanding-slot 상태를 복원하려면 drained CQE와 worker ledger를 함께 맞춰서 `kernel-owned`, `app-owned`, `ready-to-readd`를 다시 세워야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring CQ overflow, multishot, provided buffers, IOWQ placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [io_uring Provided-Buffer Bid Leak, ENOBUFS, Recycle Diagnostics](./io-uring-provided-buffer-bid-leak-enobufs-diagnostics.md)
> - [io_uring fdinfo, PBUF status, ENOBUFS reconciliation playbook](./io-uring-fdinfo-pbuf-status-enobufs-reconciliation-playbook.md)
> - [io_uring recv bundle, recvmsg multishot, buffer-ring head recycling](./io-uring-recv-bundle-recvmsg-multishot-buffer-ring-head-recycling.md)
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [io_uring Provided Buffer Exhaustion Observability Playbook](./io-uring-provided-buffer-exhaustion-observability-playbook.md)

> retrieval-anchor-keywords: io_uring_buf_ring_head resync, provided buffer ring head resync, io_uring provided buffer head recovery, IORING_REGISTER_PBUF_STATUS, io_uring_buf_ring_available, cached head recovery, cached head drift, CQ overflow head recovery, CQ pressure buffer ring, partial drain head resync, worker handoff buffer ring, CQ to worker handoff, outstanding slot ledger, provided buffer ownership recovery, kernel frontier resync, app-owned bid ledger, kernel-owned partial bid, ready-to-readd buffers, drain and reseed buffer ring, multishot recv resync, recv bundle cached head, IORING_CQE_F_BUF_MORE, IOU_PBUF_RING_INC, undrained CQE replay

## 핵심 개념

`cached_head` drift는 사실 두 문제가 겹친 상태다.

- `cursor drift`: 앱이 믿는 `cached_head`가 실제 kernel `head`보다 뒤처지거나, handoff/restart 중 아예 유실됐다.
- `ownership drift`: 어떤 `bid`가 아직 kernel-owned인지, 이미 worker가 들고 있는지, 바로 `buf_ring_add()` 가능한지가 헷갈린다.

`io_uring_buf_ring_head()`는 첫 번째 문제를 푸는 API다.

- liburing `src/register.c` 구현상 이 helper는 `IORING_REGISTER_PBUF_STATUS`를 호출해 `struct io_uring_buf_status.head`를 읽는다.
- `io_uring_buf_ring_available()`는 같은 `head`를 이용해 `tail - head`를 계산하므로, kernel이 지금 바로 집어갈 수 있는 entry 수를 보여 준다.
- 둘 다 kernel-visible frontier만 알려 주며, `F_BUF_MORE` tail offset이나 worker queue 안의 window ref는 복원하지 못한다.

즉 resync에서 꼭 분리해야 할 질문은 다음 둘이다.

| 질문 | 어디서 복구하는가 |
|---|---|
| kernel이 다음에 어느 slot을 consume할 것인가 | `io_uring_buf_ring_head()` |
| 이미 CQE로 handed off 된 slot/window 중 무엇이 아직 outstanding인가 | drained CQE + worker/app ledger |

## 깊이 들어가기

### 1. 어떤 상황에서 `cached_head`가 믿을 수 없게 되나

| 상황 | 로컬 cursor가 틀어지는 이유 | 반드시 같이 확인할 것 |
|---|---|---|
| CQ overflow 또는 CQ backlog | kernel은 계속 receive를 consume하는데 userspace는 CQE 해석이 늦다 | undrained CQE, multishot terminal CQE, outstanding `bid` ledger |
| partial drain | CQ thread는 `cq_head`를 밀었지만 worker는 아직 window를 다 소비하지 않았다 | `cq_count`와 `buf_count`를 분리한 회수 상태 |
| worker handoff / hot restart | 새 owner가 ring/tail은 받았지만 이전 `cached_head`, per-window offset을 못 받았다 | handoff queue 안의 `(bid, off, len, state)` |
| `-ENOBUFS` churn 뒤 재arm | terminal CQE에는 `bid`가 없어서 마지막 generation 경계만 남는다 | 직전 `F_BUFFER` CQE들, `F_BUF_MORE` tail 여부 |

실전에서 자주 보이는 오판:

- `available()`이 양수니까 `cached_head`도 맞을 거라고 생각한다.
- `io_uring_buf_ring_head()` 한 번 읽으면 worker가 쥔 slot도 자동으로 정리된다고 생각한다.
- handoff 직후 첫 CQE의 시작 `bid`만 보고 bundle 폭 전체를 역산하려고 한다.

첫 번째는 race, 두 번째는 ownership 문제, 세 번째는 정보 부족 때문에 모두 위험하다.

### 2. `io_uring_buf_ring_head()`로 복구되는 것과 안 되는 것

복구되는 것:

- target `bgid`의 현재 kernel `head`
- 현재 시점 `kernel_visible_free = tail - head`
- 로컬 `cached_head`를 다시 어디에 맞춰야 하는지

복구되지 않는 것:

- 아직 CQ에서 읽지 못한 bundle CQE가 실제로 몇 slot을 건드렸는지
- `IOU_PBUF_RING_INC`에서 마지막 partial tail이 어느 offset까지 소비됐는지
- worker queue, parser, app queue가 붙잡고 있는 `bid/window`
- `!F_MORE` terminal CQE 전의 generation 경계

그래서 복구 규칙은 간단하다.

```text
buf_ring_head()는 kernel frontier를 고친다.
outstanding-slot state는 CQE replay와 worker ledger가 고친다.
둘 중 하나라도 빠지면 recycle을 늦춰야지, 추측하면 안 된다.
```

### 3. 안전한 resync 절차는 `freeze -> drain -> query -> reconcile -> resume`다

#### 1. freeze

- target `bgid`를 쓰는 새 `recv_multishot` / `recvmsg_multishot` rearm을 먼저 멈춘다.
- multishot generation이 살아 있으면 cancel 후 `!IORING_CQE_F_MORE` terminal CQE까지 기다리는 편이 가장 안전하다.
- 이유: resync 중에도 kernel `head`가 계속 움직이면 읽은 순간부터 다시 stale해진다.

#### 2. drain

- CQ에 보이는 CQE를 먼저 staging ledger로 옮긴다. 이 단계에서는 `io_uring_cqe_seen()`은 해도 좋지만, `buf_ring_add()`는 아직 하지 않는 편이 안전하다.
- bundle / incremental ring이면 CQE마다 아래를 분리 기록한다.
  - `first_bid`
  - `res`
  - `F_MORE`
  - `F_BUF_MORE`
  - worker에 넘긴 `(bid, off, len)` window
- partial drain 경로라면 `cq_count`와 `buf_count`를 같은 숫자로 취급하지 않는다. 이때는 `__io_uring_buf_ring_cq_advance()` 같은 split helper가 맞다.

#### 3. query

```text
ret = io_uring_buf_ring_head(ring, bgid, &kernel_head)
avail = io_uring_buf_ring_available(ring, br, bgid)   // optional snapshot
```

- `kernel_head`는 "지금 kernel이 다음에 consume할 slot"이다.
- `avail`은 그 시점 snapshot일 뿐이며 inflight I/O가 남아 있으면 바로 바뀔 수 있다.
- resync 시점에는 `cached_head = kernel_head`를 새 anchor로 삼는다.

#### 4. reconcile

여기가 핵심이다. 방법은 두 경우로 갈린다.

**A. 마지막 안정 checkpoint가 남아 있는 경우**

- 예: CQ overflow로 lag만 생겼고, 손상 전 `cached_head`와 handoff ledger는 남아 있다.
- 이때는 checkpoint의 `cached_head`부터 staging CQE를 replay해 contiguous slot 범위를 복원한다.
- replay 결과 cursor와 `kernel_head`가 다르면:
  - `kernel_head`를 진실로 채택한다.
  - replay gap에 걸친 slot은 `unknown`으로 남긴다.
  - `unknown` slot은 worker/app이 소유를 증명하기 전까지 recycle 금지다.

**B. checkpoint가 없고 cursor를 완전히 잃은 경우**

- 예: worker handoff 중 프로세스 재시작, CQ thread와 worker 간 shared cursor 유실.
- 이때는 `kernel_head`만으로 과거 bundle 폭을 역산할 수 없다.
- 안전한 복구는 "역산"이 아니라 "generation cut"이다.
  1. terminal `!F_MORE`까지 drain한다.
  2. worker queue가 이미 알고 있는 `(bid, off, len)`만 app-owned로 인정한다.
  3. 나머지는 `unknown outstanding`으로 남긴다.
  4. `unknown`이 0이 될 때까지 재공급하지 않거나, 필요하면 해당 `bgid`를 drain-and-reseed 한다.

즉 handoff에서 중요한 것은 `buf_ring_head()` 자체보다 **handoff metadata를 잃지 않는 것**이다.

#### 5. resume

resume 직전에는 아래 식이 맞아야 한다.

```text
ring_entries
  = kernel_visible_free
  + kernel_owned_partial
  + app_owned
  + ready_to_readd
  + unknown
```

- 정상 resume 조건은 `unknown == 0`이다.
- `unknown > 0`이면 그 ring은 아직 추측 상태다. 재arm보다 `drain-and-reseed`가 안전하다.
- `kernel_owned_partial`은 `F_BUF_MORE` tail 때문에 아직 kernel이 계속 쓸 수 있는 slot이다.

### 4. 상황별 복구 요령

| 상황 | 최소 안전 절차 | 핵심 포인트 |
|---|---|---|
| CQ overflow 뒤 backlog만 큰 경우 | rearm stop -> CQ drain -> `buf_ring_head()` -> staging CQE replay | old checkpoint가 있으면 exact replay 가능성이 높다 |
| CQ thread는 빨리 돌고 worker만 느린 partial drain | CQ seen과 buffer return을 분리 -> worker queue 기준 `app_owned` 재구축 -> `kernel_head`로 cursor만 보정 | `cq_count == buf_count` 가정이 깨진다 |
| worker handoff / hot restart | terminal drain -> `kernel_head` 읽기 -> surviving worker ledger만 인정 -> unknown zero 후 resume | head만으로는 잃어버린 bundle span을 못 복원한다 |
| `-ENOBUFS` 뒤 즉시 재arm하려는 경우 | final CQE 전에 handed-off 된 `bid` 정산 -> `kernel_head`와 ledger reconcile -> 필요 시 drain-and-reseed | terminal CQE 자체에는 보통 `bid`가 없다 |

### 5. handoff-safe 설계를 하려면 무엇을 남겨야 하나

`io_uring_buf_ring_head()`는 control-plane escape hatch지만, worker handoff를 정말 안전하게 만들려면 작은 ledger가 하나 더 필요하다.

- `last_stable_cached_head`
- `handoff_seq` 또는 checkpoint generation
- `per_bid_state`: `kernel_partial | app_owned | ready_to_readd`
- `per_window_ref`: `(bid, off, len, consumer_count)`

특히 bundle + incremental ring에서는 `bid`만으로는 부족하다.

- bundle은 `first bid + res bytes`만 준다.
- incremental ring은 `F_BUF_MORE` 때문에 같은 `bid`가 계속 kernel-owned일 수 있다.
- 따라서 handoff payload는 최소한 `window` 단위여야 한다.

이 mini-ledger가 있으면 overflow/backlog 후에는 "replay + kernel_head 확인"으로 끝나고, 없으면 "drain-and-reseed"가 기본값이 된다.

## 운영 체크리스트

- `io_uring_buf_ring_head()`는 fast path 매 CQE마다 부르는 API가 아니라 drift가 생겼을 때 cursor를 재앵커링하는 control-plane helper로 쓴다.
- resync 전에 target `bgid`에 대한 새 rearm을 멈춘다.
- `io_uring_buf_ring_available()`는 free-count snapshot일 뿐 ownership 증거가 아니다.
- `F_BUF_MORE`가 남은 tail slot은 `kernel_owned_partial`로 유지하고 조기 recycle하지 않는다.
- `cq_count != buf_count`일 수 있음을 기본값으로 두고, helper도 그 가정에 맞춰 고른다.
- `kernel_head`와 replay cursor가 다르면 kernel 쪽을 진실로 채택하고 gap은 `unknown`으로 남긴다.
- worker handoff에서 cursor checkpoint가 없으면 역산보다 `drain-and-reseed`를 택한다.

## 꼬리질문

> Q: `io_uring_buf_ring_head()`만 읽으면 어떤 `bid`를 다시 넣어야 하는지 바로 알 수 있나요?
> 핵심: 아니다. 이 API는 kernel frontier만 알려 준다. 재공급 가능 여부는 CQE와 worker ledger로 따로 정산해야 한다.

> Q: CQ overflow가 났으면 `cached_head = kernel_head`만 하고 바로 재arm해도 되나요?
> 핵심: 대개 위험하다. undrained CQE와 outstanding worker window를 먼저 맞추지 않으면 같은 backing buffer를 조기 recycle할 수 있다.

> Q: worker handoff에서 이전 `cached_head`를 잃어버렸는데 bundle span을 현재 `kernel_head`로 역산할 수 있나요?
> 핵심: 안전하게는 어렵다. 현재 head는 "다음 cursor"만 알려 줄 뿐 과거 CQE가 몇 slot을 소비했는지는 말해 주지 않는다.

> Q: `io_uring_buf_ring_available()`가 양수면 `unknown` slot이 있어도 괜찮나요?
> 핵심: 아니다. free-count와 ownership은 다른 질문이다. `unknown`이 남아 있으면 재공급은 보수적으로 미뤄야 한다.

## 참고 소스

- [`io_uring_register(2)` in liburing, `IORING_REGISTER_PBUF_STATUS`](https://github.com/axboe/liburing/blob/master/man/io_uring_register.2)
- [`src/register.c` in liburing, `io_uring_buf_ring_head()` implementation](https://github.com/axboe/liburing/blob/master/src/register.c)
- [`liburing.h` in liburing, `io_uring_buf_ring_available()` / `__io_uring_buf_ring_cq_advance()`](https://github.com/axboe/liburing/blob/master/src/include/liburing.h)
- [`io_uring_setup_buf_ring(3)` in liburing, `IOU_PBUF_RING_INC` / `IORING_CQE_F_BUF_MORE`](https://github.com/axboe/liburing/blob/master/man/io_uring_setup_buf_ring.3)
- [`io_uring_prep_recv(3)` in liburing, bundle receive cached-head guidance](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_recv.3)
- [`test/recv-multishot.c` in liburing, terminal `-ENOBUFS` CQE pattern](https://github.com/axboe/liburing/blob/master/test/recv-multishot.c)
- [`test/read-inc-buf-more.c` in liburing, `F_BUF_MORE` on partial consume and EOF](https://github.com/axboe/liburing/blob/master/test/read-inc-buf-more.c)

## 한 줄 정리

`io_uring_buf_ring_head()`는 CQ pressure 뒤 로컬 `cached_head`를 다시 kernel cursor에 맞추는 API지만, 그 자체로 outstanding-slot ownership을 복구하지는 못한다. 안전한 복구는 항상 `freeze -> drain -> buf_ring_head() -> CQE/worker ledger reconcile -> resume` 순서로 해야 하며, handoff metadata를 잃었으면 추측보다 `drain-and-reseed`가 맞다.
