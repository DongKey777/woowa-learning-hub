---
schema_version: 3
title: io_uring Direct Descriptor Slot Reuse files_update close_direct Hygiene
concept_id: operating-system/io-uring-direct-descriptor-slot-reuse-files-update-close-direct-hygiene
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- io-uring-direct
- descriptor-slot-reuse
- files-update-close
- direct-timing
aliases:
- io_uring direct descriptor slot reuse
- files_update close_direct timing
- fixed file slot lifecycle
- direct descriptor hygiene
- in-flight request old file ref
- io_uring private file table
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/io-uring-cancel-scope-fixed-files-mixed-ops.md
- contents/operating-system/io-uring-multishot-cancel-rearm-drain-shutdown.md
- contents/operating-system/io-uring-operational-hazards-registered-resources-sqpoll.md
- contents/operating-system/io-uring-sq-cq-basics.md
- contents/operating-system/io-uring-completion-observability-playbook.md
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
symptoms:
- direct descriptor slot number를 object identity처럼 재사용해 in-flight request가 old file ref를 잡는다.
- files_update나 close_direct timing을 잘못 잡아 slot target과 completion ownership이 헷갈린다.
- fixed file table lifecycle과 cancel/drain 순서가 맞지 않아 stale completion이 보인다.
expected_queries:
- io_uring direct descriptor slot은 object identity가 아니라 lookup key라는 게 무슨 뜻이야?
- files_update와 close_direct는 in-flight request의 old file ref에 어떤 영향을 줘?
- fixed file slot reuse 전에 cancel drain completion을 어떤 순서로 확인해야 해?
- direct descriptor lifecycle hygiene를 completion observability와 연결해줘
contextual_chunk_prefix: |
  이 문서는 io_uring direct descriptor slot number를 object identity가 아니라 private file table
  lookup key로 설명한다. files_update와 close_direct는 lookup target을 바꾸거나 비우지만,
  이미 slot을 resolve한 in-flight request는 old file reference를 completion까지 잡는다.
---
# io_uring Direct Descriptor Slot Reuse, `files_update` / `close_direct` Timing, Lifecycle Hygiene

> 한 줄 요약: direct descriptor slot 번호는 object identity가 아니라 `io_uring` private file table lookup key다. `files_update`와 `close_direct`는 그 lookup target을 바꾸거나 비우는 작업일 뿐이고, 이미 slot을 resolve한 in-flight request는 old file ref를 completion까지 계속 쥔다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring Cancel Scope with Fixed Files and Mixed recv/send/poll Paths](./io-uring-cancel-scope-fixed-files-mixed-ops.md)
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [io_uring Operational Hazards, Registered Resources, SQPOLL](./io-uring-operational-hazards-registered-resources-sqpoll.md)
> - [io_uring SQ, CQ Basics](./io-uring-sq-cq-basics.md)
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)

> retrieval-anchor-keywords: io_uring direct descriptor slot reuse, fixed file slot reuse, fixed file lifecycle, direct descriptor lifecycle hygiene, close_direct timing, io_uring close_direct, files_update timing, io_uring files_update, IORING_OP_FILES_UPDATE, io_uring_register_files_update, IORING_FILE_INDEX_ALLOC, direct descriptor recycling, fixed fd recycle, slot generation, late CQE after slot reuse, stale completion after slot recycle, fixed file node ref, close_direct CQE not drain fence, direct descriptor teardown ordering, fixed file table lifecycle, async files_update ordering

## 핵심 개념

direct descriptor는 일반 프로세스 fd table이 아니라 ring 전용 fixed-file table slot을 쓴다. 그래서 slot 번호는 "소켓 그 자체"가 아니라 "지금 이 slot에 매핑된 file을 찾는 key"다.

핵심 규칙은 세 가지다.

- request가 `IOSQE_FIXED_FILE`로 issue될 때 커널은 그 순간 slot을 lookup하고, 그 결과 node/file ref를 request 쪽에 잡는다
- `files_update`, direct `open/socket/accept`, `close_direct`는 **slot table의 현재 매핑**만 바꾼다
- 이미 old slot entry를 resolve한 request는 slot이 재활용되어도 old file로 completion된다

즉 direct descriptor lifecycle에서 구분해야 할 것은 다음 둘이다.

- **slot namespace가 바뀌는 순간**
- **old in-flight request가 완전히 drain되는 순간**

이 둘은 같은 순간이 아니다.

## 깊이 들어가기

### 1. slot 번호는 connection identity가 아니라 recyclable lookup key다

liburing 문서 기준으로 direct `open/socket`는 registered file table slot을 직접 채운다. 이후 같은 slot 번호를 `fd` 필드에 넣고 `IOSQE_FIXED_FILE`을 켜면 그 slot을 통해 file을 찾는다.

이 구조에서는 slot 번호만으로 connection identity를 만들면 안 된다.

- `IORING_FILE_INDEX_ALLOC`는 free slot을 자동으로 고른다
- `close_direct`로 slot을 비우면 그 번호는 즉시 재할당 후보가 된다
- kernel fixed-file allocator는 막 비워진 slot도 바로 다시 줄 수 있다

그래서 운영에서는 slot을 최소한 `{slot, generation}`으로 보거나, 더 안전하게는 request `user_data`를 generation identity로 써야 한다.

### 2. `files_update`와 direct `open/socket` replacement는 "future lookup target"만 바꾼다

direct lifecycle에서 가장 자주 헷갈리는 지점은 "slot을 갈아끼웠으니 old request도 새 file을 볼 것"이라는 착각이다. 실제로는 반대다.

- `io_uring_register_files_update()`는 syscall return 시점에 table entry를 바꾼다
- `IORING_OP_FILES_UPDATE`는 async request이므로 **update CQE를 받아야** 앱이 table mutation 완료를 확정할 수 있다
- occupied slot에 direct `open/socket/accept`를 쓰면 기존 entry를 replacement하는데, 의미상 `files_update`와 같은 종류의 mutation이다

하지만 request가 이미 slot lookup을 끝낸 뒤라면 그 request는 old entry를 계속 쓴다. Linux source 기준으로 fixed-file request는 issue path에서 slot node ref를 증가시키고, completion 정리 때 그 ref를 내려놓는다. 즉 slot table의 현재 값과 request가 실제로 붙잡고 있는 file ref는 분리된다.

### 3. `close_direct` CQE는 "slot 비움 완료"이지 "old I/O 종료 완료"가 아니다

`io_uring_prep_close_direct()`는 async close request다. direct slot을 table에서 제거하는 convenience helper지만, 의미상 "fixed slot unregister"에 가깝다.

중요한 해석:

- close CQE를 받으면 앱은 **이제 그 slot이 table에서 비워졌다고** 볼 수 있다
- 하지만 old request가 이미 그 slot의 old file ref를 쥐고 있었다면, 그 request의 CQE는 close CQE 뒤에도 올 수 있다
- 따라서 close CQE는 lifecycle fence가 아니라 namespace mutation completion일 뿐이다

같은 논리로 `IORING_OP_FILES_UPDATE` CQE도 "new mapping visible"의 신호이지 "old mapping 사용 request가 모두 끝났다"는 뜻이 아니다.

### 4. request는 "언제 slot을 resolve했는가"에 따라 다른 file을 본다

fixed-file reuse를 안전하게 이해하려면 request를 세 그룹으로 나눠야 한다.

| request 상태 | 어떤 file/slot 상태를 보나 | 운영 위험 |
|---|---|---|
| 이미 issue되어 slot lookup과 ref grab을 끝낸 요청 | old file | slot 재활용 뒤에 late CQE가 와도 정상인데 앱이 새 generation으로 오해한다 |
| SQ에 있었지만 아직 slot lookup 전인 요청 | update/close가 먼저 실행되면 new file 또는 empty slot | submission 순서만 믿고 teardown했다가 `-EBADF`나 wrong-target I/O를 본다 |
| update/close completion 이후 제출한 요청 | new file 또는 empty slot | user-space mapping만 늦게 바꾸면 bookkeeping이 뒤틀린다 |

즉 teardown ordering에서 중요한 것은 "SQE를 언제 넣었나"보다 "slot lookup이 언제 일어났나"다. submission order만으로는 fixed-slot lifecycle fence가 되지 않는다.

### 5. `IORING_OP_FILES_UPDATE`는 update 대상 배열 lifetime도 갖는다

`IORING_OP_FILES_UPDATE`는 register syscall의 async 버전이라서, update 대상 fd 배열 포인터가 completion까지 살아 있어야 한다. 이 timing까지 놓치면 lifecycle bug가 두 겹이 된다.

- slot table mutation 자체가 async다
- update arguments가 completion까지 유효해야 한다

그래서 `files_update`를 teardown phase에 넣을 때는 "old request drain 여부"뿐 아니라 "update payload memory lifetime"도 같이 관리해야 한다.

## 타임라인으로 보기

```text
t0: slot 12 -> socket A
t1: recv generation A를 slot 12로 arm
t2: kernel이 generation A request를 issue하며 old file ref를 잡음
t3: close_direct(12) CQE 또는 files_update(12 -> socket B) CQE 도착
t4: IORING_FILE_INDEX_ALLOC 또는 direct open이 slot 12를 다시 사용
t5: generation A의 late CQE 도착
```

이때 앱이 `slot 12 == 현재 socket B`라고만 생각하면 `t5`의 old CQE를 B에 잘못 귀속한다. fixed slot reuse bug의 대부분은 여기서 나온다.

## teardown ordering hygiene

slot recycle이 얽힌 teardown에서는 다음 순서가 가장 안전하다.

1. slot을 소유한 logical generation에서 새 submit/rearm을 먼저 막는다.
2. long-lived op는 `user_data` 중심으로 cancel한다.
3. active generation map이 빌 때까지 target CQE를 drain한다.
4. 그 다음에만 `close_direct`로 slot을 비우거나, `files_update`/direct `open/socket`으로 slot을 새 file에 넘긴다.
5. async path라면 update/close CQE를 받아 namespace mutation 완료를 확인한다.
6. 마지막으로만 user-space `slot -> object` map을 새 generation으로 publish한다.

실무 규칙으로 줄이면 이렇다.

- **cancel/drain이 close/update보다 먼저**다
- **close/update CQE가 old generation drain 완료를 증명하지는 않는다**
- **slot-only routing을 쓰면 재활용 순간 late CQE에 취약하다**

### 언제 예외가 가능한가

old CQE가 남아 있어도 같은 slot을 일부러 빨리 재사용하는 설계는 가능하다. 단, 그 경우 전제가 강하다.

- request별 `user_data` generation ledger가 있어야 한다
- CQE 처리에서 slot lookup 대신 generation lookup을 써야 한다
- fd-scope cancel 결과도 "slot 전체"가 아니라 "어느 generation이 아직 남았는가"로 해석해야 한다

이 전제가 없으면 aggressive slot recycle은 운영 복잡도만 올린다.

## 실전 시나리오

### 시나리오 1: `IORING_FILE_INDEX_ALLOC`를 쓰는데 가끔 old CQE가 새 connection에서 보인다

가능한 원인:

- 직전 `close_direct`가 slot을 비운 뒤 allocator가 같은 번호를 바로 재사용했다
- old recv/poll/send request가 이미 old file ref를 잡고 있어서 late CQE가 왔다
- 앱이 slot 번호만으로 connection을 매칭했다

대응 감각:

- slot 번호 대신 generation `user_data`를 primary identity로 본다
- close/update CQE와 target request CQE를 따로 추적한다
- recycling pressure가 높은 서비스라면 slot range를 분리하거나 per-generation ledger를 둔다

### 시나리오 2: rollout 중 `files_update` 뒤 fixed-file request가 가끔 `-EBADF`를 본다

가능한 원인:

- request가 생각보다 늦게 issue되어 empty slot window를 봤다
- `IORING_OP_FILES_UPDATE` completion 전에 앱이 "이미 교체됐다"고 가정했다
- close/update와 새 submit을 submission order만으로 직렬화했다

대응 감각:

- namespace mutation은 syscall return 또는 update CQE 기준으로 확인한다
- slot을 비우는 단계와 새 submit 허용 단계를 분리한다
- teardown/rebind 사이에는 generation barrier를 둔다

## 코드로 보기

### 안전한 slot retire / rebind 의사 코드

```text
retire_and_rebind(slot, gen, maybe_new_fd):
  gen.stopping = true
  stop_rearm(slot, gen)

  cancel_all_requests_for_generation(gen)
  drain_until(gen.inflight == 0)

  if maybe_new_fd is none:
    submit close_direct(slot)
    wait_for_close_cqe(slot)
  else if using_sync_register_update:
    register_files_update(slot, maybe_new_fd)
  else:
    submit files_update(slot, maybe_new_fd)
    wait_for_update_cqe(slot)

  publish_slot_owner(slot, new_generation_or_empty)
```

### 피해야 하는 패턴

```text
submit close_direct(slot)
submit new socket_direct_alloc()
on close CQE:
  slot_owner[slot] = new_conn

// late CQE from old generation arrives here
```

이 패턴은 slot mutation CQE와 request drain 완료를 같은 사건으로 취급해서 깨진다.

## 꼬리질문

> Q: `close_direct` CQE를 받았으면 그 slot의 old I/O는 다 끝난 건가요?
> 핵심: 아니다. slot table에서 entry가 제거됐다는 뜻이지, old request가 잡고 있던 file ref가 모두 해제됐다는 뜻은 아니다.

> Q: `files_update`로 같은 slot에 새 소켓을 넣으면 old request도 새 소켓으로 붙나요?
> 핵심: 아니다. 이미 slot을 resolve한 request는 old file ref를 completion까지 유지한다.

> Q: slot 번호만으로 connection identity를 관리하면 왜 위험한가요?
> 핵심: `IORING_FILE_INDEX_ALLOC`와 direct close/update replacement 때문에 같은 번호가 매우 빨리 재활용될 수 있고, late CQE가 새 generation과 섞이기 때문이다.

## 참고 소스

- [`io_uring_register_files(3)`](https://github.com/axboe/liburing/blob/master/man/io_uring_register_files.3)
- [`io_uring_prep_openat(3)`](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_openat.3)
- [`io_uring_prep_socket(3)`](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_socket.3)
- [`io_uring_prep_close(3)`](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_close.3)
- [`io_uring_prep_cancel(3)`](https://github.com/axboe/liburing/blob/master/man/io_uring_prep_cancel.3)
- [`io_uring_enter(2)`](https://github.com/axboe/liburing/blob/master/man/io_uring_enter.2)
- [Linux `io_uring/io_uring.c`](https://github.com/torvalds/linux/blob/master/io_uring/io_uring.c)
- [Linux `io_uring/rsrc.c`](https://github.com/torvalds/linux/blob/master/io_uring/rsrc.c)
- [Linux `io_uring/filetable.c`](https://github.com/torvalds/linux/blob/master/io_uring/filetable.c)
- [Linux `io_uring/openclose.c`](https://github.com/torvalds/linux/blob/master/io_uring/openclose.c)

## 한 줄 정리

direct descriptor lifecycle에서 `files_update`와 `close_direct`는 slot namespace를 바꾸는 작업이고, in-flight request drain은 별도 문제다. teardown이 안전하려면 slot 번호가 아니라 generation을 기준으로 cancel/drain/rebind 순서를 분리해야 한다.
