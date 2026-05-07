---
schema_version: 3
title: MAP_SHARED vs MAP_PRIVATE Write Semantics
concept_id: operating-system/mmap-map-shared-vs-map-private-write-semantics
canonical: true
category: operating-system
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- mmap-map-shared
- vs-map-private
- write-semantics
- map-shared-vs
aliases:
- MAP_SHARED vs MAP_PRIVATE
- mmap write semantics
- file-backed mmap COW
- shared mapping dirty page cache
- private mapping anonymous COW
- mmap peer visibility
intents:
- comparison
- deep_dive
- troubleshooting
linked_paths:
- contents/operating-system/mmap-vs-read-page-cache-behavior.md
- contents/operating-system/fork-exec-copy-on-write-behavior.md
- contents/operating-system/major-minor-page-faults-runtime-diagnostics.md
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/mmap-shared-truncate-sigbus-coherency-pitfalls.md
confusable_with:
- operating-system/mmap-vs-read-page-cache-behavior
- operating-system/mmap-shared-truncate-sigbus-coherency-pitfalls
- operating-system/fork-exec-copy-on-write-behavior
expected_queries:
- MAP_SHARED와 MAP_PRIVATE write는 page cache와 COW에서 어떻게 달라?
- file-backed mmap에서 MAP_PRIVATE write는 왜 anonymous COW page로 갈라져?
- MAP_SHARED write는 peer visibility와 writeback에 어떤 기대를 만들어?
- mmap write semantics를 RSS, page fault, dirty writeback 관점에서 비교해줘
contextual_chunk_prefix: |
  이 문서는 file-backed mmap에서 MAP_SHARED write는 page cache를 dirty하게 만들고,
  MAP_PRIVATE write는 그 순간 anonymous COW page로 갈라져 writeback, RSS, peer visibility
  기대가 완전히 달라진다는 점을 비교한다.
---
# MAP_SHARED vs MAP_PRIVATE Write Semantics

> 한 줄 요약: file-backed `mmap()`에서 `MAP_SHARED` write는 page cache를 더럽히고, `MAP_PRIVATE` write는 그 순간부터 익명 COW 페이지로 갈라지므로 writeback, RSS, peer visibility 기대치가 완전히 달라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [Fork, Exec, Copy-on-Write Behavior](./fork-exec-copy-on-write-behavior.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [page cache, dirty writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [mmap Shared, Truncate, SIGBUS, Coherency Pitfalls](./mmap-shared-truncate-sigbus-coherency-pitfalls.md)
> - [mmap, msync, Hole Punching, File Replace Update Patterns](./mmap-msync-hole-punching-file-replace-update-patterns.md)
> - [Buffered vs Direct I/O Mixing, Coherency Pitfalls](./buffered-vs-direct-io-mixing-coherency-pitfalls.md)

> retrieval-anchor-keywords: mmap write semantics, MAP_SHARED vs MAP_PRIVATE, shared mapping dirty page, private mapping COW, file-backed COW boundary, private dirty vs shared dirty, anonymous COW page, page cache writeback, msync private mapping, mmap coherency expectations

## 핵심 개념

`MAP_SHARED`와 `MAP_PRIVATE`는 둘 다 file-backed page를 address space에 붙인다는 점에서는 비슷하게 시작한다. 차이는 첫 write가 일어나는 순간에 드러난다.

- `MAP_SHARED`: write가 backing file의 page cache page를 더럽힌다
- `MAP_PRIVATE`: write가 page 단위 copy-on-write를 일으켜 익명 페이지로 분리된다
- 둘 다 "한 바이트만 썼다"고 느껴도 커널은 page 단위로 상태를 바꾼다

왜 중요한가:

- 같은 `mmap()` 코드라도 `Dirty/Writeback` 압박인지 `RSS` 증가인지가 갈린다
- `msync()`를 commit 도구로 볼 수 있는지 여부가 달라진다
- 다른 프로세스가 무엇을 볼 수 있는지, 언제 remap이 필요한지가 달라진다

핵심은 "`MAP_PRIVATE`가 처음부터 전체 복사본을 만드는 것"이 아니라는 점이다. read path는 한동안 같은 file-backed page를 재사용할 수 있고, divergence는 첫 write가 발생한 page마다 따로 생긴다.

## 빠른 판단표

| 질문 | `MAP_SHARED` | `MAP_PRIVATE` |
|------|--------------|---------------|
| 처음 읽는 데이터 원천 | 보통 page cache의 file-backed page | 보통 page cache의 file-backed page |
| clean page에 첫 write가 나면 | 해당 page cache page를 dirty로 만든다 | page-fault 후 익명 페이지를 할당하고 전체 page를 복사한다 |
| dirty 바이트는 어디에 쌓이나 | file-backed page cache / writeback 경로 | process RSS 안의 anonymous page / swap 경로 |
| 다른 shared mapper나 `read()`가 볼 수 있나 | 같은 inode/page cache를 보면 볼 수 있지만 publish ordering은 별도다 | 아니다. private COW가 난 page는 파일과 분리된다 |
| backing file이 바뀌나 | 그렇다. writeback 시 파일 내용이 바뀔 수 있다 | 아니다. private write는 파일을 바꾸지 않는다 |
| `msync()`의 의미 | durability/writeback 경계를 강화한다 | private COW page를 파일에 반영하는 commit 도구가 아니다 |
| 메모리 비용의 단위 | dirty page cache page | write한 각 page마다 anonymous copy |

## 깊이 들어가기

### 1. 둘 다 처음에는 같은 file-backed page를 볼 수 있다

file-backed mapping은 보통 page cache에 있는 파일 페이지를 VMA에 붙인다.

- 아직 아무도 쓰지 않았다면 `MAP_SHARED`와 `MAP_PRIVATE` 모두 같은 clean page를 읽을 수 있다
- 그래서 read-mostly workload에서는 겉으로 비슷하게 보일 수 있다
- 구분점은 `mmap()` 호출 순간이 아니라 page별 first write다

즉 `MAP_PRIVATE`는 "즉시 전체 복사"가 아니라 "필요해진 page만 나중에 분기"다.

### 2. `MAP_SHARED` write는 page cache를 dirty하게 만든다

`MAP_SHARED`로 매핑한 page에 write하면 그 page는 backing file의 shared state 일부가 된다.

- 해당 page cache page가 dirty가 된다
- 나중에 background writeback, `msync()`, `fsync()` 같은 경로로 디스크에 내려갈 수 있다
- 다른 프로세스가 같은 inode를 `MAP_SHARED`로 매핑했거나 `read()`로 읽으면 업데이트된 page cache를 관측할 수 있다

하지만 여기서 "관측할 수 있다"와 "일관되게 안전하게 읽는다"는 다르다.

- 여러 필드를 순서대로 갱신하면 reader는 중간 상태를 볼 수 있다
- `msync()`는 durability 경계를 다루지, record-level publish protocol을 대신하지 않는다
- cross-process shared structure라면 lock, seqlock, version, ready bit 같은 userspace contract가 필요하다

즉 `MAP_SHARED`는 coherence channel이지 transaction channel이 아니다.

### 3. `MAP_PRIVATE` write는 page마다 COW 경계를 만든다

`MAP_PRIVATE` mapping에 write가 들어오면 커널은 file-backed page를 그대로 바꾸지 않는다. 대신 그 page만 익명 메모리로 분리한다.

- write fault가 난다
- 새 anonymous page를 할당한다
- 기존 file-backed page 내용을 page 전체 크기만큼 복사한다
- 이후 해당 mapping은 그 page를 private anonymous memory로 본다

중요한 결과:

- 파일은 바뀌지 않는다
- 다른 프로세스는 그 write를 보지 못한다
- 한 바이트를 고쳐도 보통 4 KiB 같은 page 하나 전체가 RSS로 추가된다
- 아직 write하지 않은 다른 page들은 계속 file-backed 상태로 남을 수 있다

따라서 `MAP_PRIVATE`는 mapping 전체가 한 번에 private해지는 것이 아니라, dirty한 page만 조금씩 private해진다.

### 4. COW는 page 단위이며, fork와 겹치면 한 번 더 생길 수 있다

`MAP_PRIVATE`로 인해 이미 anonymous COW page가 생긴 뒤 `fork()`가 일어나면, 그 anonymous page는 다시 parent/child 사이에서 COW 대상이 될 수 있다.

- 1차 COW: file-backed page -> private anonymous page
- 2차 COW: fork 후 parent/child가 같은 anonymous page를 공유하다가 다시 split

그래서 minor fault가 많다고 해서 항상 같은 원인은 아니다. file-backed private mapping을 만져서 생긴 fault인지, fork 이후 anon page를 다시 split한 fault인지 구분해야 한다.

### 5. `MAP_PRIVATE`는 안정적인 "live file update 구독" 수단이 아니다

실무에서 자주 나오는 오해는 "`MAP_PRIVATE`니까 외부 writer가 파일을 바꿔도 나는 안전한 snapshot을 본다"는 생각이다. 그 정도로 단순하지 않다.

- 아직 private COW가 나지 않은 clean page는 file-backed state와 얽혀 있다
- 외부의 `write()`/`pwrite()`/truncate/replace를 coherent update stream처럼 기대하면 안 된다
- 특정 시점 snapshot contract가 필요하면 immutable file + reopen/remap 절차를 명시해야 한다

즉 `MAP_PRIVATE`는 "내 write가 파일로 전파되지 않는다"는 계약이지, "외부 파일 갱신이 정의된 방식으로 보인다"는 계약이 아니다.

### 6. dirty 관측 지점도 다르게 읽어야 한다

같은 "mmap write가 많다"는 증상이라도 커널이 보여 주는 지표는 다르다.

- `MAP_SHARED` 문제면 `/proc/meminfo`의 `Dirty`, `Writeback`, backing device queue를 본다
- `MAP_PRIVATE` 문제면 `/proc/<pid>/smaps`의 `Private_Dirty`, `Anonymous`, RSS 증가를 본다
- `perf stat -e minor-faults`는 private COW burst를 잡는 데 도움이 된다

즉 shared mapping은 I/O와 durability 쪽, private mapping은 memory footprint와 COW churn 쪽으로 읽어야 한다.

## 실전 시나리오

### 시나리오 1: `MAP_PRIVATE`로 수정하고 `msync()`까지 했는데 파일은 안 바뀐다

가능한 원인:

- private COW page만 바꿨다
- `msync()`를 file commit 도구로 오해했다
- 테스트는 같은 프로세스 메모리만 보고 끝냈다

진단:

```bash
grep -A20 '<mapped-file>' /proc/<pid>/smaps
grep -E 'Private_Dirty|Shared_Dirty' /proc/<pid>/smaps_rollup
```

판단 포인트:

- `Private_Dirty`가 늘고 `Dirty/Writeback`은 거의 안 느는가
- 파일을 다시 열어 읽으면 변경이 없는가

### 시나리오 2: 큰 파일에서 page마다 한 바이트만 만졌는데 RSS가 급증한다

가능한 원인:

- `MAP_PRIVATE` page-by-page COW가 터졌다
- "조금만 수정"이라는 애플리케이션 감각과 page 단위 accounting이 어긋난다

진단:

```bash
perf stat -p <pid> -e minor-faults,page-faults -- sleep 30
grep -E 'Rss|Private_Dirty|Anonymous' /proc/<pid>/smaps_rollup
```

핵심:

- 1 byte write라도 page 하나 전체가 private RSS가 된다

### 시나리오 3: 두 프로세스가 같은 mapped metadata를 보는데 가끔 torn read가 나온다

가능한 원인:

- `MAP_SHARED`로 visibility만 열어 두고 publish ordering은 설계하지 않았다
- header, payload, ready bit를 무잠금으로 순서 없이 갱신했다
- `msync()`가 coherence까지 해결한다고 생각했다

판단 포인트:

- reader가 version/ready bit를 보고 재시도하는가
- cross-process atomic ordering을 보장하는가
- writer가 "보이게 하는 시점"과 "디스크에 내리는 시점"을 분리했는가

## 코드로 보기

### `MAP_SHARED`: file-backed dirty page

```c
char *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
p[0] = 'X';   // page cache page가 dirty가 된다
msync(p, len, MS_SYNC);  // durability/writeback 경계 강화
```

### `MAP_PRIVATE`: page-by-page anonymous COW

```c
char *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, 0);
p[0] = 'X';   // file-backed page를 직접 바꾸지 않고 private COW page로 분리
msync(p, len, MS_SYNC);  // private write를 파일 commit으로 바꾸지 못한다
```

### mental model

```text
clean file-backed page
  -> MAP_SHARED write
     -> same page cache page becomes dirty
     -> peer mappings may observe
     -> writeback can persist it

clean file-backed page
  -> MAP_PRIVATE write
     -> allocate anonymous page
     -> copy whole page
     -> only this mapping sees the new bytes
     -> backing file is unchanged
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `MAP_SHARED` | shared cache reuse와 zero-copy style update 경로가 된다 | publish ordering, writeback, truncate/reload contract를 직접 설계해야 한다 | shared memory file, read-mostly shared structures |
| `MAP_PRIVATE` | 파일을 더럽히지 않고 local patch/scratch view를 만들 수 있다 | page 단위 COW로 RSS가 커지고 peer coherence가 끊긴다 | local transform, parser scratch, per-process view |
| immutable file + remap | snapshot contract가 명확하다 | build/publish/remap orchestration이 필요하다 | index, dictionary, config snapshot |
| `read()` + explicit buffer | 수명과 write semantics가 단순하다 | copy 비용이 있다 | control plane, simpler failure modes |

## 꼬리질문

> Q: `MAP_PRIVATE`는 `mmap()` 시점의 파일 snapshot이라고 봐도 되나요?
> 핵심: 안전한 계약으로 보면 안 된다. private한 것은 "내 write path"이고, external file update visibility는 별도 설계가 필요하다.

> Q: 왜 한 바이트만 써도 메모리가 많이 늘 수 있나요?
> 핵심: COW 경계가 byte가 아니라 page이기 때문이다.

> Q: `msync()`를 부르면 `MAP_PRIVATE` 변경도 파일에 저장되나요?
> 핵심: commit primitive로 기대하면 안 된다. private COW page는 backing file writeback 경로와 다르다.

> Q: `MAP_SHARED`면 다른 프로세스가 언제든 안전하게 새 값을 읽나요?
> 핵심: 보일 수는 있어도 torn state 없이 읽는 것은 별도 publish protocol 문제다.

## 한 줄 정리

`MAP_SHARED`는 file-backed page cache를 dirty하게 만들어 writeback과 peer visibility 계약으로 이어지고, `MAP_PRIVATE`는 first write마다 anonymous COW page로 갈라져 파일, RSS, coherency 기대치를 바로 분리한다.
