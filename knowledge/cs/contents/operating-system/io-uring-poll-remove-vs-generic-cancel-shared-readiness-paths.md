# io_uring POLL_REMOVE vs Generic Cancel for One-Shot, Multishot, and Shared Readiness Paths

> 한 줄 요약: `io_uring`에서 poll watcher를 내리는 작업은 보통 fd teardown이 아니라 **readiness subscription 관리**다. 그래서 one-shot/multishot poll arm 하나를 retire하거나 owner handoff를 할 때는 대개 `POLL_REMOVE(user_data)`를 기본값으로 두고, generic cancel은 shared readiness path 전체나 descriptor lifecycle을 함께 끊을 때만 넓게 쓴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring Cancel Scope with Fixed Files and Mixed recv/send/poll Paths](./io-uring-cancel-scope-fixed-files-mixed-ops.md)
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [epoll Level-Triggered, Edge-Triggered, ONESHOT Wakeup Semantics](./epoll-level-edge-oneshot-wakeup-semantics.md)
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [eventfd, signalfd, Epoll Control-Plane Integration](./eventfd-signalfd-epoll-control-plane-integration.md)

> retrieval-anchor-keywords: io_uring poll_remove, POLL_REMOVE vs cancel, io_uring generic cancel, io_uring poll watcher removal, io_uring one-shot poll remove, io_uring multishot poll cancel, shared readiness path, readiness subscription, poll_remove vs cancel_fd, poll_remove vs cancel user_data, IORING_OP_POLL_ADD, io_uring_prep_poll_remove, io_uring_prep_poll_multishot, io_uring_prep_poll_update, IORING_CQE_F_MORE, IORING_ASYNC_CANCEL_ALL, IORING_ASYNC_CANCEL_OP, direct descriptor poll cancel, poll watcher handoff, poll generation user_data, EPOLLONESHOT rearm, EPOLLET poll update

## 핵심 개념

`POLL_REMOVE`와 generic cancel은 커널 내부적으로 비슷한 cancel machinery를 쓰지만, 운영 의도는 다르게 읽는 편이 안전하다.

- `POLL_REMOVE(user_data)`는 "이 poll registration 하나를 내려라"는 **watcher-level intent**다
- generic `cancel(user_data)`는 같은 user_data를 가진 request를 끊는 **request-level intent**다
- generic `cancel_fd(... ALL/OP ...)`는 같은 fd namespace 아래 걸린 request 묶음을 정리하는 **lifecycle-level intent**다

따라서 선택 기준은 "무슨 request를 찾을 수 있나"보다 "지금 끝내려는 대상이 watcher 하나인지, readiness path 전체인지, fd lifecycle인지"다.

| 지금 끝내려는 대상 | 기본 선택 | 이유 | generic cancel로 바꾸는 시점 |
|---|---|---|---|
| 특정 one-shot poll arm 하나 | `POLL_REMOVE(user_data)` | poll watcher만 retire한다는 의도가 가장 분명하다 | 같은 user_data bookkeeping을 모든 op에서 공통화했고 poll/non-poll을 굳이 구분하지 않아도 될 때 |
| 특정 multishot poll generation 하나 | `POLL_REMOVE(user_data)` + terminal CQE drain | `IORING_CQE_F_MORE`가 꺼질 때까지 old generation을 추적해야 한다 | poll watcher뿐 아니라 같은 generation의 다른 request도 함께 끊어야 할 때 |
| 같은 fd의 poll watcher 여러 개 일괄 정리 | 6.6+면 `cancel_fd + OP + ALL` | per-watch `user_data`를 모으지 않고 batch sweep 가능하다 | watcher 수가 적고 generation map이 명확하면 여러 번 `POLL_REMOVE`도 가능 |
| recv/send/poll이 섞인 shared readiness path 전체 stop | generic cancel | poll만 지우면 실제 I/O generation은 남기 때문에 stop intent가 반쪽이 된다 | 해당 stop이 "알림 제거"만 의미한다면 다시 `POLL_REMOVE`로 좁힌다 |
| connection/listener full teardown | generic `fd + ALL` | descriptor lifecycle 전체를 함께 정리해야 한다 | 없음. teardown에서는 넓은 cancel이 오히려 맞다 |

## 깊이 들어가기

### 1. one-shot poll watcher는 "이미 한 번 끝날 수 있는 arm"이라 remove의 의미가 더 좁다

`io_uring_prep_poll_add()`의 기본 동작은 single-shot이다. readiness가 한 번 발생하면 CQE 하나를 올리고 그 watcher는 끝난다. 그래서 one-shot poll에서 `POLL_REMOVE`를 보내는 상황은 보통 다음 셋 중 하나다.

- timeout이나 다른 fallback branch가 먼저 이겨서, 아직 안 깬 watcher를 철회하고 싶다
- worker ownership을 넘기기 전에 old arm을 확실히 내리고 싶다
- `EPOLLONESHOT`/`EPOLLET` 같은 higher-order readiness semantics를 바꾸기 위해 old watcher를 제거하고 새 arm을 걸어야 한다

여기서 `-ENOENT`는 흔히 버그보다 race다.

- watcher가 이미 readiness CQE를 올리고 끝났을 수 있다
- 다른 thread가 먼저 remove/cancel했을 수 있다
- generation bookkeeping이 늦어 old arm이 이미 사라졌을 수 있다

one-shot watcher는 원래 self-terminating이므로, `-ENOENT`를 보면 먼저 "이미 firing돼서 끝났는가"를 확인해야 한다. 이 경우 blind retry보다 CQ를 drain하고 next generation state를 맞추는 편이 맞다.

### 2. multishot poll watcher는 cancel CQE가 아니라 `!IORING_CQE_F_MORE`가 진짜 종료 경계다

`io_uring_prep_poll_multishot()`은 readiness notification이 여러 번 올 수 있는 long-lived subscription이다. 이 watcher를 내릴 때는 accept/recv multishot과 똑같이 generation 사고방식이 필요하다.

- `IORING_CQE_F_MORE=1`이면 같은 poll generation이 아직 살아 있다
- remove/cancel 요청의 CQE가 먼저 와도 old generation CQE가 뒤이어 도착할 수 있다
- `IORING_CQE_F_MORE=0`인 terminal CQE를 확인해야만 그 generation이 끝났다고 볼 수 있다

즉 multishot poll watcher는:

1. `POLL_REMOVE(active_poll_ud)`를 낸다
2. remove CQE만 보고 새 watcher를 바로 arm하지 않는다
3. old `user_data`의 terminal CQE(`!F_MORE`)까지 drain한다
4. 그 뒤에만 새 generation을 arm하거나 fd를 닫는다

이 패턴이 중요한 이유는 shared readiness path에서 "old watcher가 아직 살아 있는데 new owner가 새 watcher를 건" 상태를 막기 위해서다.

### 3. shared readiness path에서는 poll watcher와 actual I/O generation을 분리해서 본다

여기서 말하는 shared readiness path는 같은 fd에 다음이 함께 걸린 구조다.

- `IORING_OP_POLL_ADD` / multishot poll watcher
- `recv`, `send`, `recvmsg`, timeout, eventfd 같은 실제 data/control request
- 경우에 따라 direct descriptor slot이나 shared socket state

이 구조에서 poll watcher는 대개 "알림 레버"이고, recv/send는 "실제 data plane"이다. 그래서 poll watcher만 내리고 싶을 때 generic fd cancel을 쓰면 의도보다 범위가 넓어진다.

대표적인 예:

- `POLLOUT` watcher는 send queue 재개 신호용인데, 같은 fd의 `sendmsg` retry나 `recv_multishot`는 계속 살아 있어야 한다
- control-plane thread가 readiness만 관리하고, data-plane worker는 실제 read/write를 진행한다
- listener/socket teardown이 아니라 worker handoff 또는 interest mask 전환만 하고 싶다

이때 기본값은 `POLL_REMOVE(user_data)`다. 반대로 다음은 generic cancel이 더 맞다.

- connection close처럼 recv/send/poll을 같이 죽여야 한다
- listener stop처럼 shared readiness path 자체를 모두 내려야 한다
- per-watch `user_data`를 모으기보다 같은 fd의 poll watcher를 batch sweep해야 한다

한 줄로 정리하면:

- **watcher retirement / owner handoff / mask semantics reset**: `POLL_REMOVE`
- **request batch stop / path stop / teardown**: generic cancel

### 4. generic `cancel(user_data)`와 `POLL_REMOVE(user_data)`의 차이는 "정확도"보다 "의도 보존"에 가깝다

`POLL_REMOVE` man page 기준으로 동작은 generic cancel과 거의 같고, 단지 poll request만 찾는다. 그래서 user_data가 전역적으로 유일하고 poll/non-poll alias가 절대 없다면 두 방식 모두 정확하게 한 request를 찾을 수 있다.

그럼에도 `POLL_REMOVE`를 기본값으로 둘 이유는 있다.

- code review 때 "이건 fd teardown이 아니라 readiness watcher 제거"라는 의도가 바로 보인다
- shared readiness path에서 helper를 재사용하다가 non-poll request를 끊는 실수를 줄인다
- poll bookkeeping 문서화가 쉬워진다. 특히 one-shot arm, multishot generation, owner handoff가 섞일 때 유리하다

즉 `cancel(user_data)`가 틀린 것은 아니지만, poll watcher lifecycle을 다루는 코드 경로라면 `POLL_REMOVE`가 더 self-describing하다.

### 5. `POLL_UPDATE`로 끝나는 변경과 remove+rearm이 필요한 변경을 구분해야 한다

`io_uring_prep_poll_update()`는 기존 watcher를 새 mask/user_data로 갱신할 수 있지만, 다 바꿀 수 있는 것은 아니다.

- lower 16-bit event mask 교체: update 가능
- `user_data` 교체: update 가능
- singleshot -> multishot 전환: `IORING_POLL_ADD_MULTI`와 함께 update 가능
- `EPOLLONESHOT`, `EPOLLET` 같은 higher-order state 변경: update 불가

즉 다음 경우는 remove+rearm이 필요하다.

- readiness ownership 모델을 바꾼다
- `EPOLLONESHOT`/`EPOLLET`을 켜거나 끈다
- old generation을 끝내고 새 generation 번호로 다시 관리하고 싶다

이런 변경은 "mask 몇 비트 수정"이 아니라 watcher semantics를 새로 만드는 일이라 `POLL_REMOVE`가 더 잘 맞는다.

### 6. descriptor-wide sweep은 batch convenience가 장점이지만, shared path에서는 의도 누수가 생긴다

6.6+에서는 `IORING_ASYNC_CANCEL_OP`로 `IORING_OP_POLL_ADD`만 골라 `fd + OP + ALL` sweep을 할 수 있다. 이건 분명 유용하다.

- per-fd 아래 poll watcher가 정말 많다
- all-watchers-on-this-fd stop이 정책상 맞다
- fixed/direct descriptor라서 `FD_FIXED`까지 포함한 descriptor namespace 정리가 필요하다

하지만 trade-off도 크다.

- watcher 하나만 retire하려는 상황에서는 지나치게 넓다
- 같은 fd를 공유하는 다른 owner의 watcher까지 같이 죽일 수 있다
- batch cancel CQE는 양수 count를 반환하므로, 이후 어떤 watcher들이 실제로 terminal CQE를 냈는지 추가 drain bookkeeping이 필요하다

그래서 batch sweep은 **per-fd policy**일 때만 쓰고, **per-watch lifecycle**에서는 `POLL_REMOVE`를 우선하는 편이 좋다.

## 실전 시나리오

### 시나리오 1: `POLLOUT` one-shot watcher를 없애고 send queue는 유지하고 싶다

상황:

- send queue가 비어 `POLLOUT` 관심을 잠시 내리고 싶다
- 같은 fd의 recv path는 계속 살아 있어야 한다

선택:

- `POLL_REMOVE(write_poll_ud)`

이유:

- 의도는 writable readiness hint 제거이지 fd teardown이 아니다
- `cancel_fd + ALL`은 recv/send retry path까지 건드릴 수 있다

### 시나리오 2: multishot poll watcher를 다른 worker에게 handoff한다

상황:

- old worker가 `POLLIN` multishot watcher를 갖고 있다
- 새 worker가 ownership을 가져갈 예정이다

선택:

1. old worker의 `POLL_REMOVE(active_ud)`
2. old generation의 `!F_MORE` terminal CQE 확인
3. 새 worker가 새 `user_data`로 arm

핵심:

- remove CQE 수신만으로 handoff 완료로 보면 old/new watcher가 잠깐 중복될 수 있다

### 시나리오 3: listener/socket을 아예 내린다

상황:

- poll watcher뿐 아니라 recv/send/accept/timeout path도 모두 끝내야 한다

선택:

- generic `cancel_fd(... ALL)` 또는 목적에 맞는 `fd + OP + ALL`

핵심:

- 이건 watcher 관리가 아니라 descriptor lifecycle 정리다
- direct descriptor면 `FD_FIXED`를 빠뜨리면 안 된다

### 시나리오 4: same fd의 poll watcher 64개를 한 번에 걷고 싶다

상황:

- per-watch `user_data`를 전부 순회하는 것보다 fd-wide sweep이 더 단순하다

선택:

- 6.6+면 `cancel_fd + OP + ALL`, opcode는 `IORING_OP_POLL_ADD`

핵심:

- batch policy가 맞는 경우에만 generic cancel이 이긴다
- 이후 terminal CQE drain과 count reconciliation은 여전히 필요하다

## 코드로 보기

### watcher handoff 의사 코드

```text
retire_poll_generation(gen):
  submit poll_remove(gen.user_data)

  while gen.live:
    cqe = wait_cqe()
    if cqe.user_data != gen.user_data:
      dispatch_other(cqe)
      continue

    if !(cqe.flags & IORING_CQE_F_MORE):
      gen.live = false

arm_new_owner(fd, mask):
  ud = next_generation()
  prep_poll_multishot(fd, mask, ud)
```

### full teardown 의사 코드

```text
teardown_fd(conn):
  if conn.uses_fixed_file:
    cancel_fd(conn.direct_slot, FD_FIXED | ALL)
  else:
    cancel_fd(conn.fd, ALL)

  drain_target_cqes()
  shutdown_close_free()
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| `POLL_REMOVE(user_data)` | poll watcher intent가 가장 분명하고 범위가 좁다 | per-watch `user_data` 추적이 필요하다 | one-shot arm retire, multishot generation stop, owner handoff |
| generic `cancel(user_data)` | helper 통일이 쉽다 | poll/non-poll intent가 코드에서 흐려진다 | user_data가 globally unique이고 poll-only helper를 따로 두지 않을 때 |
| `cancel_fd + OP + ALL` | 같은 fd의 poll watcher를 batch sweep한다 | 6.6+ 전제, owner 경계를 쉽게 넘는다 | per-fd policy stop, shard-wide watcher reset |
| `cancel_fd + ALL` | full teardown을 짧게 표현할 수 있다 | shared readiness path에서 너무 넓다 | connection close, listener stop |
| `poll_update` | 기존 watcher를 유지한 채 mask/user_data를 바꾼다 | higher-order readiness semantics는 못 바꾼다 | low-bit event update, singleshot->multishot 전환 |

## 꼬리질문

> Q: `cancel(user_data)`와 `POLL_REMOVE(user_data)`는 사실상 같은가요?
> 핵심: 한 poll request만 놓고 보면 거의 같지만, `POLL_REMOVE`는 poll-only intent를 보존한다. shared readiness path에서는 그 의도 차이가 운영 사고를 줄인다.

> Q: one-shot poll watcher에서도 `POLL_REMOVE`를 써야 하나요?
> 핵심: watcher가 아직 안 끝났을 때만 의미가 있다. 이미 firing돼 끝났다면 `-ENOENT`가 정상 race일 수 있다.

> Q: multishot poll watcher는 remove CQE만 보면 끝난 것 아닌가요?
> 핵심: 아니다. `!IORING_CQE_F_MORE` terminal CQE를 확인해야 old generation이 진짜 끝난다.

> Q: 같은 fd의 poll watcher가 너무 많으면 `POLL_REMOVE`를 반복하는 게 비효율적인가요?
> 핵심: 그렇다면 6.6+의 `fd + OP + ALL`이 맞다. 다만 그건 per-watch lifecycle이 아니라 per-fd policy stop일 때만 권장된다.

## 참고 소스

- [`io_uring_prep_poll_remove(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_poll_remove.3.html)
- [`io_uring_prep_cancel(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_cancel.3.html)
- [`io_uring_prep_poll_multishot(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_poll_multishot.3.html)
- [`io_uring_prep_poll_update(3)`](https://man7.org/linux/man-pages/man3/io_uring_prep_poll_update.3.html)
- [`test/poll-cancel.c` in liburing](https://github.com/axboe/liburing/blob/master/test/poll-cancel.c)
- [`test/poll-cancel-all.c` in liburing](https://github.com/axboe/liburing/blob/master/test/poll-cancel-all.c)

## 한 줄 정리

poll watcher 하나를 내리는 일은 보통 fd teardown이 아니라 readiness subscription 관리이므로, one-shot/multishot watcher의 retire와 handoff는 `POLL_REMOVE`를 기본값으로 두고, generic cancel은 shared readiness path 전체나 descriptor lifecycle을 정리할 때만 넓게 쓰는 편이 안전하다.
