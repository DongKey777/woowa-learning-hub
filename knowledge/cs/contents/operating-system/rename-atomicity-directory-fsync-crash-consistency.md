# Rename Atomicity, Directory fsync, Crash Consistency

> 한 줄 요약: `rename()`은 이름 교체를 atomic하게 보이게 할 수 있지만, crash-safe publish까지 자동으로 보장하지는 않으므로 file `fsync()`와 parent directory `fsync()`를 분리해서 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Fsync Batching Semantics](./fsync-batching-semantics.md)
> - [Fsync Tail Latency, Dirty Writeback, Backend Debugging](./fsync-tail-latency-dirty-writeback-debugging.md)
> - [Deleted-but-Open Files, Log Rotation, Space Leak Debugging](./deleted-open-file-space-leak-log-rotation.md)
> - [mmap, msync, Hole Punching, File Replace Update Patterns](./mmap-msync-hole-punching-file-replace-update-patterns.md)
> - [Sparse Files, fallocate, Hole Punching](./sparse-file-fallocate-hole-punching.md)
> - [OverlayFS Copy-up, Container Layering, Runtime Debugging](./overlayfs-copy-up-container-layering-debugging.md)

> retrieval-anchor-keywords: rename atomicity, directory fsync, parent directory fsync, crash consistency, temp file replace, durable rename, EXDEV, atomic publish, file replacement, config swap

## 핵심 개념

백엔드 시스템은 config snapshot, manifest, segment pointer, generated asset 같은 파일을 "교체"하는 일을 자주 한다. 이때 흔히 `write -> rename`만 떠올리지만, 운영적으로는 다음 세 층을 구분해야 한다.

- namespace atomicity: 새 이름이 한 번에 보이느냐
- file durability: 새 파일의 내용이 디스크에 안정적으로 내려갔느냐
- directory durability: 이름 변경 사실이 디렉터리 엔트리까지 안정적으로 반영됐느냐

왜 중요한가:

- 프로세스 관점에서는 교체가 atomic해 보여도 crash 후엔 old/new 어느 쪽도 보장되지 않을 수 있다
- open 중인 old fd는 rename 이후에도 계속 old inode를 볼 수 있다
- cross-device 경로에서는 `rename()` 자체가 성립하지 않아 다른 failure mode가 생긴다

## 깊이 들어가기

### 1. `rename()`의 atomicity는 "보이는 이름"에 대한 약속이다

같은 파일시스템 안에서의 `rename()`은 대개 "기존 경로가 있었으면 새 경로로 교체되고, 중간 반쯤 보이는 상태는 없다"는 namespace atomicity를 준다.

- 새로운 open은 old 또는 new 중 하나를 본다
- 기존에 열려 있던 old fd는 계속 old inode를 볼 수 있다
- 그래서 reader cutover에는 유용하다

하지만 이것만으로 crash consistency까지 보장된다고 생각하면 위험하다.

### 2. file `fsync()`와 directory `fsync()`는 역할이 다르다

많이 놓치는 지점이 이것이다.

- file `fsync(fd)`: 새 파일의 데이터와 관련 메타데이터를 안정화하려는 단계다
- directory `fsync(dirfd)`: rename/create/unlink 같은 이름 공간 변경을 안정화하려는 단계다

즉 temp file을 다 쓴 뒤 file만 `fsync()`하고 `rename()`만 하면, 런타임에서는 교체가 성공해 보여도 crash 후 디렉터리 엔트리 반영까지 완전히 보장되지 않을 수 있다.

### 3. crash-safe replace 패턴은 temp file + file fsync + rename + dir fsync다

가장 자주 쓰는 안전 패턴은 다음이다.

1. 대상과 같은 디렉터리에 temp file 생성
2. temp file에 새 내용 쓰기
3. temp file `fsync()`
4. `rename(temp, target)`
5. parent directory `fsync()`

이 순서를 어기면 다음 문제가 생긴다.

- temp가 다른 파일시스템에 있으면 `EXDEV`
- file `fsync()` 없이 rename하면 새 파일 내용이 덜 안정적일 수 있다
- dir `fsync()` 없이 끝내면 name publish가 crash 후 흔들릴 수 있다

### 4. atomic replace와 concurrent readers는 별개 문제다

rename은 reader에게 "절반짜리 파일"을 덜 보여 주는 데 유용하지만, reader가 이미 열어 둔 fd가 있으면 그 reader는 old inode를 계속 볼 수 있다.

- config reload는 next open부터 새 파일을 본다
- long-lived reader는 old fd를 유지할 수 있다
- inotify/epoll와 결합하면 cutover 감각이 더 중요해진다

즉 atomic publish는 path 기준이지, 이미 열린 descriptor 기준이 아니다.

## 실전 시나리오

### 시나리오 1: snapshot publish는 성공했는데 crash 후 파일이 이상하다

가능한 원인:

- file `fsync()` 없이 `rename()`만 했다
- directory `fsync()`를 빠뜨렸다
- temp file이 다른 mount/volume에 있었다

진단 감각:

- temp file 경로와 target 경로가 같은 디렉터리/같은 파일시스템인가
- write -> fsync -> rename -> dir fsync 순서를 지켰는가
- 장애가 "이름 바뀜" 문제인지 "내용 덜 내려감" 문제인지 분리했는가

### 시나리오 2: config hot-reload 직후 일부 워커만 old file을 계속 본다

가능한 원인:

- 워커가 이미 old fd를 열고 있었다
- path reopen 시점이 제각각이다
- atomic rename을 "모든 reader가 동시에 새 내용 사용"으로 오해했다

이 경우는 storage semantics보다 descriptor lifecycle과 reload strategy 문제다.

### 시나리오 3: `/tmp`에 쓰고 `rename()`했더니 운영 환경에서만 실패한다

가능한 원인:

- `/tmp`와 target 경로가 다른 파일시스템이다
- `rename()`가 `EXDEV`로 실패한다
- 일부 라이브러리가 fallback copy+unlink로 바꿔 atomicity를 잃는다

대응 감각:

- temp file은 target과 같은 디렉터리 또는 같은 mount 아래에 둔다
- fallback copy가 crash-safe replace와 같다고 착각하지 않는다

## 코드로 보기

### crash-safe replace 의사 코드

```c
int fd = open("target.tmp", O_CREAT | O_WRONLY | O_TRUNC, 0644);
write(fd, buf, len);
fsync(fd);
close(fd);

rename("target.tmp", "target");

int dirfd = open(".", O_RDONLY | O_DIRECTORY);
fsync(dirfd);
close(dirfd);
```

### mental model

```text
write new bytes
  -> file fsync
  -> rename into place
  -> directory fsync

atomic visibility != durable publish
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| write + rename only | 구현이 단순하다 | crash consistency가 약할 수 있다 | 임시 파일, 약한 내구성 |
| file fsync + rename + dir fsync | publish가 더 안전하다 | latency가 늘 수 있다 | manifest, config, snapshot pointer |
| temp를 다른 fs에 둠 | 관리가 쉬워 보일 수 있다 | `EXDEV`와 atomicity 상실 위험 | 피하는 편이 좋다 |
| long-lived fd 유지 | reopen 비용이 줄 수 있다 | rename 후 old inode를 계속 볼 수 있다 | 명시적 reload 설계 필요 |

## 꼬리질문

> Q: `rename()`은 atomic인데 왜 directory `fsync()`가 또 필요한가요?
> 핵심: namespace 교체의 atomic visibility와 crash 후 durable persistence는 다른 층의 문제이기 때문이다.

> Q: 이미 열린 reader도 rename 후 새 파일을 보나요?
> 핵심: 아니다. 이미 열린 fd는 old inode를 계속 볼 수 있고, 새로 open한 쪽부터 new path를 본다.

> Q: temp file을 `/tmp`에 두면 왜 위험할 수 있나요?
> 핵심: target과 다른 파일시스템이면 `rename()`가 `EXDEV`로 실패하거나 non-atomic fallback으로 바뀔 수 있기 때문이다.

## 한 줄 정리

backend의 crash-safe file publish는 `rename()` 하나가 아니라, "같은 fs에 temp 생성 -> file fsync -> rename -> parent dir fsync"라는 수명 주기 전체로 봐야 한다.
