---
schema_version: 3
title: Sparse Files fallocate Hole Punching
concept_id: operating-system/sparse-file-fallocate-hole-punching
canonical: true
category: operating-system
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- sparse-file-fallocate
- hole-punching
- logical-size-allocated
- blocks
aliases:
- sparse file fallocate hole punching
- logical size allocated blocks
- file hole punching
- preallocation
- disk usage mismatch
- WAL snapshot backup sparse
intents:
- deep_dive
- troubleshooting
- design
linked_paths:
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/mmap-msync-hole-punching-file-replace-update-patterns.md
- contents/operating-system/rename-atomicity-directory-fsync-crash-consistency.md
- contents/operating-system/deleted-open-file-space-leak-log-rotation.md
- contents/operating-system/fsync-tail-latency-dirty-writeback-debugging.md
expected_queries:
- sparse file의 logical size와 실제 allocated blocks는 왜 다를 수 있어?
- fallocate preallocation과 hole punching은 disk usage와 crash consistency에 어떤 영향을 줘?
- WAL, snapshot, backup에서 sparse file을 잘못 해석하면 어떤 문제가 생겨?
- mmap live mapping과 hole punching을 함께 쓰면 왜 위험할 수 있어?
contextual_chunk_prefix: |
  이 문서는 file logical size와 allocated block size가 다를 수 있으며 sparse file, fallocate
  preallocation, hole punching 차이를 모르면 WAL, snapshot, backup, disk alarm을 잘못 해석하기
  쉽다는 점을 설명한다.
---
# Sparse Files, fallocate, Hole Punching

> 한 줄 요약: 파일의 논리 크기와 실제 할당 블록은 다를 수 있고, sparse file·preallocation·hole punching의 차이를 모르면 WAL, snapshot, backup, disk alarm을 잘못 해석하기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Fsync Batching Semantics](./fsync-batching-semantics.md)
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [mmap, msync, Hole Punching, File Replace Update Patterns](./mmap-msync-hole-punching-file-replace-update-patterns.md)
> - [OverlayFS Copy-up, Container Layering, Runtime Debugging](./overlayfs-copy-up-container-layering-debugging.md)
> - [VFS, Dentry, Inode Cache Pressure](./vfs-dentry-inode-cache-pressure.md)

> retrieval-anchor-keywords: sparse file, fallocate, hole punching, preallocation, file apparent size, allocated blocks, du vs ls, SEEK_HOLE, WAL segment, delayed ENOSPC

## 핵심 개념

리눅스 파일은 "보이는 크기"와 "실제로 디스크 블록이 잡힌 양"이 다를 수 있다. 이 차이를 만드는 대표적인 기법이 sparse file, `fallocate()` 기반 preallocation, hole punching이다.

- `sparse file`: 중간에 hole이 있어도 논리적으로는 큰 파일처럼 보이는 파일이다
- `apparent size`: `ls -lh`에서 보이는 논리 크기다
- `allocated blocks`: 실제로 블록이 잡힌 양으로 `du`나 `stat`의 block 수로 본다
- `fallocate`: 파일시스템 지원이 있을 때 공간을 미리 확보하거나 hole을 다루는 시스템 콜이다
- `hole punching`: 파일 크기는 유지하면서 일부 블록을 다시 비워 두는 기법이다

왜 중요한가:

- WAL segment를 미리 만들 때 disk usage와 failure mode가 달라진다
- backup/copy 도구가 sparse를 보존하느냐에 따라 실제 사용량이 급증할 수 있다
- "파일이 100GB인데 왜 디스크는 안 찼지?" 또는 반대로 "왜 생성 순간 디스크가 바로 찼지?"를 설명할 수 있다

## 깊이 들어가기

### 1. 큰 파일이 항상 큰 디스크 사용량을 뜻하지는 않는다

`sparse file`은 hole 구간을 실제 블록 없이 표현하므로, 논리 크기는 커도 물리 사용량은 작을 수 있다.

- `truncate`로 크게 늘린 파일
- 일부 구간만 실제로 쓴 이미지 파일
- snapshot/segment 파일에서 비어 있는 영역

이때 `ls -lh`만 보면 과장된 위기감을 느끼고, `du -h`만 보면 반대로 미래 위험을 과소평가할 수 있다.

### 2. sparse와 preallocation은 비슷해 보여도 운영 의미가 다르다

둘 다 "미래에 커질 파일"을 다루지만 의도와 failure mode가 다르다.

- sparse: 지금은 블록을 덜 쓰지만, 나중에 실제 write 시점에 공간이 필요하다
- preallocation: 지금 미리 공간을 확보해 later ENOSPC 위험과 fragmentation을 줄인다
- `FALLOC_FL_KEEP_SIZE` 같은 방식은 visible size와 reserved blocks를 분리할 수 있다

즉 sparse는 낙관적 예약이고, preallocation은 비용을 앞당겨 확정하는 선택에 가깝다.

### 3. hole punching은 "지웠다"와 "크기가 줄었다"를 분리한다

hole punching은 특정 범위의 블록을 다시 hole로 바꿔 실제 사용량을 줄일 수 있지만, 파일의 논리 크기 자체는 그대로일 수 있다.

- `ls -lh`는 거의 안 바뀔 수 있다
- `du -h`는 줄 수 있다
- 일부 파일시스템/마운트 옵션에서 지원과 성능 특성이 다르다

그래서 디스크 사용률 알람과 파일 크기 알람을 같은 의미로 보면 판단이 흔들린다.

### 4. copy/backup/snapshot 도구가 sparse 의미를 깨뜨릴 수 있다

파일을 옮길 때 hole 정보를 보존하지 않으면 빈 공간이 실제 zero block으로 확장될 수 있다.

- 원본은 sparse라서 디스크를 적게 썼다
- 복사본은 sparse를 보존하지 않아 실제 블록이 커졌다
- backup 저장소나 restore 시간에서 뜻밖의 비용이 나타난다

즉 sparse file은 생성 전략뿐 아니라 이동 전략까지 함께 설계해야 한다.

## 실전 시나리오

### 시나리오 1: WAL segment가 엄청 커 보여서 디스크가 곧 찰 것 같다

확인할 점:

- 논리 크기만 큰 sparse file인지
- `fallocate()`로 이미 블록을 예약한 것인지
- WAL rotation과 archive 도구가 sparse를 어떻게 다루는지

진단:

```bash
ls -lh wal.segment
du -h wal.segment
du -h --apparent-size wal.segment
stat -c '%n size=%s blocks=%b blksize=%B' wal.segment
```

### 시나리오 2: 백업을 복사했더니 대상 볼륨이 갑자기 가득 찼다

가능한 원인:

- 원본은 sparse였지만 복사 도구가 hole을 보존하지 않았다
- restore 과정에서 zero 영역이 실제 블록으로 할당됐다
- snapshot 레이어나 overlay 환경이 블록 의미를 바꿨다

### 시나리오 3: compaction 후 디스크 사용량은 줄었는데 파일 크기는 그대로다

가능한 원인:

- hole punching으로 블록만 반납했다
- 논리 크기 기준 모니터링과 물리 사용량 기준 모니터링이 다르다
- 앱은 size를 보고, 운영자는 block usage를 봐야 하는 상황이다

## 코드로 보기

### sparse file 만들기

```bash
truncate -s 10G sparse.img
ls -lh sparse.img
du -h sparse.img
du -h --apparent-size sparse.img
```

### preallocation 예시

```bash
fallocate -l 10G wal.segment
stat -c '%n size=%s blocks=%b blksize=%B' wal.segment
```

### 해석 감각

```text
logical size grows
  != physical blocks necessarily grow

future write into hole
  -> may allocate blocks later

preallocation now
  -> pays space cost early to reduce later allocation surprise
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| sparse file | 초기 공간 사용이 적다 | 나중에 ENOSPC나 copy inflation이 터질 수 있다 | 이미지, 일부 snapshot |
| preallocation | late allocation surprise를 줄인다 | 생성 시 디스크 비용이 바로 든다 | WAL, 대형 segment |
| hole punching | 물리 사용량을 줄일 수 있다 | 파일 크기와 usage 해석이 복잡해진다 | compaction, reclaim |
| 단순 zero-write | 직관적이다 | 느리고 fragmentation이 생길 수 있다 | 작은 파일 또는 단순 구현 |

## 꼬리질문

> Q: `ls -lh`와 `du -h`가 왜 다르게 보이나요?
> 핵심: 전자는 논리 크기, 후자는 실제 할당 블록 기준이라 sparse/hole 여부에 따라 달라진다.

> Q: sparse file이 항상 좋은가요?
> 핵심: 아니다. 초기 공간은 아끼지만 later write 시점 ENOSPC나 복사 비용을 뒤로 미룰 수 있다.

> Q: hole punching을 했는데 파일 크기가 왜 그대로인가요?
> 핵심: 블록만 반납하고 논리 크기는 유지하는 방식이기 때문이다.

## 한 줄 정리

sparse file과 `fallocate()` 전략은 디스크를 "지금 쓸지 나중에 쓸지"를 결정하는 선택이며, 파일 크기와 실제 블록 사용량을 분리해서 읽는 습관이 핵심이다.
