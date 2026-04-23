# io_uring send bundle, zerocopy notification, fixed-buffer completion accounting

> 한 줄 요약: `io_uring_prep_send_bundle()`은 "SQE 하나 = CQE 하나"가 아니라 **contiguous provided buffer batch를 여러 data CQE로 나눠 배출할 수 있는 send-side multishot**에 가깝다. 각 data CQE의 `res`는 이번 batch에서 account된 바이트 수이고 `flags`의 `bid`는 그 batch의 시작 `bid`다. plain provided-buffer send bundle에서는 해당 batch의 ownership이 **그 CQE 시점에 곧바로 userspace로 돌아오며**, `IORING_CQE_F_MORE`는 "같은 SQE가 다음 bundle batch를 또 시작할 수 있다"는 뜻이지 tail buffer가 아직 kernel-owned라는 뜻이 아니다. 반대로 zerocopy send는 `IORING_CQE_F_NOTIF` notification이 와야 메모리를 재사용할 수 있고, fixed buffer send는 per-I/O 완료와 등록 슬롯 lifetime을 분리해서 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring recv bundle, recvmsg multishot, buffer-ring head recycling](./io-uring-recv-bundle-recvmsg-multishot-buffer-ring-head-recycling.md)
> - [io_uring Provided Buffer Rings, Fixed Buffers, Memory Pressure](./io-uring-provided-buffers-fixed-buffers-memory-pressure.md)
> - [io_uring Operational Hazards, Registered Resources, SQPOLL](./io-uring-operational-hazards-registered-resources-sqpoll.md)
> - [io_uring Cancel Scope with Fixed Files and Mixed recv/send/poll Paths](./io-uring-cancel-scope-fixed-files-mixed-ops.md)
> - [io_uring recv multishot, send/sendmsg, zerocopy notification teardown ordering](./io-uring-recv-send-zerocopy-teardown-ordering.md)
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [mmap, sendfile, splice, zero copy](./mmap-sendfile-splice-zero-copy.md)

> retrieval-anchor-keywords: io_uring send bundle, io_uring send provided buffers, io_uring_prep_send_bundle, IORING_FEAT_RECVSEND_BUNDLE, send bundle CQE semantics, send bundle res bytes, send bundle starting bid, contiguous provided buffer send, send bundle cached head, send bundle reclaim rules, send bundle F_MORE, send bundle partial tail, provided buffer send ordering, IOSQE_BUFFER_SELECT send, IORING_CQE_F_BUFFER send, IORING_CQE_F_MORE send, IORING_CQE_F_NOTIF, zerocopy send notification, io_uring_prep_send_zc, io_uring send_zc fixed buffer, IORING_SEND_ZC_REPORT_USAGE, IORING_NOTIF_USAGE_ZC_COPIED, IORING_RECVSEND_FIXED_BUF, fixed buffer send lifetime, registered buffer send reuse, provided buffers versus fixed buffers

## 핵심 개념

send-side에서 제일 먼저 버려야 할 직관은 "`send bundle`은 recv bundle의 거울상일 뿐"이라는 생각이다. 비슷한 건 contiguous provided buffer를 한 번에 다룬다는 점까지고, completion 해석과 reclaim 규칙은 다르다.

- `io_uring_prep_send_bundle()`은 현재 `len=0`, `IOSQE_BUFFER_SELECT`, `sqe->buf_group`를 요구한다.
- current kernel send path는 bundle을 `send`에만 허용하고 `sendmsg` / `send_zc` 쪽 bundle은 받지 않는다.
- feature probe는 current liburing header 기준 `IORING_FEAT_RECVSEND_BUNDLE`로 본다. `io_uring_setup(2)` 문서도 이 feature가 send bundle과 send-side provided buffers를 같이 연다고 적는다.
- 커널 `io_uring/net.c`는 send bundle SQE에 내부적으로 `REQ_F_MULTISHOT`을 세운다. 그래서 **SQE 하나가 data CQE 여러 개를 낼 수 있다**.
- 각 data CQE의 `res`는 이번 CQE가 account한 **바이트 수**다. 일부 UAPI comment가 "buffer 수"처럼 읽히더라도, current kernel code / man page / liburing test는 모두 byte count로 사용한다.
- `IORING_CQE_F_BUFFER`의 upper bits는 이번 CQE가 account한 contiguous range의 **시작 `bid`**다. `bgid`가 아니다.
- plain provided-buffer send bundle에서는 현재 batch의 buffer ownership이 CQE 시점에 이미 app 쪽으로 돌아온다. `IORING_CQE_F_MORE`는 "같은 SQE가 다음 bundle batch를 자동으로 시작할 수 있다"는 뜻이다.
- zerocopy send는 다른 계약이다. data CQE 뒤에 `IORING_CQE_F_NOTIF` notification CQE가 와야 메모리를 재사용할 수 있다.
- fixed buffer send는 또 다른 계약이다. CQE가 끝내는 것은 **이번 I/O의 참조**이지 **등록 슬롯 자체**가 아니다.

핵심 오해는 보통 아래 셋이다.

- `F_MORE`면 마지막 tail buffer가 아직 kernel-owned라고 생각한다.
- send bundle data CQE만 받으면 zerocopy buffer도 바로 재사용한다고 생각한다.
- fixed buffer send가 끝나면 등록 슬롯도 즉시 free/unregister 가능하다고 생각한다.

## 깊이 들어가기

### 1. send bundle CQE는 "이번 batch가 끝났다"를 뜻한다

current kernel `io_uring/net.c` send path를 보면:

- bundle send는 내부적으로 multishot처럼 동작한다.
- `io_send_finish()`가 `io_put_kbufs()`로 현재 batch를 정산한 뒤 CQE를 올린다.
- `IORING_CQE_F_MORE`가 붙은 data CQE는 **같은 SQE가 다음 bundle batch를 또 시작할 예정**이라는 신호다.
- liburing `test/recvsend_bundle.c`도 `F_MORE`가 내려간 뒤에만 새 bundle SQE를 resubmit한다.

따라서 send bundle CQE 해석은 이렇게 잡는 편이 맞다.

| CQE 패턴 | 의미 | 앱이 해야 할 일 |
|------|------|-----------------|
| `res > 0`, `F_BUFFER=1`, `F_MORE=1` | 이번 batch는 account 완료, 같은 SQE가 다음 batch를 이어서 낼 수 있음 | 이번 CQE가 건드린 contiguous range를 정산하고, **새 SQE를 넣지 않고** 다음 CQE를 기다린다 |
| `res > 0`, `F_BUFFER=1`, `F_MORE=0` | 이번 batch 정산 + 이 SQE 종료 | range 정산 후, 아직 보낼 payload가 남았을 때만 새 SQE를 넣는다 |
| `res < 0`, `F_MORE=0` | 현재 SQE 실패/종료 | ownership ledger와 socket 상태를 같이 정산한다 |

중요한 차이는 recv incremental path와의 대비다.

- recv 쪽 `F_BUF_MORE`는 "같은 bid가 여전히 kernel-owned"일 수 있다는 뜻이다.
- send bundle의 흔한 plain ring path에서는 `F_MORE`가 그런 의미가 아니다.
- send bundle에서 `F_MORE`는 "이번 CQE 뒤에도 같은 SQE가 계속 산다"는 request-liveness 신호다.

즉 `F_MORE`를 보고 현재 tail buffer recycle을 보류하는 코드는 send bundle에서 지나치게 보수적이거나, 더 나쁘게는 queue stall을 만든다.

### 2. contiguous ownership은 `bid 하나`가 아니라 `start bid + res bytes`로 복원한다

`io_uring_prep_send(3)` 문서와 current kernel send path가 주는 정보는 같다.

- CQE는 시작 `bid`만 직접 실어 준다.
- 실제로 account된 buffer는 그 `bid`부터 **contiguous** 하다.
- CQE에는 "이번 batch가 몇 개 slot을 먹었는지"가 직접 실리지 않는다.

그래서 send-side도 recv bundle과 마찬가지로 `cached_head` 또는 `next bid cursor`를 앱이 들고 있어야 한다. 다만 reclaim 규칙은 다르다.

운영적으로 필요한 ledger 최소셋:

- `cached_head_slot`: ring 안에서 다음 CQE가 시작할 것으로 기대하는 slot cursor
- `bid_at(slot)`: slot 순서와 CQE의 시작 `bid`를 연결하는 매핑
- `slot_len[slot]`: 각 provided buffer slot의 실제 send 가능 길이
- `residual_tail[bid]`: short send가 마지막 buffer 중간에서 끊겼을 때 앱이 다시 publish해야 할 unsent suffix

send bundle data CQE 처리 의사 코드는 보통 이런 식이 된다.

```text
on_bundle_cqe(cqe):
  bytes = cqe.res
  bid   = cqe.flags >> IORING_CQE_BUFFER_SHIFT
  assert(bid == bid_at(cached_head_slot))

  while bytes > 0:
    take = min(bytes, slot_len[cached_head_slot])

    if take == slot_len[cached_head_slot]:
      mark_full_slot_done(cached_head_slot)
    else:
      mark_partial_tail_done(cached_head_slot, sent=take,
                             unsent=slot_len[cached_head_slot] - take)

    bytes -= take
    cached_head_slot = next_slot(cached_head_slot)
```

여기서 recv incremental과 가장 크게 갈리는 지점은 partial tail 해석이다.

- send bundle plain ring에서는 partial tail도 **이미 app-owned**다.
- 즉 `res`가 마지막 buffer 중간에서 끊기면, 남은 suffix는 "kernel이 나중에 같은 bid에서 이어서 보낼 bytes"가 아니라 **앱이 다시 publish해야 할 bytes**다.
- current kernel comment도 bundle send에서 short send가 나면 "현재 bundle sequence를 끝낸다"고 못 박는다. 즉 같은 batch 안에서 그 tail을 자동 continuation하지 않는다.

실무적으로는 이것을 "`partial tail`이 아니라 `requeue tail`"로 보는 편이 덜 헷갈린다.

- full buffer: CQE 이후 바로 재사용/재공급 가능
- partial tail: CQE 이후 app가 메모리는 다시 소유하지만, 아직 안 나간 suffix를 따로 다시 큐잉해야 함

### 3. send bundle의 `F_MORE`와 zerocopy의 `F_MORE`는 같은 뜻이 아니다

이 둘을 한 bucket으로 묶으면 버퍼 lifetime 버그가 거의 반드시 난다.

| 경로 | `F_MORE`의 의미 | 메모리 재사용 시점 |
|------|------------------|--------------------|
| plain send bundle + provided buffers | 같은 SQE가 다음 bundle batch CQE를 더 낼 수 있음 | **현재 data CQE 시점** |
| `send_zc` / `sendmsg_zc` | notification CQE가 뒤에 더 온다는 뜻 | **`IORING_CQE_F_NOTIF` CQE 시점** |

current kernel send-zc prep는 `IORING_RECVSEND_BUNDLE`을 valid flag로 받지 않는다. 그래서 한 SQE에서 "bundle multishot `F_MORE`"와 "zerocopy notif pending `F_MORE`"가 겹치는 복합 해석을 할 필요는 없다.

zerocopy path의 핵심은 다음이다.

- 첫 CQE: data CQE, `res`는 bytes sent 또는 음수 에러
- `F_MORE=1`이면 notification CQE가 뒤따른다
- 둘째 CQE: `F_NOTIF=1`, 메모리 재사용 가능 신호
- `IORING_SEND_ZC_REPORT_USAGE`를 켰다면 notification `res`는 `0` 또는 `IORING_NOTIF_USAGE_ZC_COPIED`

즉 zerocopy send는 "전송 결과"와 "메모리 lifetime 종료"가 CQE 두 개로 분리된다. send bundle copy path에는 이 두 단계가 없다.

### 4. fixed buffers는 recycle이 아니라 registration lifetime 문제다

fixed buffer send는 `IOSQE_BUFFER_SELECT`와 다른 메커니즘이다.

- provided buffers: CQE마다 `bid` ownership을 userspace와 주고받는다
- fixed buffers: `IORING_RECVSEND_FIXED_BUF` + `buf_index`로 **이미 등록된 슬롯**을 참조한다

따라서 fixed buffer path에서는 `buf_ring_add()` 같은 reclaim이 없다.

| 경로 | CQE가 끝내는 것 | CQE가 끝내지 않는 것 |
|------|-----------------|----------------------|
| copy send + fixed buffer | 이번 send가 그 registered region을 참조하던 per-I/O use | buffer slot registration 자체 |
| zerocopy send + fixed buffer | data CQE는 전송 결과만, notif CQE가 memory reuse 시점 | 등록 슬롯 자체 |

이 차이 때문에 fixed buffer send 운영은 두 단계로 봐야 한다.

1. 이번 I/O가 끝났는가  
data CQE, 또는 zerocopy면 notif CQE까지 본다.

2. 등록 슬롯을 바꿔도 되는가  
`io_uring_register_buffers_update_tag(3)` / unregister completion tag가 오거나, ring teardown 뒤 inflight ref가 사라졌는지 본다.

`io_uring_registered_buffers.7`이 강조하듯 registered buffers와 provided buffers는 별도 메커니즘이다. send bundle은 `IOSQE_BUFFER_SELECT`가 필요하므로 fixed buffer와 섞을 수 없다.

### 5. send-side incremental ring은 예외적으로 `F_BUF_MORE`를 다시 의미 있게 만든다

보통 send bundle 설명은 "send 쪽에는 recv 같은 tail hold가 없다"에서 끝내도 된다. 다만 send bgid 자체를 `IOU_PBUF_RING_INC`로 등록했다면 얘기가 달라진다.

current kernel `kbuf.c`는 incremental ring commit이 마지막 buffer를 부분 소비하면:

- ring head를 완전히 넘기지 않고
- CQE에 `IORING_CQE_F_BUF_MORE`를 세운다

즉 send-side에서도 incremental ring을 쓰는 순간 reclaim 규칙이 다시 byte-window 기반으로 바뀐다.

- plain send bundle ring: partial tail는 app-owned unsent suffix
- incremental send ring: `F_BUF_MORE` tail는 아직 kernel-owned continuation

실무에서는 send bundle을 ordinary provided ring으로 쓰는 경우가 대부분이라 첫 번째 규칙만 알아도 된다. 하지만 `IOU_PBUF_RING_INC`까지 얹는 실험을 한다면 recv 쪽과 같은 수준의 window ledger가 다시 필요하다.

## 운영 체크리스트

- send bundle CQE의 `res`를 buffer count로 읽지 말고 byte count로 읽는다.
- `IORING_CQE_F_MORE`가 켜졌다고 같은 SQE를 resubmit하지 않는다. current SQE가 아직 살아 있다.
- send bundle plain ring에서 partial tail이 나오면, 그 suffix는 kernel continuation이 아니라 **userspace 재큐잉 대상**으로 기록한다.
- zerocopy send는 data CQE 이후에도 `IORING_CQE_F_NOTIF`를 기다린다. 첫 CQE에서 버퍼를 덮어쓰면 안 된다.
- fixed buffer send는 `buf_ring_add()`를 호출하지 않는다. CQE가 끝내는 것은 per-I/O 참조이지 등록 슬롯 lifetime이 아니다.
- provided buffers와 fixed buffers는 별도 메커니즘이다. `IOSQE_BUFFER_SELECT`와 `IORING_RECVSEND_FIXED_BUF`를 한 SQE에서 같은 의미로 섞어 생각하지 않는다.
- feature probe는 `IORING_FEAT_RECVSEND_BUNDLE`, zerocopy는 opcode/protocol 지원과 notification CQE 유무로 본다.

## 꼬리질문

> Q: send bundle에서 `F_MORE`면 마지막 buffer를 아직 recycle하면 안 되나요?  
> 핵심: plain provided ring 기준으로는 그렇지 않다. `F_MORE`는 다음 bundle batch가 이어질 수 있다는 뜻이고, 현재 batch는 이미 CQE 시점에 app 쪽으로 돌아온다.

> Q: send bundle CQE가 buffer 중간에서 끊기면 kernel이 같은 `bid`에서 이어서 보내 주나요?  
> 핵심: plain ring에서는 기대하지 않는 편이 안전하다. current kernel comment도 short send면 현재 bundle sequence를 끝낸다고 본다. 남은 suffix는 앱이 다시 publish해야 한다.

> Q: zerocopy send는 data CQE가 성공했으면 버퍼를 덮어써도 되나요?  
> 핵심: 안 된다. `IORING_CQE_F_NOTIF` notification CQE가 와야 안전하다.

> Q: fixed buffer send가 끝났으면 바로 unregister해도 되나요?  
> 핵심: per-I/O는 끝났을 수 있어도 registration slot은 inflight ref가 남아 있을 수 있다. tagged update/unregister completion이나 ring teardown 이후까지 고려해야 한다.

## 참고 소스

- [`io_uring_setup(2)` in liburing, `IORING_FEAT_RECVSEND_BUNDLE`](https://github.com/axboe/liburing/blob/master/man/io_uring_setup.2)
- [`io_uring_prep_send(3)` in liburing, provided-buffer send / send bundle contract](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_send.3)
- [`io_uring_prep_send_zc(3)` in liburing, notification CQE semantics](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_send_zc.3)
- [`io_uring_enter(2)` in liburing, zerocopy send CQE lifetime notes](https://github.com/axboe/liburing/blob/master/man/io_uring_enter.2)
- [`io_uring_registered_buffers(7)` in liburing, registration lifetime / tags](https://github.com/axboe/liburing/blob/master/man/io_uring_registered_buffers.7)
- [`include/uapi/linux/io_uring.h` in Linux kernel, `IORING_RECVSEND_BUNDLE` / `IORING_RECVSEND_FIXED_BUF` / CQE flags](https://github.com/torvalds/linux/blob/master/include/uapi/linux/io_uring.h)
- [`io_uring/net.c` in Linux kernel, send bundle multishot + completion path](https://github.com/torvalds/linux/blob/master/io_uring/net.c)
- [`io_uring/kbuf.c` in Linux kernel, `io_put_kbufs()` / incremental `F_BUF_MORE` commit semantics](https://github.com/torvalds/linux/blob/master/io_uring/kbuf.c)
- [`test/recvsend_bundle.c` in liburing](https://github.com/axboe/liburing/blob/master/test/recvsend_bundle.c)
- [`test/send-zerocopy.c` in liburing](https://github.com/axboe/liburing/blob/master/test/send-zerocopy.c)

## 한 줄 정리

send bundle은 "`start bid + res bytes`를 CQE마다 정산하면서 같은 SQE가 다음 batch를 이어 갈 수 있는 send-side multishot"이고, plain provided ring에서는 그 batch의 ownership이 CQE 시점에 이미 app로 돌아온다. 반대로 zerocopy는 notification CQE가 lifetime 종료 신호이고, fixed buffers는 per-I/O 완료와 registration slot lifetime을 분리해서 봐야 한다.
