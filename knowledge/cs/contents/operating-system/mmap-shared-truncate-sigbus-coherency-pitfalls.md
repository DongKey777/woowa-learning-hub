---
schema_version: 3
title: mmap Shared Truncate SIGBUS Coherency Pitfalls
concept_id: operating-system/mmap-shared-truncate-sigbus-coherency-pitfalls
canonical: true
category: operating-system
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- mmap-shared-truncate
- sigbus-coherency-pitfalls
- mmap-truncate-sigbus
- map-shared-coherency
aliases:
- mmap truncate SIGBUS
- MAP_SHARED coherency
- stale mmap mapping
- external writer visibility
- file-backed mmap pitfall
- EOF beyond mapping SIGBUS
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/mmap-vs-read-page-cache-behavior.md
- contents/operating-system/mmap-map-shared-vs-map-private-write-semantics.md
- contents/operating-system/mmap-msync-hole-punching-file-replace-update-patterns.md
- contents/operating-system/posix-fadvise-madvise-page-cache-hints.md
- contents/operating-system/rename-atomicity-directory-fsync-crash-consistency.md
symptoms:
- mmap 영역을 읽던 중 file truncate나 replace 뒤 SIGBUS가 난다.
- MAP_SHARED와 external writer visibility timing을 일반 memory write처럼 기대한다.
- msync, stale mapping, coherency 문제가 섞여 file update 후 reader가 다른 값을 본다.
expected_queries:
- mmap된 파일이 truncate되면 EOF 밖 접근에서 왜 SIGBUS가 날 수 있어?
- MAP_SHARED mmap은 external writer와 coherency timing을 어떻게 보장하거나 보장하지 않아?
- stale mapping과 msync, rename replace update pattern을 어떻게 구분해?
- file-backed mmap failure mode를 page cache와 SIGBUS 관점에서 설명해줘
contextual_chunk_prefix: |
  이 문서는 mmap이 file을 memory처럼 보이게 하지만 truncate, MAP_SHARED, msync, external writer,
  file replacement가 섞이면 EOF 밖 접근 SIGBUS, visibility timing, stale mapping 같은
  별도 failure mode가 생긴다는 점을 라우팅한다.
---
# mmap Shared, Truncate, SIGBUS, Coherency Pitfalls

> 한 줄 요약: `mmap()`은 파일을 메모리처럼 보이게 하지만, `truncate`, `MAP_SHARED`, `msync`, external writers가 섞이면 EOF 밖 접근의 `SIGBUS`, visibility timing, stale mapping 같은 전혀 다른 실패 모드를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [MAP_SHARED vs MAP_PRIVATE Write Semantics](./mmap-map-shared-vs-map-private-write-semantics.md)
> - [mmap, msync, Hole Punching, File Replace Update Patterns](./mmap-msync-hole-punching-file-replace-update-patterns.md)
> - [posix_fadvise, madvise, Page Cache Hints](./posix-fadvise-madvise-page-cache-hints.md)
> - [Rename Atomicity, Directory fsync, Crash Consistency](./rename-atomicity-directory-fsync-crash-consistency.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)

> retrieval-anchor-keywords: mmap coherency, MAP_SHARED, truncate mmap, SIGBUS, msync, file-backed mapping, stale mapping, shared mapping visibility, truncation fault, mmap pitfalls

## 핵심 개념

`mmap()`은 file-backed data를 메모리처럼 접근하게 해 주지만, file size 변화와 mapping lifetime은 `read()`와 완전히 다르게 실패한다. 특히 `MAP_SHARED`와 file truncate/replace가 섞이면 "파일이 없거나 작아졌다"가 에러 코드가 아니라 `SIGBUS`나 stale mapping처럼 나타날 수 있다.

- `MAP_SHARED`: mapping의 변경이 file과 공유될 수 있는 모드다
- `MAP_PRIVATE`: copy-on-write 성격의 private mapping이다
- `truncate/ftruncate`: 파일 길이를 줄이거나 늘리는 동작이다
- `SIGBUS`: mapped object access가 유효하지 않을 때 올 수 있는 시그널이다
- `msync`: mapped 변경을 backing file에 반영하도록 요청하는 동기화다

왜 중요한가:

- hot reload나 compaction이 mapping 사용자에게 fatal signal로 돌아올 수 있다
- "rename으로 교체했으니 안전하다"가 mapping 사용자에게는 틀릴 수 있다
- file-backed shared memory를 데이터 구조처럼 다루면 coherency contract를 직접 설계해야 한다

## 깊이 들어가기

### 1. `mmap()`의 참조는 fd close와 별개로 살아남을 수 있다

mapping이 생기면 그 파일 객체에 대한 참조는 fd close와 수명이 분리될 수 있다.

- fd를 닫아도 mapping은 계속 쓸 수 있다
- 그래서 path lifecycle과 mapping lifecycle이 어긋날 수 있다
- reload/cleanup 코드가 fd만 닫고 안심하면 안 된다

즉 `mmap`은 "fd 기반 수명"보다 더 긴 메모리 참조를 만든다.

### 2. truncate는 mapping 사용자에게 `SIGBUS`로 보일 수 있다

mapped file의 끝 이후 whole page를 건드리면 `SIGBUS`가 날 수 있다. 따라서 다른 프로세스/스레드가 파일을 줄이면 mapping 쪽은 평범한 I/O error가 아니라 signal crash처럼 보일 수 있다.

- file size가 줄었다
- mapping은 예전 길이를 믿는다
- EOF 뒤 페이지 접근이 `SIGBUS`가 된다

이 failure mode는 `read()` 기반 코드와 완전히 다르다.

### 3. `MAP_SHARED` visibility는 동시성 계약 문제다

shared mapping은 "보인다/안 보인다"의 타이밍을 명시적으로 설계해야 한다.

- 어떤 필드를 먼저 쓰는가
- publish boundary를 무엇으로 삼는가
- `msync`가 durability인지 visibility인지

즉 `MAP_SHARED`는 빠른 공유 경로이면서 동시에 userspace-level memory model 문제다.

### 4. rename 교체와 mapping은 독립이다

rename으로 path를 바꿔도 기존 mapping은 old inode를 계속 볼 수 있다.

- 새로 open하는 쪽은 new file을 본다
- 기존 mapping은 old backing object를 계속 본다
- "atomic replace"가 mapping coherence까지 해결해 주지는 않는다

그래서 mapped file hot reload는 path atomicity와 mapping lifecycle을 따로 설계해야 한다.

## 실전 시나리오

### 시나리오 1: compaction/rotate 후 가끔 프로세스가 `SIGBUS`로 죽는다

가능한 원인:

- mapped file이 truncate되었다
- reader가 old size를 믿고 EOF 밖 페이지를 접근했다
- reload 절차가 `read()` 사고방식으로 작성되었다

진단:

```bash
ls -l /proc/<pid>/maps
cat /proc/<pid>/smaps | head -n 40
dmesg | tail
```

판단 포인트:

- 최근 truncate/compaction이 있었는가
- crash signal이 `SIGBUS`인가
- mapping 수명이 file replacement 수명보다 긴가

### 시나리오 2: 파일은 교체됐는데 일부 worker는 계속 예전 내용을 본다

가능한 원인:

- worker가 old inode를 mapping으로 계속 보고 있다
- rename 후 reopen은 했지만 remap은 안 했다
- path atomicity와 mapping coherence를 혼동했다

### 시나리오 3: shared mapping write 후 다른 프로세스 관측 시점이 애매하다

가능한 원인:

- publish ordering 설계가 없다
- durable flush와 visibility boundary를 섞었다
- shared data structure의 versioning이 없다

## 코드로 보기

### 위험한 mental model

```text
map file once
  -> treat it like ordinary memory forever
  -> someone truncates/replaces file
  -> mapping user still believes old layout
  -> SIGBUS or stale data
```

### safer questions

```text
Can the backing file size change while mappings are live?
Who owns remap/reload?
Is msync about visibility, durability, or both in this design?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `mmap()` shared file | copy를 줄이고 random access가 편하다 | truncate/coherency failure mode가 복잡하다 | index/cache-like structures |
| `read()` + explicit buffer | lifetime이 단순하다 | copy 비용이 있다 | predictable reload and errors |
| rename-only publish | path atomicity는 좋다 | live mappings는 old inode를 계속 본다 | path-based readers |
| versioned remap design | coherence를 통제하기 쉽다 | 구현 복잡도가 오른다 | shared mapped data |

## 꼬리질문

> Q: mapped file을 truncate하면 왜 `SIGBUS`가 날 수 있나요?
> 핵심: mapping이 믿는 범위와 실제 파일 끝이 어긋나며 EOF 뒤 페이지 접근이 invalid mapping access가 되기 때문이다.

> Q: rename으로 새 파일로 바꾸면 기존 mapping도 자동으로 새 내용을 보나요?
> 핵심: 아니다. 기존 mapping은 old inode/backing object를 계속 볼 수 있다.

> Q: `msync`는 visibility와 durability를 동시에 해결하나요?
> 핵심: 항상 그런 식으로 단순화하면 안 된다. 설계에서 어떤 경계를 원하는지 분리해서 봐야 한다.

## 한 줄 정리

`mmap()` 기반 설계는 빠를 수 있지만, path 교체나 truncate가 섞이는 순간 `read()`와 전혀 다른 coherency와 `SIGBUS` failure mode를 감당해야 한다.
