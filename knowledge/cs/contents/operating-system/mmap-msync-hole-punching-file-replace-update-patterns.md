---
schema_version: 3
title: mmap msync Hole Punching File Replace Update Patterns
concept_id: operating-system/mmap-msync-hole-punching-file-replace-update-patterns
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- mmap-msync-hole
- punching-file-replace
- update
- punching
aliases:
- mmap msync hole punching
- file replace live mapping
- mmap update pattern
- truncate SIGBUS avoidance
- msync durability
- hole punching mapped file
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/mmap-map-shared-vs-map-private-write-semantics.md
- contents/operating-system/mmap-shared-truncate-sigbus-coherency-pitfalls.md
- contents/operating-system/mmap-vs-read-page-cache-behavior.md
- contents/operating-system/rename-atomicity-directory-fsync-crash-consistency.md
- contents/operating-system/sparse-file-fallocate-hole-punching.md
symptoms:
- file-backed mmap 사용 중 truncate나 hole punching이 live mapping에 SIGBUS를 만든다.
- msync timing과 rename/replace update pattern이 durability와 visibility expectation을 흐린다.
- mapped file을 in-place update할지 새 file로 교체할지 판단이 필요하다.
expected_queries:
- mmap 파일을 운영에서 업데이트할 때 msync, hole punching, replace를 어떻게 다뤄?
- live mapping이 있는 파일에 truncate나 hole punch를 하면 왜 SIGBUS가 날 수 있어?
- mmap update pattern에서 rename atomicity와 directory fsync는 어디에 필요해?
- file-backed mmap은 어떻게 읽느냐보다 update pattern이 더 중요하다는 뜻은?
contextual_chunk_prefix: |
  이 문서는 file-backed mmap을 운영에 쓸 때 read path보다 msync timing, truncate/hole punching,
  live mapping replacement, rename atomicity, crash consistency가 더 중요해지는 update pattern
  playbook이다.
---
# mmap, msync, Hole Punching, File Replace Update Patterns

> 한 줄 요약: file-backed `mmap()`을 운영에 쓰는 순간 중요한 것은 "어떻게 읽느냐"보다 "언제 `msync`하고, 언제 hole punching/truncate/replace를 피하며, live mapping을 어떤 업데이트 패턴으로 바꿀 것인가"다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [MAP_SHARED vs MAP_PRIVATE Write Semantics](./mmap-map-shared-vs-map-private-write-semantics.md)
> - [mmap Shared, Truncate, SIGBUS, Coherency Pitfalls](./mmap-shared-truncate-sigbus-coherency-pitfalls.md)
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [Rename Atomicity, Directory fsync, Crash Consistency](./rename-atomicity-directory-fsync-crash-consistency.md)
> - [Sparse Files, fallocate, Hole Punching](./sparse-file-fallocate-hole-punching.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Deleted-but-Open Files, Log Rotation, Space Leak Debugging](./deleted-open-file-space-leak-log-rotation.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)

> retrieval-anchor-keywords: mmap update pattern, msync, msync visibility durability, msync invalidate, msync private mapping, MAP_SHARED vs MAP_PRIVATE, hole punching, punch hole keep size, fallocate punch hole, file replace, rename replace stale mapping, remap strategy, live mapping update, versioned remap, shared mapping publish, truncate safety, mapped file refresh, stale mmap reader, deleted old inode

## 핵심 개념

file-backed `mmap()`을 쓰는 시스템은 결국 "라이브 mapping을 어떻게 갱신할 것인가"라는 질문을 피할 수 없다. 이때 단순히 `msync()`를 더 자주 부르거나 `rename()`으로 새 파일을 바꾸는 것만으로는 충분하지 않다. hole punching, truncate, replace는 각각 전혀 다른 failure mode를 가진다.

- `msync`: mapped 변경을 backing file 쪽으로 반영하려는 동기화다
- `hole punching`: 파일 일부 블록을 다시 hole로 만들어 물리 사용량을 줄이는 기법이다
- `file replace`: temp file 작성 후 `rename()`으로 새 path를 publish하는 방식이다
- `remap strategy`: live mapping을 안전하게 새 backing object로 바꾸는 절차다

왜 중요한가:

- hot reload나 compaction 설계가 잘못되면 일부 워커만 stale mapping을 오래 볼 수 있다
- hole punching은 disk usage는 줄이지만 mapped reader에게는 위험한 의미를 가질 수 있다
- `msync()`는 visibility, durability, publish boundary를 모두 자동으로 해결해 주지 않는다

## 빠른 판단표

| 동작 | 실제로 바뀌는 것 | live mapping이 주로 겪는 일 | 흔한 오해 |
|------|------------------|------------------------------|-----------|
| `msync(MS_SYNC)` | 같은 inode의 dirty page를 backing file 쪽으로 동기화한다 | 같은 mapping/inode를 쓰는 reader는 이미 데이터를 볼 수 있을 수 있고, durability만 더 강해진다 | `msync()`가 reader handoff까지 대신해 준다고 생각한다 |
| `fallocate(PUNCH_HOLE + KEEP_SIZE)` | 파일 길이는 유지한 채 일부 블록만 hole로 바꾼다 | punched range가 zero-fill/re-fault 의미로 바뀔 수 있다 | hole punching만으로 곧바로 `SIGBUS`가 난다고 생각한다 |
| `ftruncate(smaller)` | `i_size`가 줄어든다 | 새 EOF 밖 페이지 접근이 `SIGBUS`가 될 수 있다 | 평범한 I/O 에러처럼만 실패할 거라고 생각한다 |
| `rename(tmp, live)` | pathname이 새 inode를 가리킨다 | 기존 mapping은 old inode를 계속 본다 | path replace가 live mapping refresh까지 해결한다고 생각한다 |
| `mremap()` | 같은 backing object의 VMA 크기/위치를 바꾼다 | 같은 파일 객체 안에서만 의미가 있다 | 새 inode로 갈아끼우는 remap 도구라고 생각한다 |

## 깊이 들어가기

### 1. `msync()`는 flush 도구이지 reader handoff 도구가 아니다

많은 설계가 `msync()`를 만능 동기화처럼 취급한다. 하지만 실제로는 질문을 더 분리해야 한다.

- 다른 프로세스가 언제 새 내용을 읽게 할 것인가
- crash 후 어떤 상태를 보장할 것인가
- live mapping을 계속 유지할 것인가, remap할 것인가

`MAP_SHARED`에서 같은 inode를 바라보는 mapping끼리는 page cache를 공유하므로, 다른 reader가 값을 "관측"하는 문제와 디스크에 "내구화"하는 문제를 분리해서 봐야 한다.

- `MS_SYNC`: dirty page writeback이 끝날 때까지 기다린다
- `MS_ASYNC`: writeback을 예약하고 빨리 돌아온다
- `MS_INVALIDATE`: 다른 cached view를 무효화하려 시도하지만, 새 inode로 reader를 바꿔 주지는 못한다

즉 `msync()`는 일부 flush 경계에는 도움을 주지만, "이제부터 모든 reader가 새 버전을 사용한다"는 publish protocol을 대신하지 않는다. rename 기반 replace라면 여전히 `fsync(new_fd)`와 parent directory `fsync(dirfd)`가 필요하고, live reader 전환은 별도 remap 절차가 필요하다.

### 2. hole punching과 `SIGBUS`는 같은 문제가 아니다

파일 블록을 punch hole하면 `du` 관점에서는 좋아 보일 수 있다. 하지만 mapping 사용자 입장에서는 다른 문제가 열린다.

- 일부 구간의 backing storage 의미가 바뀐다
- reader는 기존 레이아웃을 믿고 있을 수 있다
- compaction 이후 접근 패턴이 바뀌며 예기치 않은 fault/stale view가 생길 수 있다

특히 `fallocate(FALLOC_FL_PUNCH_HOLE | FALLOC_FL_KEEP_SIZE)`는 보통 파일 길이를 줄이지 않는다. 그래서 live mapping 쪽에서 더 흔한 현상은 다음이다.

- punched range를 읽을 때 zero-fill처럼 보인다
- 다시 접근하면서 refault와 tail latency가 늘어난다
- 파일 포맷이 "dense offset"을 전제하면 zero range를 정상 데이터로 오해한다

반대로 `SIGBUS`는 대체로 `i_size`가 줄어들었을 때 더 직접적으로 등장한다. 즉 "hole punching = 바로 `SIGBUS`"가 아니라, "hole punching = 의미가 바뀐 sparse 영역"에 가깝고, `truncate`가 섞일 때 `SIGBUS` 위험이 커진다.

그래서 hole punching은 storage reclaim 도구이면서 동시에 mapping contract 변경으로 봐야 한다.

### 3. rename replace는 path reader에게 좋지만 live mapping엔 부족하다

temp file을 만들고 `rename()`으로 교체하면 path reopen reader는 비교적 깔끔하다. 하지만 live mapping은 다르다.

- 기존 mapping은 old inode를 계속 본다
- 새 path를 여는 쪽만 new inode를 본다
- remap/version switch 없이 "자동 갱신"은 없다

여기서 자주 빠지는 부분이 old inode의 수명이다.

- old file이 unlink돼도 mapping이나 열린 fd가 남아 있으면 old inode는 살아 있다
- 그래서 space leak처럼 보이는 "deleted-but-still-mapped" 상태가 생길 수 있다
- `mremap()`은 기존 VMA를 옮기거나 키우는 도구일 뿐, 새 inode를 붙여 주는 API가 아니다

즉 replace는 publish layer이고, mapping refresh는 별도 layer다.

### 4. live remap/update는 "불변 스냅샷 전환" 쪽이 안전하다

대형 index나 dictionary 같은 read-mostly workload는 in-place 수정보다 "새 스냅샷 생성 후 전환"이 보통 더 안전하다.

- 새로운 파일/버전 생성
- file `fsync()` 후 `rename()` 및 directory `fsync()`
- 새 inode를 열어 새 mapping 준비
- header/footer/version을 검증한 뒤 readers를 점진적으로 새 mapping으로 전환
- old mapping을 쓰는 reader drain 후 old file 정리

즉 update protocol을 path 단위와 mapping 단위로 나눠 설계해야 한다.

### 5. 실전 패턴은 보통 세 가지로 압축된다

| 패턴 | 핵심 절차 | 장점 | 주의점 | 잘 맞는 곳 |
|------|-----------|------|--------|------------|
| immutable snapshot + rename + remap + drain | 새 파일 작성 -> `fsync` -> `rename` -> dir `fsync` -> 새 `mmap` -> atomic switch -> old drain | coherence 계약이 가장 명확하다 | generation/reader drain 관리가 필요하다 | 검색 index, rule table, config snapshot |
| append-only generation | 파일 뒤에 새 세그먼트/세대 추가 -> 완료 footer 기록 -> reader가 가장 최신 complete generation 선택 | truncate를 피하기 쉽다 | GC/compaction 설계가 필요하다 | 세대형 metadata, segment catalog |
| in-place shared mapping update | 고정 크기 구조체를 version/CRC/ready bit와 함께 갱신 | 파일 하나로 끝나 단순해 보인다 | torn state, publish ordering, partial durability를 직접 다뤄야 한다 | 작은 control block, 매우 통제된 환경 |

reader 쪽 불변식도 같이 두는 편이 좋다.

- mapping 길이는 path 재조회가 아니라 mapped header/footer 검증값으로 결정한다
- version/epoch를 보고 "완료된 세대"만 읽는다
- old mapping을 참조 중인 reader가 0이 되기 전에는 `munmap()`하지 않는다
- replace 직후 inode가 바뀌었는지, reader가 어느 세대를 보고 있는지 관측 지점을 남긴다

## 실전 시나리오

### 시나리오 1: compaction 후 일부 프로세스만 이상한 데이터나 `SIGBUS`를 본다

가능한 원인:

- hole punching과 truncate를 같은 단계에 섞었다
- punched range를 dense data로 가정하는 reader가 있다
- 실제 `SIGBUS` 원인은 file shrink인데, 문제를 hole punching 탓으로만 봤다
- old mapping drain 없이 backing object를 바꿨다
- `msync()`가 coherence를 해결해 줄 거라고 오해했다

판단 포인트:

- 파일 길이가 실제로 줄었는가
- 문제 구간이 sparse/hole인지 아니면 새 EOF 밖인지
- 장애 시점의 inode와 현재 path inode가 같은가

### 시나리오 2: 새 파일은 잘 publish됐는데 worker 절반은 계속 예전 index를 본다

가능한 원인:

- path reopen은 했지만 mapped reader는 remap하지 않았다
- live mapping refresh protocol이 없다
- replace와 mapping update를 같은 단계로 생각했다

진단:

```bash
stat -c '%i %s %n' live.index
grep live.index /proc/<pid>/maps
lsof +L1 | grep live.index
```

판단 포인트:

- 현재 path inode와 `/proc/<pid>/maps` inode가 다른가
- `(deleted)` old inode가 아직 살아 있는가
- reader switch가 refcount/epoch 없이 즉시 `munmap()`으로 끝나는가

### 시나리오 3: disk usage를 줄이려 hole punching을 넣었더니 tail latency가 나빠졌다

가능한 원인:

- reclaim은 되었지만 mapping/fault contract가 더 복잡해졌다
- sparse area 접근과 compaction timing이 겹쳤다
- readers가 old layout을 전제했다

판단 포인트:

- 장애가 crash인지, zero-fill 읽기인지, refault latency인지 구분했는가
- reclaim job이 hot range까지 punch하고 있지 않은가
- hole punching이 필요했던 이유가 실제 space pressure인지, deleted-old-inode 누수인지 분리했는가

### 시나리오 4: live remap은 했는데 드물게 mixed-version read가 나온다

가능한 원인:

- 새 mapping publish 전에 header/footer 검증을 안 했다
- reader가 acquire/release 없이 pointer만 읽는다
- old mapping drain 전에 writer가 old file을 정리했다

## 코드로 보기

### 위험한 mental model

```text
mapped file exists
  -> modify/truncate/punch/replace backing file
  -> call msync
  -> assume live readers are now coherent
```

### safer update model

```text
build new version
  -> validate header/footer/size
  -> fsync new file
  -> publish via rename
  -> fsync parent directory
  -> open new inode and create new mapping
  -> atomically switch readers to new generation
  -> drain old mapping
  -> reclaim old backing object
```

### reader/writer 역할 분리 의사 코드

```text
writer:
  new_file = build_immutable_snapshot()
  fsync(new_file)
  rename(new_file, live_path)
  fsync(parent_dir)
  new_map = mmap(open(live_path))
  validate(new_map.header, new_map.footer, new_map.len)
  publish(current_generation = new_map)
  wait_until(old_generation.readers == 0)
  munmap(old_generation)

reader:
  snap = acquire(current_generation)
  if !snap.ready or !snap.version_complete:
      retry
  read_using(snap.ptr, snap.len)
  release(snap)
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| in-place shared mapping update | 파일 하나로 끝나 단순해 보인다 | coherency, ordering, crash model을 직접 떠안는다 | very controlled environments |
| replace + remap | publish와 reader 전환이 분리된다 | versioning/orchestration 비용이 든다 | production mapped indexes |
| hole punching after compaction | disk usage를 줄일 수 있다 | zero-fill/sparse semantics와 latency가 복잡해진다 | reclaim-oriented storage paths |
| read() 기반 reload | 수명 모델이 단순하다 | copy 비용이 있다 | safer control plane/config paths |
| append-only generation | live truncate를 피하기 쉽다 | 공간 회수와 GC 설계가 필요하다 | log-ish metadata snapshots |

## 꼬리질문

> Q: `msync()`를 하면 live mapping update가 자동으로 안전해지나요?
> 핵심: 아니다. flush와 durability에는 도움을 주지만, reader switch와 새 inode adoption은 별도 프로토콜이 필요하다.

> Q: hole punching은 왜 mapped file에서 더 위험한가요?
> 핵심: 단순한 공간 회수가 아니라 reader가 믿는 backing layout을 sparse/zero-fill semantics로 바꾸기 때문이다.

> Q: hole punching을 하면 바로 `SIGBUS`가 나나요?
> 핵심: 보통은 아니다. `KEEP_SIZE`라면 더 흔한 증상은 zero range와 refault이고, `SIGBUS`는 주로 file shrink와 새 EOF 밖 접근에서 나온다.

> Q: rename replace는 왜 mapping 사용자에게 충분하지 않나요?
> 핵심: path는 바뀌어도 기존 mapping은 old inode/backing object를 계속 보기 때문이다.

> Q: `mremap()`으로 새 파일로 갈아끼울 수 있나요?
> 핵심: 아니다. `mremap()`은 같은 backing object의 VMA를 옮기거나 키우는 도구고, 새 inode로 바꾸려면 새 fd와 새 `mmap()`이 필요하다.

## 한 줄 정리

file-backed `mmap()` 갱신은 `msync()` 하나의 문제가 아니라, `msync`와 hole punching, truncate, rename이 각각 무엇을 바꾸는지 구분하고 publish protocol과 reader remap protocol을 분리하는 설계 문제다.
