---
schema_version: 3
title: io_uring recv send zerocopy Teardown Ordering
concept_id: operating-system/io-uring-recv-send-zerocopy-teardown-ordering
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- io-uring-recv
- send-zerocopy-teardown
- ordering
- io-uring-zerocopy
aliases:
- io_uring zerocopy teardown ordering
- send_zc notification CQE
- recv_multishot terminal CQE
- request drain buffer-lifetime drain
- tx buffer lifetime
- late notification CQE
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/io-uring-multishot-cancel-rearm-drain-shutdown.md
- contents/operating-system/io-uring-send-bundle-zerocopy-fixed-buffer-completion-accounting.md
- contents/operating-system/io-uring-cancel-scope-fixed-files-mixed-ops.md
- contents/operating-system/io-uring-recv-bundle-recvmsg-multishot-buffer-ring-head-recycling.md
- contents/operating-system/io-uring-completion-observability-playbook.md
symptoms:
- send_zc data CQE만 보고 tx buffer를 재사용했다가 늦게 온 notification CQE와 충돌한다.
- recv_multishot terminal CQE와 send/sendmsg data CQE를 같은 종료선으로 착각한다.
- connection state와 user_data를 cancel CQE 직후 해제해 late CQE가 stale state를 참조한다.
expected_queries:
- io_uring zerocopy send teardown에서 data CQE와 notification CQE는 어떻게 달라?
- recv_multishot terminal CQE와 send completion, zerocopy notification을 분리해야 하는 이유는?
- request drain과 buffer-lifetime drain을 connection shutdown에서 어떻게 추적해?
- cancel CQE만 보고 connection state를 해제하면 어떤 late CQE 문제가 생겨?
contextual_chunk_prefix: |
  이 문서는 io_uring connection teardown에서 recv_multishot terminal CQE, send/sendmsg data CQE,
  send_zc notification CQE가 서로 다른 종료선이라는 점을 설명한다. request drain과
  buffer-lifetime drain을 분리해 tx buffer, user_data, connection state를 해제해야 한다.
---
# io_uring recv multishot, send/sendmsg, zerocopy notification teardown ordering

> 한 줄 요약: connection teardown에서 `recv_multishot` terminal CQE, `send` / `sendmsg` data CQE, `send_zc` / `sendmsg_zc` notification CQE는 서로 다른 종료선이다. cancel CQE나 zerocopy의 첫 data CQE만 보고 connection state, `user_data`, tx buffer를 해제하면 늦게 도착한 terminal/notif CQE와 충돌하므로, shared state machine은 `request drain`과 `buffer-lifetime drain`을 분리해 추적해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [io_uring send bundle, zerocopy notification, fixed-buffer completion accounting](./io-uring-send-bundle-zerocopy-fixed-buffer-completion-accounting.md)
> - [io_uring Cancel Scope with Fixed Files and Mixed recv/send/poll Paths](./io-uring-cancel-scope-fixed-files-mixed-ops.md)
> - [io_uring recv bundle, recvmsg multishot, buffer-ring head recycling](./io-uring-recv-bundle-recvmsg-multishot-buffer-ring-head-recycling.md)
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [eventfd, signalfd, Epoll Control-Plane Integration](./eventfd-signalfd-epoll-control-plane-integration.md)

> retrieval-anchor-keywords: io_uring recv send zerocopy teardown ordering, io_uring shared connection state machine, recv multishot send_zc teardown, sendmsg_zc teardown ordering, zerocopy notification drain, IORING_CQE_F_NOTIF teardown, IORING_CQE_F_MORE recv terminal, multishot recv terminal CQE, cancel CQE drain barrier, shutdown after zerocopy notif, close after zerocopy notification, tx data phase versus buffer lifetime, user_data reuse after notif, send_zc same user_data notification, sendmsg_zc same user_data, pending notif counter, half close write drain, shutdown SHUT_WR zerocopy, full close multishot recv cancel, connection destroy barrier, connection close barrier, io_uring send/sendmsg teardown, io_uring request drain versus buffer drain

## 핵심 개념

한 connection 안에서 teardown 시 같이 엮이는 것은 보통 세 종류다.

- `recv_multishot` generation: `IORING_CQE_F_MORE`가 꺼진 terminal CQE를 받아야 진짜로 죽는다.
- `send` / `sendmsg` data request: data CQE 하나면 request execution이 끝난다.
- `send_zc` / `sendmsg_zc` request: 첫 data CQE가 execution을 끝내더라도, `F_MORE`가 켜졌다면 buffer lifetime은 아직 끝나지 않았고 `IORING_CQE_F_NOTIF` CQE를 더 기다려야 한다.

그래서 shared connection state machine은 질문을 둘로 쪼개야 한다.

1. descriptor 관점에서 더 늦게 도착할 request CQE가 남아 있는가
2. memory 관점에서 아직 kernel-owned인 zerocopy buffer가 남아 있는가

이 둘을 섞으면 두 종류의 버그가 나온다.

- cancel CQE나 zerocopy data CQE만 보고 connection object를 free해서 늦게 온 terminal/notif CQE와 충돌한다.
- 반대로 notification까지 기다려야만 `shutdown` / `close`를 제출한다고 설계해서, write-side drain이 TCP ACK 지연에 과하게 묶인다.

이 문서에서 말하는 `drain`은 `IOSQE_IO_DRAIN`이 아니라, **userspace가 final CQE와 refcount를 다 정리할 때까지 기다리는 teardown barrier**다.

## 1. 어떤 CQE가 무엇을 끝내는가

| 관찰한 CQE | request identity 종료? | tx buffer 재사용 가능? | state machine이 해야 할 일 |
|------|------------------------|------------------------|-----------------------------|
| recv CQE, `MORE=1` | 아니오 | 해당 없음 | recv generation을 계속 alive로 둔 채 CQE만 소비 |
| recv CQE, `MORE=0` | recv generation 종료 | 해당 없음 | rearm 또는 close barrier 계산 |
| send / sendmsg data CQE | 해당 tx request 종료 | 예 | tx entry를 바로 done 처리 |
| send_zc / sendmsg_zc data CQE, `MORE=0` | 해당 tx request 종료 | 예 | tx entry를 바로 done 처리 |
| send_zc / sendmsg_zc data CQE, `MORE=1` | execution phase만 종료 | 아니오 | `waiting_notif`로 전환하고 entry 유지 |
| notification CQE, `F_NOTIF=1` | 이미 끝난 tx request의 buffer lifetime 종료 | 예 | tx buffer / `user_data` slot 최종 해제 |
| cancel CQE | cancel 시도 결과일 뿐 | 아니오 | target terminal/notif CQE를 계속 기다림 |

특히 zerocopy send path는 `res`보다 `flags`가 더 중요하다.

- data CQE의 `res < 0`이어도 `F_MORE`가 켜져 있으면 notification CQE가 더 올 수 있다.
- notification CQE는 original request와 **같은 `user_data`** 를 사용한다.
- 따라서 첫 data CQE만 받고 그 `user_data` slot을 재사용하면, 늦게 온 notif CQE를 새 request completion으로 잘못 해석할 수 있다.

즉 send_zc 계열은 "`request는 끝났는가`"와 "`이 메모리를 덮어써도 되는가`"가 같은 질문이 아니다.

## 2. teardown barrier를 두 개로 나눈다

| barrier | 의미 | 통과 조건 |
|---------|------|-----------|
| descriptor close barrier | socket request identity가 더는 남지 않음 | live recv generation 없음, data-phase tx 없음, shared poll watcher 없음 |
| object destroy barrier | connection memory / tx buffer / `user_data` indirection까지 안전 | descriptor close barrier 통과, pending zerocopy notification 0, rx window refs 0 |

이렇게 나누면 teardown 정책이 선명해진다.

- `shutdown(SHUT_RDWR)` / `close` 제출 시점은 descriptor close barrier가 기준이다.
- connection struct, tx slab, `user_data -> entry` 매핑, provided-buffer ownership ledger를 free하는 시점은 object destroy barrier가 기준이다.

실무에서 자주 터지는 문제는 아래 둘이다.

- descriptor close barrier와 object destroy barrier를 하나로 취급해, zerocopy notif가 남아 있는데 connection memory를 먼저 해제한다.
- 반대로 object destroy barrier를 descriptor close barrier에 강제로 맞춰, notif가 늦게 오는 동안 socket close 자체를 붙잡는다.

만약 `user_data`에 connection 포인터를 직접 넣었다면 사실상 두 barrier를 분리하기 어렵다. 더 유연하게 가려면 `user_data -> tx entry` indirection을 두고, connection 본체는 `closing_wait_notif` 같은 상태로 남겨 두는 편이 안전하다.

## 3. full close는 cancel -> drain -> shutdown/close -> final notif drain 순서다

1. `conn.closing = true`로 새 recv rearm, 새 tx submit, poll rearm을 먼저 막는다.
2. active recv multishot generation을 `user_data` 기준으로 cancel한다.
3. 더 이상 보내면 안 되는 pending `send` / `sendmsg` / `send_zc` / `sendmsg_zc` data-phase request도 cancel한다.
   - generation별로 끊을 수 있으면 `user_data`가 기본이다.
   - descriptor-wide teardown이 목적일 때만 `fd + ALL` 또는 `fd + OP + ALL`로 넓힌다.
4. CQ drain loop에서 CQE를 종류별로 처리한다.
   - recv: `!MORE`일 때만 generation dead
   - copy send: data CQE에서 done
   - zerocopy send: data CQE + `F_MORE`면 `waiting_notif`, `F_NOTIF` CQE에서 done
   - cancel CQE: bookkeeping hint일 뿐, free trigger가 아니다
5. descriptor close barrier가 통과되면 `IORING_OP_SHUTDOWN` 또는 `IORING_OP_CLOSE`를 제출한다.
6. object destroy barrier까지 계속 drain한 뒤에만 connection state, tx buffer ownership record, `user_data` slot을 해제한다.

핵심은 5와 6을 분리하는 것이다.

- close CQE는 socket descriptor lifecycle을 끝낼 뿐이다.
- zerocopy notif CQE는 tx memory lifecycle을 끝낸다.
- 둘 중 늦은 쪽이 connection object destroy 시점을 결정한다.

send-side에도 `IORING_RECVSEND_POLL_FIRST` 같은 deferred execution이 걸릴 수 있으므로, "send는 multishot이 아니니까 close 직전까지 신경 안 써도 된다"는 생각은 위험하다. request는 one-shot이어도 CQE는 teardown 경계까지 늦게 올 수 있다.

## 4. `shutdown(SHUT_WR)`는 recv cancel과 분리한다

graceful half-close에서는 "더 안 보낸다"와 "더 안 읽는다"가 같은 말이 아니다.

권장 순서:

1. `write_closing = true`로 새 tx submit을 막는다.
2. in-flight copy send와 zerocopy send를 drain한다.
3. zerocopy send는 notification까지 기다린다.
4. 그다음 `shutdown(SHUT_WR)`를 제출한다.
5. recv multishot은 그대로 두고 peer EOF(`res == 0 && !MORE`)나 별도 read-side stop 정책을 기다린다.

왜 recv를 같이 cancel하면 안 되나:

- 프로토콜상 마지막 응답이나 trailer를 아직 읽어야 할 수 있다.
- write-side drain과 read-side subscription teardown을 한 barrier로 묶으면 정상 half-close가 full close처럼 변한다.
- recv provided buffer ownership은 app parser/worker가 아직 붙잡고 있을 수 있으므로, write-side 종료와 무관하게 별도 ledger가 필요하다.

반대로 fatal error나 connection abort가 목적이면 half-close 규칙을 쓰지 말고, full close 규칙으로 recv/send를 함께 정리해야 한다.

## 5. bookkeeping을 최소한 이렇게 쪼갠다

- `recv_generation_ud`: arm마다 새로 발급하고 terminal `!MORE` CQE까지 유지
- `tx_id`: `send` / `sendmsg` / `send_zc` / `sendmsg_zc` request identity. zerocopy data CQE에 `F_MORE`가 있었다면 notif CQE까지 재사용 금지
- `tx_phase`: `waiting_data | waiting_notif | done`
- `pending_zc_notif`: descriptor close barrier와 object destroy barrier를 분리하는 counter
- `rx_window_refs`: provided buffer를 parser/worker가 아직 붙잡고 있으면 recv generation이 죽었어도 destroy 금지

하나의 `pending_io` counter만 두면 안 되는 이유는 단순하다.

- recv multishot는 request 하나가 CQE 여러 개를 낸다.
- zerocopy send는 request 하나가 CQE 최대 두 개를 낸다.
- cancel CQE는 target request의 terminal CQE와 별도다.

즉 teardown bookkeeping은 최소한 `recv generation`, `tx request phase`, `tx notif pending`, `rx ownership` 네 축으로 갈라야 late CQE와 early free를 동시에 막을 수 있다.

## 코드로 보기

```text
start_full_close(conn):
  conn.closing = true
  conn.allow_recv_rearm = false
  conn.allow_tx_submit = false

  if conn.recv.alive:
    cancel(conn.recv.user_data)

  for tx in conn.tx_table where tx.phase == waiting_data:
    cancel(tx.user_data)

on_cqe(cqe):
  if cqe.user_data == conn.recv.user_data:
    if !(cqe.flags & IORING_CQE_F_MORE):
      conn.recv.alive = false
    return

  tx = conn.tx_table[cqe.user_data]
  if !tx:
    handle_non_conn_cqe(cqe)
    return

  if cqe.flags & IORING_CQE_F_NOTIF:
    tx.phase = done
  else if tx.is_zc && (cqe.flags & IORING_CQE_F_MORE):
    tx.phase = waiting_notif
  else:
    tx.phase = done

  if descriptor_close_barrier(conn) && !conn.close_submitted:
    submit_shutdown_or_close(conn)

  if object_destroy_barrier(conn):
    free_conn(conn)
```

포인트는 간단하다.

- recv는 terminal `!MORE` CQE를 보기 전까지 dead가 아니다.
- zerocopy send는 notif CQE를 보기 전까지 memory-safe가 아니다.
- cancel CQE는 barrier를 줄여 주지 않으며, drain loop만 계속하게 만든다.

## 꼬리질문

> Q: zerocopy send의 첫 data CQE가 이미 왔는데 `close`를 바로 제출해도 되나요?  
> 핵심: descriptor close barrier 기준으로는 가능할 수 있지만, notif가 남아 있으면 connection memory나 tx buffer bookkeeping은 아직 free하면 안 된다.

> Q: cancel CQE가 `0`이 떴으면 recv/send state를 바로 지워도 되나요?  
> 핵심: 안 된다. cancel CQE는 취소 시도 결과이고, target request의 terminal CQE나 zerocopy notif CQE가 따로 남아 있을 수 있다.

> Q: send_zc data CQE가 실패했는데도 notif를 기다려야 하나요?  
> 핵심: `res`가 아니라 `F_MORE`를 본다. errored request도 notif를 낼 수 있으므로 `F_MORE=1`이면 기다리는 편이 맞다.

> Q: half-close에서 recv multishot도 같이 cancel해야 하나요?  
> 핵심: 보통 아니다. `SHUT_WR`는 write-side 종료일 뿐이고, read-side subscription 종료는 peer EOF 또는 별도 정책이 결정한다.

## 참고 소스

- [`io_uring_enter(2)`, `IORING_OP_SEND_ZC` / `IORING_OP_SENDMSG_ZC` notification CQE semantics](https://man7.org/linux/man-pages/man2/io_uring_enter.2.html)
- [`io_uring_prep_send(3)` / `io_uring_prep_send_zc(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_send.3.html)
- [`io_uring_prep_sendmsg(3)` / `io_uring_prep_sendmsg_zc(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_sendmsg.3.html)
- [`io_uring_prep_recv_multishot(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_recv_multishot.3.html)
- [`io_uring_prep_cancel(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_cancel.3.html)
- [`io_uring_prep_cancel_fd(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_cancel_fd.3.html)
- [`shutdown(2)`](https://man7.org/linux/man-pages/man2/shutdown.2.html)

## 한 줄 정리

shared connection teardown에서 먼저 끊어야 하는 것은 new submit/rearm이고, 그다음 기준은 "recv terminal CQE까지의 request drain"과 "zerocopy notif CQE까지의 buffer-lifetime drain"을 분리해서 보는 것이다.
