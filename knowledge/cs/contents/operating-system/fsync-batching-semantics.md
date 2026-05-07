---
schema_version: 3
title: Fsync Batching Semantics
concept_id: operating-system/fsync-batching-semantics
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- fsync-batching-semantics
- durability-batching
- group-commit-fsync
- batch-size-fsync
aliases:
- fsync batching semantics
- durability batching
- group commit fsync
- batch size fsync latency
- data loss window
- directory fsync crash consistency
intents:
- deep_dive
- design
- troubleshooting
linked_paths:
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/dirty-page-ratios-writeback-tuning.md
- contents/operating-system/fsync-tail-latency-dirty-writeback-debugging.md
- contents/operating-system/rename-atomicity-directory-fsync-crash-consistency.md
- contents/operating-system/page-cache-thrash-vs-direct-io.md
- contents/operating-system/io-scheduler-blk-mq-basics.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
symptoms:
- fsync를 매 요청마다 호출해 tail latency가 커지거나, 너무 모아 data loss window가 커진다.
- batching으로 throughput은 좋아졌지만 durability acknowledgement 의미가 불명확해졌다.
- directory fsync나 rename atomicity까지 포함한 crash consistency 경계를 놓친다.
expected_queries:
- fsync batching은 latency와 durability loss window를 어떻게 trade-off해?
- group commit처럼 여러 write를 묶어 fsync할 때 acknowledgement 의미는 무엇이야?
- batch size와 timing을 잘못 잡으면 왜 지연과 데이터 손실 위험을 동시에 키워?
- rename atomicity와 directory fsync까지 durability contract에 포함해야 해?
contextual_chunk_prefix: |
  이 문서는 fsync batching을 여러 write 결과를 묶어 durability를 확보하는 전략으로 보되,
  batch size와 timing, acknowledgement semantics, crash consistency, data loss window를 함께
  설계해야 한다는 점을 설명한다.
---
# Fsync Batching Semantics

> 한 줄 요약: fsync batching은 여러 쓰기 결과를 묶어 내구성을 확보하는 전략이지만, 배치 크기와 타이밍을 잘못 잡으면 지연과 데이터 손실 위험을 동시에 키운다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)
> - [Fsync Tail Latency, Dirty Writeback, Backend Debugging](./fsync-tail-latency-dirty-writeback-debugging.md)
> - [Rename Atomicity, Directory fsync, Crash Consistency](./rename-atomicity-directory-fsync-crash-consistency.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: fsync batching, fdatasync, group commit, durability, write coalescing, journal commit, sync_file_range, WAL, fsync tail latency, group commit latency, backend durability

## 핵심 개념

`fsync()`는 데이터를 디스크에 안전하게 반영해 달라는 요청이다. batching은 여러 쓰기의 내구성 보장을 한 번에 묶어 처리하는 전략이다.

- `fsync`: 데이터와 메타데이터의 안정적 반영을 요구한다
- `fdatasync`: 데이터 중심 동기화다
- `group commit`: 여러 요청의 flush를 묶는 전략이다

왜 중요한가:

- 자주 fsync하면 throughput이 급락할 수 있다
- 너무 늦게 묶으면 장애 시 손실이 커질 수 있다
- DB/WAL, append log, queue durability에 직접 연결된다

이 문서는 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)를 durability batching 관점으로 좁힌다.

## 깊이 들어가기

### 1. batching은 durability의 배치다

여러 write를 모아 한 번에 fsync하면 효율이 올라간다.

- 디스크 flush 횟수를 줄일 수 있다
- journal commit과 궁합이 맞을 수 있다
- 그러나 commit boundary를 잘못 잡으면 지연이 늘어난다

### 2. fsync는 write 완료와 다르다

`write()` 성공은 커널 버퍼 반영일 뿐이다. `fsync()`는 더 강한 보장이다.

### 3. group commit은 성능과 안정성의 타협이다

- 더 자주 flush하면 안전하지만 느리다
- 더 크게 묶으면 빠르지만 손실 창이 늘어난다

### 4. 워크로드마다 최적점이 다르다

- DB WAL
- message queue
- append-only log
- file-based state checkpoint

## 실전 시나리오

### 시나리오 1: 작은 write마다 fsync하니 TPS가 급락한다

가능한 원인:

- flush 비용이 너무 자주 발생한다
- 배치 효과를 못 얻는다
- 디스크 queue가 계속 비워진다

진단:

```bash
iostat -x 1
pidstat -d 1
cat /proc/meminfo | grep -E 'Dirty|Writeback'
```

### 시나리오 2: batching을 키웠더니 복구 시 손실이 커졌다

가능한 원인:

- commit window가 너무 길다
- fsync interval이 길다
- durable boundary가 늦다

### 시나리오 3: 배치가 크면 좋은데 가끔 spike가 보인다

가능한 원인:

- writeback burst
- journal commit burst
- storage queueing

## 코드로 보기

### 배치 감각

```text
multiple writes
  -> batch them
  -> fsync once
  -> durability boundary reached
```

### 기본 API

```c
write(fd, buf, len);
fsync(fd);
fdatasync(fd);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 자주 fsync | 안전성이 높다 | TPS가 떨어질 수 있다 | 강한 내구성 |
| group commit | 효율이 좋다 | 손실 창이 늘 수 있다 | DB/WAL |
| 느슨한 flush | 성능이 좋다 | 장애 시 손실 위험 | 로그/캐시성 데이터 |

## 꼬리질문

> Q: fsync batching은 왜 쓰나요?
> 핵심: flush 비용을 여러 write에 나눠 성능을 높이기 위해서다.

> Q: `fdatasync`와 `fsync` 차이는?
> 핵심: `fdatasync`는 데이터 중심, `fsync`는 메타데이터까지 포함한 더 강한 동기화다.

> Q: batching이 커질수록 항상 좋은가요?
> 핵심: 아니다. durability window와 latency가 커진다.

## 한 줄 정리

fsync batching은 디스크 flush를 묶어 성능을 높이지만, commit window가 길어질수록 durability와 latency의 trade-off가 커진다.
