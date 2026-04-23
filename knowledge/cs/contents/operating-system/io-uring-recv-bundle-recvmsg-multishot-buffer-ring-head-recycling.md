# io_uring recv bundle, recvmsg multishot, buffer-ring head recycling

> 한 줄 요약: `recv_multishot + IORING_RECVSEND_BUNDLE`는 CQE 하나가 여러 contiguous provided buffer를 함께 소비할 수 있고, `IOU_PBUF_RING_INC`가 켜지면 accounting 단위가 "CQE 하나 = bid 하나"가 아니라 "**CQE가 넘긴 byte window + 아직 kernel-owned인 tail bid**"로 바뀐다. 그래서 burst receive에서는 low-water를 free-bid count가 아니라 `tail 잔여 바이트 + 다음 burst가 먹을 contiguous slot 수`로 계산해야 하고, recycle도 `bid 등장`이 아니라 `window 소비 완료 + F_BUF_MORE 해제`를 같이 봐야 안전하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring CQ overflow, multishot, provided buffers, IOWQ placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [io_uring provided buffer rings, fixed buffers, memory pressure](./io-uring-provided-buffers-fixed-buffers-memory-pressure.md)
> - [io_uring Provided-Buffer Bid Leak, ENOBUFS, Recycle Diagnostics](./io-uring-provided-buffer-bid-leak-enobufs-diagnostics.md)
> - [io_uring read vs read_multishot: incremental short-read, EOF, BUF_MORE, recycle timing](./io-uring-read-vs-read-multishot-incremental-short-read-eof-recycle.md)
> - [io_uring provided-buffer ring head resync after CQ overflow, partial drains, worker handoff](./io-uring-provided-buffer-ring-head-resync-cq-overflow-worker-handoff.md)
> - [io_uring send bundle, zerocopy notification, fixed-buffer completion accounting](./io-uring-send-bundle-zerocopy-fixed-buffer-completion-accounting.md)
> - [io_uring multishot cancel, rearm, drain, shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [io_uring completion observability playbook](./io-uring-completion-observability-playbook.md)
> - [eventfd, signalfd, epoll control-plane integration](./eventfd-signalfd-epoll-control-plane-integration.md)
> - [socket buffer autotuning, backpressure](./socket-buffer-autotuning-backpressure.md)

> retrieval-anchor-keywords: io_uring recv bundle, recv multishot bundle, recvmsg multishot, recvmsg zero payload, recvmsg header only, header-only recvmsg completion, control-only recvmsg completion, mixed recv recvmsg diagnostics, io_uring_recvmsg_out, io_uring_recvmsg_validate, io_uring_recvmsg_payload_length, io_uring_buf_ring_head, io_uring_buf_ring_available, io_uring_buf_ring_cq_advance, IORING_RECVSEND_BUNDLE, IORING_CQE_F_BUFFER, IORING_CQE_F_MORE, IORING_CQE_F_BUF_MORE, IOU_PBUF_RING_INC, provided buffer ring head tracking, bundle first bid, partial drain recycle, partial consume accounting, low-water math, effective headroom, tail room bytes, burst receive headroom, bid window ownership, cached head drift, shutdown drain, ENOBUFS, buffer id leak, recvmsg eof normalization, zero receive normalization, head resync after CQ pressure, worker handoff head recovery, pbuf status resync, bundle receive ownership example, cached_head worked example, contiguous bundle span example, per-bid ownership ledger example, repeated first bid continuation

## 핵심 개념

`recv bundle`과 `recvmsg multishot`는 둘 다 provided buffer ring을 쓰지만, CQE를 해석하는 단위가 다르다.

- `recv_multishot + IORING_RECVSEND_BUNDLE`: `cqe->res`는 여러 contiguous slot을 합친 총 바이트 수이고, `cqe->flags`의 bid는 **첫 slot만** 알려 준다. 공식 문서 기준 bundle receive는 kernel 6.10+에서 제공된다.
- `recvmsg_multishot`: `cqe->res`는 payload 바이트 수가 아니라 `struct io_uring_recvmsg_out` header + name + control + payload가 들어간 **window 길이**다. multishot recvmsg 자체는 kernel 6.0+부터 쓸 수 있다.
- `IORING_CQE_F_MORE`: multishot request generation이 계속 살아 있다는 뜻이다.
- `IORING_CQE_F_BUF_MORE`: 현재 tail buffer slot이 아직 완전히 소비되지 않아, 같은 slot이 뒤 CQE에서도 이어질 수 있다는 뜻이다.
- `io_uring_buf_ring_head()`: kernel이 다음에 소비할 slot index를 조회하는 resync API다. `IORING_REGISTER_PBUF_STATUS` 기반 조회는 kernel 6.8+에서 가능하다.
- `io_uring_buf_ring_available()`: free count의 시점값일 뿐이며 inflight I/O가 있으면 본질적으로 racy하다. 이 helper 역시 6.8+ 기준으로 보는 편이 맞다.

핵심 오해는 보통 여기서 나온다.

- `bid`만 알면 어느 버퍼를 recycle할지 결정할 수 있다고 생각한다.
- `!IORING_CQE_F_MORE`만 보면 shutdown이 끝났다고 생각한다.
- CQE를 읽은 시점과 payload 소비 완료 시점을 같은 것으로 취급한다.

실제로는 `kernel이 소비한 slot`, `app이 아직 붙잡고 있는 slot`, `다음에 재공급 가능한 slot`이 서로 다른 상태다.

## 깊이 들어가기

### 1. `F_MORE`와 `F_BUF_MORE`는 서로 다른 질문에 답한다

| 신호 | 범위 | 의미 | 잘못 해석하면 생기는 문제 |
|------|------|------|---------------------------|
| `IORING_CQE_F_MORE` | request generation | 같은 multishot arm에서 CQE가 더 올 수 있다 | cancel/shutdown 직후 premature close |
| `IORING_CQE_F_BUF_MORE` | 현재 tail buffer slot | 같은 slot이 아직 완전히 소비되지 않았다 | partial slot 중복 recycle |
| `IORING_CQE_F_BUFFER` + bid | buffer identity | 이번 CQE가 참조한 시작 slot을 알려 준다 | bundle 폭을 bid 하나로 오해 |

둘은 독립적이다. 특히 incremental consumption 자체는 `IOU_PBUF_RING_INC`가 도입된 kernel 6.12+ semantics를 전제로 해야 한다.

- `!F_MORE`여도 마지막 slot에 대한 app-owned cleanup은 남아 있을 수 있다.
- `F_BUF_MORE`는 request 생존 여부가 아니라 **slot 재사용 금지** 신호다.
- incremental ring에서는 `res == 0`이어도 `F_BUF_MORE`가 설 수 있으므로, EOF나 shutdown만 보고 slot을 되돌리면 안 된다.

### 2. bundle recv는 "첫 bid + 총 바이트 수"만 준다

공식 `io_uring_prep_recv(3)` 문서에서 `IORING_RECVSEND_BUNDLE`은 다음 계약을 갖는다.

- `cqe->res`: 이번 CQE가 받은 총 바이트 수
- `cqe->flags`의 bid: 이번 bundle의 첫 buffer ID
- 실제로 소비된 buffer는 ring 안에서 **contiguous** 하다
- CQE에는 "ring 안의 몇 번째 slot까지 갔는지"가 직접 실리지 않는다

그래서 fast path에서는 per-ring `cached_head`가 필요하다.

- `cached_head`: kernel이 다음에 소비할 slot이라고 앱이 믿는 로컬 index
- CQE를 처리할 때는 `cached_head`에서 시작해 `cqe->res` bytes가 소진될 때까지 slot들을 걷는다
- full slot은 `cached_head`를 앞으로 밀 수 있지만, `F_BUF_MORE`가 켜진 tail slot은 아직 head에 남겨 둬야 한다

이 규칙을 표로 정리하면:

| 모드 | head가 언제 전진하는가 |
|------|------------------------|
| 일반 provided ring | slot 하나가 CQE로 handed off 되면 `+1` |
| bundle recv | fully-consumed slot 수만큼 전진 |
| incremental ring + `F_BUF_MORE` | partially-consumed tail slot에서는 멈춤 |
| bundle + incremental ring | full slot들은 건너뛰고, 마지막 partial tail slot에서 멈춤 |

이 때문에 `recvsend_bundle-inc.c`처럼 `F_BUF_MORE`가 반복되는 테스트에서 같은 bid가 계속 보이는 것은 이상 현상이 아니다. 아직 kernel의 next-to-consume head가 그 slot을 떠나지 않았기 때문이다.

### 3. recycle은 `cached_head`가 아니라 ownership ledger로 결정한다

`cached_head`는 kernel 소비 순서를 설명하지만, recycle 가능 시점을 직접 말해 주지 않는다.

분리해서 봐야 할 상태:

- `kernel-owned`: 아직 `F_BUF_MORE`가 켜져 있거나, 같은 generation의 뒤 CQE가 이 slot을 이어 쓸 수 있는 상태
- `app-owned`: CQE로 handed off 되었지만 payload parser, decoder, worker queue가 아직 붙잡고 있는 상태
- `recyclable`: app 후속 처리가 끝나 `io_uring_buf_ring_add()`로 되돌릴 수 있는 상태

즉 `cached_head`는 "커널이 어디까지 가져갔는가"이고, recycle ledger는 "앱이 무엇을 끝냈는가"다. 둘을 합치면 partial drain에서 바로 사고가 난다.

실전 의사 코드는 보통 이런 모양이 된다.

```text
on_cqe(cqe):
  if !(cqe.flags & IORING_CQE_F_BUFFER):
    handle_terminal_or_error()
    return

  bytes = cqe.res
  slot  = cached_head
  off   = slot_offset[slot]   // incremental tail이면 0이 아닐 수 있다

  while bytes > 0:
    take = min(bytes, slot_size - off)
    handoff_window(slot, off, take)
    bytes -= take
    off   += take

    if bytes == 0 && (cqe.flags & IORING_CQE_F_BUF_MORE):
      slot_offset[slot] = off
      mark_kernel_owned(slot)
      break

    slot_offset[slot] = 0
    mark_app_owned(slot)
    slot = next_slot(slot)
    off  = 0

  cached_head = slot
```

중요한 점은 마지막 branch다.

- `F_BUF_MORE`가 켜져 있으면 마지막 slot은 CQE를 읽었다고 해서 recycle 후보가 되지 않는다.
- `bytes == 0`이더라도 그 slot을 app이 임의로 `buf_ring_add()` 하면 kernel과 앱이 같은 backing memory를 동시에 보게 된다.
- 여기서 `handoff_window()`는 "bid 전체를 앱에 넘겼다"가 아니라 `(slot, off, len)` window reference를 만든다는 뜻이다. `IOU_PBUF_RING_INC`가 켜지면 같은 bid 안에 **app이 읽을 수 있는 앞부분**과 **kernel이 이어서 채울 뒷부분**이 동시에 존재할 수 있다.

### 4. burst receive에서 low-water는 "free bid 개수"가 아니라 "다음 recycle 전까지 버틸 byte headroom"이다

bundle도 incremental ring도 없을 때는 low-water를 free bid count로 잡아도 대략 맞는다. 하지만 `IORING_RECVSEND_BUNDLE`과 `IOU_PBUF_RING_INC`가 들어오면 CQE 수, bid 수, byte headroom이 서로 분리된다.

- bundle: CQE 1개가 contiguous bid 여러 개를 한 번에 소모할 수 있다. 그래서 `pending CQE 수`나 `recv arm 수`는 low-water 계산의 분모가 아니다.
- incremental: 현재 `F_BUF_MORE` tail bid는 free bid가 아니지만, 그 안의 남은 공간은 다음 burst를 흡수할 byte headroom이다.
- liburing `io_uring_prep_recv(3)` 문서가 말하듯 bundle receive는 첫 recv가 덜 가져가고 뒤 recv가 더 많은 buffer를 가져갈 수 있다. 그래서 low-water는 "이번 CQE 폭"이 아니라 "**다음 CQ drain 전 소켓이 더 밀어 넣을 수 있는 bytes**"로 잡는 편이 안전하다.

운영에 필요한 상태는 최소한 이 정도다.

- `slot_size`
- `visible_free_bids`
- `tail_room_bytes = F_BUF_MORE tail ? slot_size - tail_offset : 0`
- `burst_bytes_budget`: 다음 recycle/CQ drain 전에 더 들어올 수 있다고 보는 byte budget
- `recycle_jitter_bids`: app queue/CQ lag 때문에 즉시 못 돌려줄 reserve

실전 계산은 보통 "bytes를 먼저 보고, 마지막에 bid로 환산"하는 식이 된다.

```text
new_bids_needed =
  max(0, ceil((burst_bytes_budget - tail_room_bytes) / slot_size))

effective_free_bids =
  visible_free_bids - new_bids_needed - recycle_jitter_bids
```

해석:

- `effective_free_bids < 0`: 다음 burst를 그대로 받으면 `-ENOBUFS`나 late throttle 가능성이 높다. 새 recv rearm, shard intake, poll-first 경로를 눌러야 한다.
- `effective_free_bids == 0`: `available()`은 아직 양수여도 사실상 reserve가 없다.
- `tail_room_bytes > 0`인데 `available()`만 보면 지나치게 비관적이 된다. 반대로 bundle 폭을 `1 CQE ~= 1 bid`로 보면 지나치게 낙관적이 된다.

예를 들면:

- `slot_size = 4096`
- `visible_free_bids = 4`
- 현재 partial tail offset = `3072` -> `tail_room_bytes = 1024`
- 다음 CQ drain 전 `burst_bytes_budget = 12288`
- `recycle_jitter_bids = 1`

```text
new_bids_needed = ceil((12288 - 1024) / 4096) = 3
effective_free_bids = 4 - 3 - 1 = 0
```

즉 `available() == 4`라서 여유로워 보여도, 실제로는 다음 bundle burst 하나면 reserve를 모두 태운다.

### 5. `IOU_PBUF_RING_INC`가 켜지면 ownership 단위가 `bid`에서 `window + tail state`로 쪼개진다

plain provided ring에서는 CQE에 찍힌 `bid`를 곧바로 "앱이 받은 buffer"로 이해해도 큰 문제가 없는 경우가 많다. 하지만 incremental ring에서는 CQE가 `bid` 전체가 아니라 그 안의 **byte window**만 앱에 넘기고, `bid` 자체는 계속 kernel-owned일 수 있다.

| ledger 단위 | 의미 | recycle 가능 조건 |
|------|------|-------------------|
| `window(bid, off, len)` | 이번 CQE가 앱에 handed off 한 실제 byte 범위 | 해당 window를 참조하는 parser/worker가 끝나야 함 |
| `kernel-owned partial bid` | `F_BUF_MORE`가 켜져 뒤 CQE가 같은 bid를 이어 쓸 수 있는 상태 | 불가 |
| `app-owned full bid` | slot 전체가 CQE들로 완전히 소비되어 더 이상 커널이 덧쓰지 않는 상태 | 모든 window 소비 완료 후 가능 |

`IORING_RECVSEND_BUNDLE`까지 합치면 CQE 하나가 세 가지 ownership을 동시에 만들 수 있다.

예를 들어 `slot_size = 4096`, 직전 CQE가 bid 40을 3072바이트까지 채워 둔 상태에서 다음 bundle CQE가 `res = 11264`, `F_BUF_MORE = 1`로 오면:

1. bid 40의 남은 1024바이트를 먼저 마저 채운다 -> bid 40은 이제 `app-owned full bid`
2. bid 41, 42는 각각 4096바이트씩 꽉 찬다 -> 둘도 `app-owned full bid`
3. bid 43의 앞 2048바이트만 사용한다 -> bid 43은 여전히 `kernel-owned partial bid`

즉 같은 CQE라도:

- `flags`에 찍힌 첫 bid 40은 "이번 CQE가 건드린 첫 cursor"일 뿐이다.
- 실제 recycle 후보는 40, 41, 42일 수 있지만, 43은 `F_BUF_MORE`가 꺼질 때까지 금지다.
- 다음 CQE가 다시 같은 bid 43을 들고 와도 double-assign이 아니라 partial consume continuation일 수 있다.

운영적으로는 `bid -> owner` 단일 맵보다 아래 두 ledger가 더 안전하다.

- `per_bid_state`: `kernel_partial | app_full | free`
- `per_window_ref`: `(bid, off, len, consumer_count)`

그래야 "같은 bid가 또 왔다"를 정상 partial reuse와 진짜 bookkeeping corruption으로 나눌 수 있다.

### 예시 1. partial tail 위로 bundle CQE가 이어 붙는 경우

아래 예시는 `slot_size = 4096`, ring slot `0..7`이 각각 bid `40..47`에 대응된다고 가정한다. 직전 CQE가 bid 40의 앞 `3072`바이트를 넘기고 `F_BUF_MORE=1`로 끝났다면, 새 CQE를 보기 직전 상태는 이렇게 읽는 편이 맞다.

| slot | bid | 새 CQE 직전 상태 |
|------|-----|------------------|
| 0 | 40 | `cached_head`가 가리키는 current tail, app은 `window(40, 0, 3072)`를 들고 있고 kernel은 뒤 `1024`바이트를 더 채울 수 있다 |
| 1 | 41 | free |
| 2 | 42 | free |
| 3 | 43 | free |

이때 새 bundle CQE가 아래처럼 왔다고 보자.

```text
first_bid = 40
res       = 11264
flags     = BUFFER | MORE | BUF_MORE
```

`cached_head=40`, `tail_offset[40]=3072`에서 시작해 `res`를 걷으면 contiguous span은 아래처럼 복원된다.

| bid | 이번 CQE가 넘긴 window | 이번 CQE 후 bid 상태 | 설명 |
|-----|------------------------|----------------------|------|
| 40 | `(40, 3072, 1024)` | `app_full` | 이전 CQE의 앞 `3072`바이트와 합쳐 slot 전체가 app 쪽으로 넘어왔다 |
| 41 | `(41, 0, 4096)` | `app_full` | full slot |
| 42 | `(42, 0, 4096)` | `app_full` | full slot |
| 43 | `(43, 0, 2048)` | `kernel_partial` | tail slot, 뒤 `2048`바이트는 아직 kernel-owned |

이 한 CQE로 얻는 결론은 세 가지다.

- CQE에 찍힌 bid는 40 하나지만, 실제 contiguous bundle span은 `40 -> 43`이다.
- `cached_head`는 full slot 세 개를 지나 `43`까지 전진하고, `F_BUF_MORE` 때문에 거기서 멈춘다.
- recycle 판단은 `cached_head`가 아니라 ownership ledger로 한다. bid 40은 head가 이미 지나갔어도 이전 `window(40, 0, 3072)` 소비가 안 끝났으면 아직 못 돌린다.

즉 bundle + incremental에서는 "첫 bid 40을 봤다"가 아니라 "`cached_head=40`에서 `11264`바이트를 걷자 full bid 세 개와 partial tail 하나가 생겼다"로 읽어야 맞다.

### 예시 2. 같은 bid가 다음 bundle CQE의 `first_bid`로 다시 오는 경우

예시 1 직후라면 `cached_head=43`, `tail_offset[43]=2048`이다. 이제 다음 CQE가 아래처럼 오면:

```text
first_bid = 43
res       = 3584
flags     = BUFFER | MORE | BUF_MORE
```

이번 span은 `43 -> 44`다.

| bid | 이번 CQE가 넘긴 window | 이번 CQE 후 bid 상태 | 설명 |
|-----|------------------------|----------------------|------|
| 43 | `(43, 2048, 2048)` | `app_full` | 예시 1에서 남았던 tail을 이번 CQE가 마저 넘긴다 |
| 44 | `(44, 0, 1536)` | `kernel_partial` | 새 partial tail, 뒤 `2560`바이트는 아직 kernel-owned |

이 상황에서 `first_bid=43`이 다시 나오는 것은 bookkeeping corruption이 아니라 정상 continuation이다.

- 예시 1에서는 bid 43이 `kernel_partial`이었다.
- 예시 2는 그 남은 tail부터 이어서 읽기 때문에 첫 bid가 다시 43으로 보인다.
- `cached_head`는 이번 CQE 후 `44`로 이동하고, 다음 CQE도 bid 44부터 시작할 수 있다.

여기서 단일 `bid -> owner` 맵만 있으면 "43은 이미 본 bid인데 왜 또 나오지?"라는 오진이 생긴다. 반대로 `per_window_ref`를 같이 두면 정상 흐름으로 해석된다.

- 예시 1이 만든 `window(43, 0, 2048)`
- 예시 2가 추가한 `window(43, 2048, 2048)`

둘이 합쳐져서 bid 43이 이제야 `app_full`이 된다. 즉 "같은 bid가 반복됐다"가 아니라 "같은 bid 안의 다음 window가 handed off 됐다"가 정확한 설명이다.

### 예시 3. recycle 가능 시점은 `cached_head` 순서와 다를 수 있다

예시 2 직후 ownership ledger를 단순화하면 아래처럼 볼 수 있다.

| bid | kernel 상태 | app window ref 상태 | 지금 바로 recycle 가능? |
|-----|-------------|---------------------|--------------------------|
| 40 | none | `window(40, 0, 3072)`, `window(40, 3072, 1024)` outstanding | 아니오 |
| 41 | none | `window(41, 0, 4096)` outstanding | app이 끝내면 가능 |
| 42 | none | `window(42, 0, 4096)` outstanding | app이 끝내면 가능 |
| 43 | none | `window(43, 0, 2048)`, `window(43, 2048, 2048)` outstanding | app이 끝내면 가능 |
| 44 | `kernel_partial`, tail offset `1536` | `window(44, 0, 1536)` outstanding | 아니오 |

이제 worker가 out-of-order로 소비를 끝낸다고 가정해 보자.

1. worker가 bid 41을 먼저 완료하면, bid 41은 `cached_head=44`보다 뒤가 아니라 앞에 있더라도 바로 `ready_to_readd`가 될 수 있다.
2. worker가 bid 44의 visible window `(44, 0, 1536)`를 먼저 끝내도, `F_BUF_MORE` tail이 남아 있으므로 bid 44는 여전히 recycle 금지다.
3. 반대로 bid 40은 `cached_head`가 한참 지나간 오래된 bid여도, 초기 `3072`바이트 window가 아직 parser에 남아 있으면 계속 app-owned다.

여기서 중요한 분리는 다음과 같다.

- `cached_head`: kernel이 다음에 어디서 이어 받을지
- contiguous bundle span: 이번 CQE가 실제로 어느 bid 범위를 건드렸는지
- per-bid ownership: 각 bid가 `kernel_partial`, `app_full`, `ready_to_readd` 중 어디에 있는지

셋을 분리하지 않으면 아래 오판이 나온다.

- `cached_head`가 44니까 40~43은 전부 recycle 가능하다고 생각한다.
- bid 44의 visible `1536`바이트를 app이 읽었으니 바로 `buf_ring_add(44)` 해도 된다고 생각한다.
- bid 41이 먼저 끝났는데도 "head보다 앞선 slot은 순서대로만 돌려야 한다"고 생각한다.

CQ overflow나 worker handoff 중 이런 ledger를 잃어버렸다면, 현재 `kernel_head`만으로 과거 span을 역산하려고 하지 말고 [io_uring provided-buffer ring head resync after CQ overflow, partial drains, worker handoff](./io-uring-provided-buffer-ring-head-resync-cq-overflow-worker-handoff.md) 문서의 `freeze -> drain -> query -> reconcile -> resume` 절차로 넘어가는 편이 안전하다.

### 6. `recvmsg_multishot`는 `res`를 바로 payload 길이로 읽으면 틀린다

공식 `io_uring_prep_recvmsg(3)`와 `io_uring_recvmsg_out(3)` 기준으로, multishot recvmsg는 CQE가 가리키는 window 앞부분에 `struct io_uring_recvmsg_out` header를 붙인다.

따라서 `recvmsg_multishot` CQE 해석 절차는 보통 다음 순서를 따른다.

1. window 시작 주소를 구한다.
2. `io_uring_recvmsg_validate(window, cqe->res, &msgh)`로 header를 검증한다.
3. `io_uring_recvmsg_name()`, `io_uring_recvmsg_cmsg_firsthdr()`, `io_uring_recvmsg_payload()`로 하위 영역을 꺼낸다.
4. 실제 payload 길이는 `io_uring_recvmsg_payload_length()` 또는 `o->payloadlen`로 따로 계산한다.

즉 `cqe->res`는 payload bytes가 아니다.

- `io_uring_recvmsg_validate()`는 header와 제출 당시 `msghdr`가 예약한 name/control layout이 맞는지만 검증한다.
- handoff할 실제 byte 수는 `io_uring_recvmsg_payload_length()`로 계산하고, "논리적으로 payload가 0인가"는 `o->payloadlen == 0`으로 따로 본다.
- 따라서 `payload_length() == 0`과 `o->payloadlen == 0`은 같은 질문이 아니다. 전자는 이번 window 안에서 앱이 바로 읽을 수 있는 payload bytes, 후자는 `recvmsg(2)` 관점의 payload 길이다.
- header-only CQE도 가능하다.
- liburing `examples/proxy.c`는 `msg_namelen == 0`, `msg_controllen == 0`인 recvmsg multishot path에서 `res == sizeof(struct io_uring_recvmsg_out)`를 "zero receive"처럼 다룬다.
- terminal error CQE는 대개 `F_BUFFER`가 없으므로, buffer recycle을 그 경로에 붙이면 안 된다.

주의할 점 하나가 더 있다.

- 공식 man page는 `IORING_RECVSEND_BUNDLE`을 `recv` 쪽에 문서화하지만 `recvmsg` 쪽에는 같은 설명을 두지 않는다.
- 그래서 `recvmsg_multishot`는 bundle 폭 계산보다, `recvmsg_out` header parsing과 per-window recycle discipline을 먼저 맞추는 것이 안전하다.

incremental ring까지 같이 쓰는 경우에는 window 시작점도 buffer base가 아니라 `slot_addr + current_offset`일 수 있다. 이때 `io_uring_recvmsg_validate()`는 전체 backing buffer가 아니라 **이번 CQE window**를 기준으로 호출해야 한다.

```text
window = slot_addr + slot_offset_before_this_cqe
o = io_uring_recvmsg_validate(window, cqe.res, &msgh)
payload = io_uring_recvmsg_payload(o, &msgh)
payload_len = io_uring_recvmsg_payload_length(o, cqe.res, &msgh)
```

여기서 zero-payload와 header-only를 더 분리해 두면 mixed recv/recvmsg 진단이 훨씬 덜 흔들린다.

| CQE shape | recvmsg 쪽 정상 해석 | 진단상 주의점 |
|------|----------------------|---------------|
| `res == sizeof(struct io_uring_recvmsg_out)` and `msg_namelen == msg_controllen == 0` | header-only + zero-payload CQE | plain `recv`의 `res == 0`와 같은 층위로 normalize할 수 있지만, raw `res`는 0이 아니다 |
| `res > sizeof(...)`, `o->payloadlen == 0`, `payload_length() == 0` | zero-payload지만 name/control reservation은 포함된 CQE | "payload가 있는데 bytes accounting이 틀렸다"가 아니라 control-only or zero-length payload일 수 있다 |
| `payload_length() == 0`, `o->payloadlen > 0` | payload는 논리적으로 있었지만 이번 window에서 usable payload가 0 | zero-payload/EOF가 아니라 truncation 또는 layout mismatch 쪽을 먼저 본다 |

즉 recvmsg multishot에서 "zero"를 판정하는 기준은 보통 다음 순서가 더 안전하다.

1. `io_uring_recvmsg_validate()`가 성공하는지 본다.
2. `logical_payload_zero = (o->payloadlen == 0)`를 계산한다.
3. `visible_payload_len = io_uring_recvmsg_payload_length(...)`를 계산한다.
4. `header_only = logical_payload_zero && visible_payload_len == 0 && cqe->res == sizeof(struct io_uring_recvmsg_out) && msgh.msg_namelen == 0 && msgh.msg_controllen == 0`를 별도 태그로 둔다.

이렇게 해 두면 mixed path에서 아래 오판을 줄일 수 있다.

- plain `recv` 기준 `res == 0` heuristic를 recvmsg CQE에 그대로 적용한다.
- header-only CQE를 parse failure나 stray metadata로 버린다.
- `payload_length() == 0`만 보고 EOF라고 단정한다.

### 7. mixed `recv`/`recvmsg` 경로는 "logical payload bytes"를 먼저 맞춘 뒤 EOF와 `F_BUF_MORE`를 본다

plain `recv`와 `recvmsg_multishot`를 같은 dashboard나 ownership ledger로 합치면, raw `cqe->res` 기준 진단은 금방 깨진다.

- plain `recv` 계열: `logical_payload_bytes = cqe->res`
- `recvmsg_multishot`: `logical_payload_bytes = o->payloadlen`, `visible_payload_bytes = io_uring_recvmsg_payload_length(...)`

즉 mixed path에서는 먼저 둘을 같은 단위로 normalize한 뒤 EOF-like 분기를 태우는 편이 안전하다.

```text
if recvmsg_multishot:
  o = io_uring_recvmsg_validate(window, cqe.res, &msgh)
  logical_payload = o->payloadlen
  visible_payload = io_uring_recvmsg_payload_length(o, cqe.res, &msgh)
  zero_payload = (logical_payload == 0)
else:
  logical_payload = cqe.res
  visible_payload = cqe.res
  zero_payload = (cqe.res == 0)

if zero_payload && (cqe.flags & IORING_CQE_F_BUF_MORE):
  classification = SAME_BID_CONTINUATION
elif zero_payload && !(cqe.flags & IORING_CQE_F_MORE):
  classification = STREAM_EOF_OR_TERMINAL_ZERO
else:
  classification = DATA_OR_CONTROL_ONLY
```

이 의사 코드는 운영 해석을 단순화한 것이다. 실제 판정에서는 socket type을 같이 봐야 한다.

- stream/socketpair/pipe 계열에서는 `zero_payload && !F_BUF_MORE`가 EOF-like signal일 수 있다.
- datagram 계열에서는 zero-length payload 자체가 정상 message일 수 있으므로, 같은 모양을 EOF로 부르면 안 된다.
- 어떤 경우든 `F_BUF_MORE=1`이면 same-`bid` cursor는 아직 열려 있으므로, zero-payload/header-only CQE라도 tail recycle은 미뤄야 한다.

즉 `F_BUF_MORE`는 recvmsg header 유무와 무관하게 여전히 buffer lifecycle flag다. "payload가 0이었다"와 "same bid가 retire되었다"는 질문을 합치면 mixed path diagnostics가 다시 틀어진다.

### 8. partial drain에서는 CQ advancement와 buffer return count가 더 크게 벌어진다

CQ consumer가 CQE를 읽었다고 해서, 그 CQE가 참조한 slot 수만큼 바로 buffer ring에 돌려줄 수 있는 것은 아니다.

대표적인 경우:

- CQ thread는 CQE만 분류하고 실제 payload 소비는 worker thread가 한다
- bundle CQE는 slot 3개를 handed off 했지만, 그중 마지막 slot은 `F_BUF_MORE` 때문에 아직 kernel-owned다
- shutdown 중이라 CQE는 비우되 재arm은 막아야 한다

이럴 때는 `CQ advance 수`와 `buffer return 수`를 분리해야 한다.

- 같은 수로 움직일 수 있으면 `io_uring_buf_ring_cq_advance()`가 가장 싸다
- 다르면 `__io_uring_buf_ring_cq_advance()` 또는 별도 `io_uring_cq_advance()` + `io_uring_buf_ring_advance()`를 써야 한다

특히 bundle + incremental 조합에서는 CQE 1개가 다음 셋 중 아무거나 만들 수 있다.

- `cq +1, buf +0`: tail bid는 아직 kernel-owned이고, full bid도 app queue가 아직 들고 있다
- `cq +1, buf +(N-1)`: `N`개 slot을 건드렸지만 마지막 tail slot은 `F_BUF_MORE` 때문에 제외된다
- `cq +1, buf +N`: 모든 touched bid가 full-consume 되었고, 앱도 inline으로 바로 release한다

즉 `CQE 수 == recycle 가능한 bid 수`라는 가정은 burst가 커질수록 더 자주 깨진다.

`io_uring_buf_ring_head()`는 이런 상황에서 resync 용도로 유용하다.

- CQ 일부를 다른 스레드가 먹어 로컬 `cached_head`를 잃어버렸다
- crash recovery나 hot restart 직후 ring 상태를 다시 맞춰야 한다
- shutdown drain 중 "kernel이 어디까지 소비했는지"를 마지막으로 확인하고 싶다

하지만 `buf_ring_head()`로 알 수 있는 것은 kernel head뿐이다. 그 값만으로 app-owned buffer가 끝났다고 결론 내리면 안 된다.

### 9. shutdown과 cancel은 `request 종료`와 `buffer tail 정리`를 둘 다 기다려야 한다

[io_uring multishot cancel, rearm, drain, shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md) 문서의 핵심은 `!IORING_CQE_F_MORE`가 generation 종료 기준이라는 점이다. 여기서 provided buffers까지 더하면 종료 규칙이 한 단계 더 생긴다.

shutdown 순서:

1. 새 recv rearm을 먼저 금지한다.
2. 필요하면 active multishot recv generation을 cancel한다.
3. cancel CQE만 보지 말고 `!IORING_CQE_F_MORE` terminal CQE까지 drain한다.
4. 그동안 outstanding slot ledger를 보며 `kernel-owned`와 `app-owned`를 분리한다.
5. `app-owned` slot만 후속 처리 완료 시 recycle한다.
6. terminal CQE를 확인하고, `F_BUF_MORE` tail state가 더 이상 없을 때만 fd/ring teardown으로 넘어간다.

특히 조심해야 할 branch:

- `-ENOBUFS`: 현재 generation이 끝났다는 뜻이지, app이 보유한 slot이 자동으로 free됐다는 뜻이 아니다
- `res == 0`: EOF처럼 보여도 incremental ring에서는 `F_BUF_MORE`를 같이 봐야 한다
- `recvmsg` header-only CQE: payload가 0이어도 window 자체는 실제 CQE payload이므로, parse/recycle 규칙을 동일하게 적용해야 한다
- `recvmsg` zero-payload CQE: raw `res`가 0이 아닐 수 있으므로, shutdown 진단은 `o->payloadlen == 0`로 normalize한 뒤 `F_BUF_MORE`를 같이 봐야 한다

정리하면:

- `!F_MORE`는 "이 multishot arm은 끝났다"
- `!F_BUF_MORE`는 "이 tail slot은 더 이상 kernel-owned가 아니다"

두 조건이 모두 맞아야 shutdown 중 recycle/teardown 판단이 안전해진다.

## 운영 체크리스트

- `bid` 하나로 bundle 폭을 추정하지 말고, ring geometry와 `cached_head`로 slot 범위를 계산한다.
- low-water는 `available()` count만 보지 말고 `tail_room_bytes + visible_free_bids * slot_size`를 burst byte budget으로 다시 환산해서 잡는다.
- incremental ring에서는 `bid` 하나가 아니라 `(bid, off, len)` window와 `per_bid_state`를 함께 기록한다.
- `io_uring_buf_ring_available()`는 capacity 경보용으로만 보고, recycle 근거로 쓰지 않는다.
- incremental ring에서는 `F_BUF_MORE`가 꺼질 때까지 tail slot을 re-add 하지 않는다.
- bundle + incremental에서는 `io_uring_buf_ring_cq_advance()`를 기본값으로 두지 말고, `cq_count != buf_count`가 흔하다는 전제로 helper를 고른다.
- `recvmsg_multishot`는 항상 `io_uring_recvmsg_validate()`로 해석하고, `cqe->res`를 payload bytes로 직접 쓰지 않는다.
- mixed `recv`/`recvmsg` 계측에서는 raw `cqe->res`와 `logical_payload_bytes`를 분리해 기록한다.
- `recvmsg` zero-payload/EOF 진단은 `o->payloadlen == 0`, `payload_length()`, `F_BUF_MORE`, socket type을 함께 본다.
- shutdown/cancel 중에는 `terminal !F_MORE` CQE와 outstanding tail fragment 정리를 모두 끝낸 뒤에만 fd/ring을 닫는다.

## 꼬리질문

> Q: bundle recv에서는 왜 `bid`만으로는 recycle 대상을 정할 수 없나요?
> 핵심: CQE는 첫 slot만 알려 주고 bundle 폭은 `res`에만 담기므로, contiguous slot 범위는 `cached_head`와 buffer 크기로 다시 계산해야 하기 때문이다.

> Q: `!IORING_CQE_F_MORE`면 tail buffer도 바로 재사용해도 되나요?
> 핵심: 아니다. `F_MORE`는 request 종료 신호이고 `F_BUF_MORE`는 slot 종료 신호라서, tail slot은 별도로 확인해야 한다.

> Q: `recvmsg_multishot`에서 `cqe->res == 0`만 보면 되나요?
> 핵심: 아니다. multishot recvmsg는 header-only completion이 가능하므로 `io_uring_recvmsg_out`를 기준으로 해석해야 한다.

> Q: `recvmsg_multishot`에서 `res == sizeof(struct io_uring_recvmsg_out)`면 항상 EOF인가요?
> 핵심: 아니다. `msg_namelen`과 `msg_controllen`이 0인 경로에서는 header-only zero-payload CQE일 뿐이다. stream path에서는 zero receive처럼 normalize할 수 있지만, `F_BUF_MORE`와 socket type을 같이 봐야 한다.

> Q: `io_uring_recvmsg_payload_length() == 0`이면 그냥 zero-payload로 처리해도 되나요?
> 핵심: `o->payloadlen`도 같이 봐야 한다. `payload_length() == 0 && o->payloadlen > 0`이면 EOF보다 truncation/layout mismatch 쪽이 더 가깝다.

> Q: `io_uring_buf_ring_head()`가 있으면 로컬 head cache는 필요 없나요?
> 핵심: 아니다. `buf_ring_head()`는 resync API이고, fast path에서 bundle 폭과 tail fragment를 계산하려면 per-CQE 로컬 accounting이 여전히 필요하다.

> Q: `io_uring_buf_ring_available()`가 4면 slot 4개 분량을 안전하게 더 받을 수 있다는 뜻인가요?
> 핵심: 아니다. `F_BUF_MORE` tail 안의 남은 바이트는 free bid count에 안 잡히고, bundle은 CQE 하나가 여러 bid를 먹을 수 있으므로 bytes -> bids 환산을 다시 해야 한다.

> Q: CQE에 `bid`가 찍혔으면 그 bid 전체를 recycle 후보로 봐도 되나요?
> 핵심: incremental ring에서는 아니다. CQE가 넘긴 것은 `bid` 전체가 아니라 그 안의 byte window일 수 있고, `F_BUF_MORE`가 남아 있으면 bid 자체는 여전히 kernel-owned다.

## 참고 소스

- [`io_uring_prep_recv(3)` in liburing](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_recv.3)
- [`io_uring_prep_recvmsg(3)` in liburing](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_recvmsg.3)
- [`io_uring_recvmsg_out(3)` in liburing](https://github.com/axboe/liburing/blob/master/man/io_uring_recvmsg_out.3)
- [`io_uring_setup_buf_ring(3)` in liburing](https://github.com/axboe/liburing/blob/master/man/io_uring_setup_buf_ring.3)
- [`io_uring_buf_ring_available(3)` in liburing](https://github.com/axboe/liburing/blob/master/man/io_uring_buf_ring_available.3)
- [`io_uring_buf_ring_cq_advance(3)` in liburing](https://github.com/axboe/liburing/blob/master/man/io_uring_buf_ring_cq_advance.3)
- [`io_uring_register(2)` in liburing, `IORING_REGISTER_PBUF_STATUS`](https://github.com/axboe/liburing/blob/master/man/io_uring_register.2)
- [`io_uring(7)` in liburing, CQE flag semantics](https://github.com/axboe/liburing/blob/master/man/io_uring.7)
- [`examples/proxy.c` in liburing](https://github.com/axboe/liburing/blob/master/examples/proxy.c)
- [`test/recvsend_bundle.c` in liburing](https://github.com/axboe/liburing/blob/master/test/recvsend_bundle.c)
- [`test/recvsend_bundle-inc.c` in liburing](https://github.com/axboe/liburing/blob/master/test/recvsend_bundle-inc.c)
- [`test/read-inc-buf-more.c` in liburing](https://github.com/axboe/liburing/blob/master/test/read-inc-buf-more.c)
- [`test/recv-multishot.c` in liburing](https://github.com/axboe/liburing/blob/master/test/recv-multishot.c)

## 한 줄 정리

bundle-mode `recv`는 slot 범위를 `cached_head`로 복원해야 하고, burst receive에서는 low-water를 free-bid count가 아니라 `tail_room + bundle burst bytes`로 계산해야 한다. `IOU_PBUF_RING_INC`가 켜지면 CQE는 `bid` 전체가 아니라 byte window를 넘길 수 있으므로, `F_MORE`와 `F_BUF_MORE`, `per_bid_state`, `per_window_ref`를 분리해서 본 뒤에만 recycle과 teardown을 진행해야 한다.
