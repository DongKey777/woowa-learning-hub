# OverlayFS Copy-up, Container Layering, Runtime Debugging

> 한 줄 요약: 컨테이너에서 "작은 수정"처럼 보여도 OverlayFS는 lower layer의 파일을 upperdir로 copy-up 하면서 예상보다 큰 I/O와 writable layer 증가를 만들 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [VFS, Dentry, Inode Cache Pressure](./vfs-dentry-inode-cache-pressure.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Fsync Tail Latency, Dirty Writeback, Backend Debugging](./fsync-tail-latency-dirty-writeback-debugging.md)
> - [tmpfs, shmem, /dev/shm, Cgroup Memory Accounting](./tmpfs-shmem-cgroup-memory-accounting.md)

> retrieval-anchor-keywords: overlayfs, overlay, copy-up, copy_up, upperdir, lowerdir, workdir, whiteout, opaque directory, container writable layer, image layer, writable layer growth

## 핵심 개념

OverlayFS는 여러 read-only lower layer와 하나의 writable upper layer를 합쳐 하나의 파일 시스템처럼 보이게 만드는 union filesystem이다. 많은 컨테이너 런타임이 이미지 레이어와 컨테이너 writable layer를 표현할 때 이 모델을 사용한다.

- `lowerdir`: 주로 이미지 레이어처럼 read-only로 보이는 부분이다
- `upperdir`: 컨테이너 실행 중 변경 사항이 기록되는 writable layer다
- `workdir`: OverlayFS 내부 작업용 디렉터리다
- `copy-up`: lower에 있던 파일을 수정하려 할 때 upper로 복사한 뒤 그 사본을 바꾸는 동작이다
- `whiteout` / `opaque directory`: lower에 있는 파일이나 디렉터리를 merged view에서 숨기는 표시다

왜 중요한가:

- `chown -R`, `chmod -R`, startup 시 템플릿 rewrite 같은 작업이 대량 copy-up으로 바뀔 수 있다
- 애플리케이션이 image path 아래에 로그나 임시 파일을 쓰면 upperdir가 빠르게 커질 수 있다
- tail latency 원인이 "앱이 한 줄 썼다"가 아니라 "커널이 파일 전체를 upper로 올렸다"일 수 있다

## 깊이 들어가기

### 1. copy-up 비용은 수정량이 아니라 객체 경계로 보아야 한다

OverlayFS에서 lowerdir의 파일을 수정하려면 먼저 upperdir에 writable copy가 필요하다. 그래서 몇 바이트만 고쳐도 비용은 "몇 바이트를 썼는가"보다 "어떤 파일을 upper로 끌어올렸는가"에 더 가깝다.

- 큰 파일의 일부만 바꿔도 첫 변경 시점에는 copy-up 비용이 붙을 수 있다
- 일부 메타데이터 변경도 copy-up을 유발할 수 있다
- 첫 write가 끝난 뒤에는 upperdir 사본을 계속 사용하므로 이후 비용 패턴이 달라진다

즉 애플리케이션 로그에서 `write()`는 작아 보여도, 실제 저장 비용은 copy-up + dirty writeback + `fsync()` 대기로 구성될 수 있다.

### 2. delete는 lower layer를 지우는 것이 아니라 merged view를 가린다

컨테이너 안에서 lower layer에 있던 파일을 삭제하면 보통 lower 자체가 지워지지 않는다. 대신 upperdir에 whiteout이 생겨 merged view에서만 안 보이게 만든다.

- 현재 컨테이너에서는 삭제된 것처럼 보인다
- 같은 이미지를 다시 띄운 새 컨테이너에서는 그 파일이 다시 보일 수 있다
- "지웠는데 이미지 용량이 왜 안 줄지?" 같은 혼란이 생긴다

그래서 runtime writable layer와 image layer의 저장 의미를 분리해서 생각해야 한다.

### 3. copy-up 뒤에는 일반 파일 시스템 비용이 다시 나타난다

copy-up은 시작점일 뿐이다. upperdir에 파일이 생긴 뒤에는 일반 파일 시스템과 동일하게 page cache, dirty writeback, journal commit, flush queue의 영향을 받는다.

- copy-up이 큰 파일일수록 dirty page를 빠르게 만든다
- 같은 노드의 다른 writer와 storage queue를 공유한다
- `fsync()` 기반 durability 경로가 있다면 copy-up 직후 p99가 더 크게 튈 수 있다

즉 OverlayFS 문제는 "컨테이너 전용"으로 끝나지 않고, 결국 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md) 문제로 이어진다.

### 4. mutable hot path는 image path 밖으로 빼는 편이 낫다

다음과 같은 경로는 image layer 아래보다 별도 volume이나 tmpfs가 더 적합한 경우가 많다.

- request 중 계속 append되는 로그
- 업로드 staging 파일
- unzip, render, export 같은 중간 산출물
- SQLite, local queue, WAL처럼 지속적으로 write와 sync가 일어나는 파일

이렇게 나누면 image layer는 immutable artifact로 유지되고, writable hot path는 I/O 특성에 맞게 분리할 수 있다.

## 실전 시나리오

### 시나리오 1: 컨테이너 startup만 유독 느리다

가능한 원인:

- entrypoint에서 `chown -R` 또는 `chmod -R`를 수행한다
- lower layer의 많은 파일이 upperdir로 copy-up 된다
- startup 직후 dirty writeback이 몰린다

진단:

```bash
findmnt -t overlay -o TARGET,SOURCE,OPTIONS
du -sh <upperdir>
strace -ff -ttT -e trace=chmod,fchmodat,chown,fchownat,rename,openat,write <entrypoint-cmd>
```

판단 포인트:

- startup 전후 upperdir가 급격히 커지는가
- 메타데이터 작업 직후 writeback pressure가 붙는가
- read-only artifact를 매번 "수정해서 쓰는" 초기화 방식인가

### 시나리오 2: API 서버가 image path 아래에 로그를 남긴다

가능한 원인:

- 처음 append 시 lower 파일 copy-up이 일어난다
- 이후 upperdir에서 dirty page와 `fsync()` 대기가 쌓인다
- 컨테이너 재시작 전까지 writable layer가 계속 커진다

대응 감각:

- 로그 경로를 volume이나 host log path로 분리한다
- image 안에 둘 파일은 immutable artifact로 유지한다
- write-heavy local state는 tmpfs 또는 전용 볼륨으로 나눈다

### 시나리오 3: 파일을 지웠는데도 저장소 경보가 바로 줄지 않는다

가능한 원인:

- lower layer 파일은 whiteout으로만 가려졌다
- upperdir 쪽 다른 copy-up 파일이 남아 있다
- open file descriptor가 남아 있어 공간 회수가 늦는다

이때는 "이미지 용량", "upperdir 사용량", "열린 삭제 파일"을 따로 봐야 한다.

## 코드로 보기

### merged view mental model

```text
lowerdir=/layers/base:/layers/app
upperdir=/containers/123/upper

read /app/config.yml
  -> lower에서 보일 수 있다

first write /app/config.yml
  -> lower의 파일을 upper로 copy-up
  -> 이후에는 upper 사본을 수정
```

### overlay mount 확인

```bash
findmnt -t overlay -o TARGET,SOURCE,OPTIONS
mount | rg overlay
```

### writable hot path 분리 예시

```text
/app                 -> image artifact, 가능하면 read-only 유지
/var/lib/myapp       -> volume, 지속 상태 저장
/var/log/myapp       -> volume 또는 외부 log path
/tmp/myapp           -> tmpfs 또는 host tmp
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| OverlayFS writable layer 유지 | 배포가 단순하다 | copy-up과 upperdir growth를 감수해야 한다 | 작은 변경만 있을 때 |
| Volume으로 분리 | write path를 명확히 분리한다 | 운영 객체가 늘어난다 | DB, queue, upload, log |
| tmpfs 사용 | 빠르고 image 오염이 없다 | 메모리를 먹고 재시작 시 사라진다 | 짧은 임시 작업 |
| 이미지를 immutable하게 유지 | startup/운영 예측이 쉬워진다 | 런타임 커스터마이징이 줄어든다 | 표준화된 서비스 운영 |

## 꼬리질문

> Q: OverlayFS의 copy-up은 왜 tail latency를 만들 수 있나요?
> 핵심: 작은 수정처럼 보여도 먼저 upperdir에 writable copy를 만들어야 해서 I/O가 객체 단위로 커질 수 있기 때문이다.

> Q: 컨테이너에서 파일 삭제가 왜 image 용량 감소와 다를 수 있나요?
> 핵심: lower layer를 직접 지우는 것이 아니라 whiteout으로 현재 merged view만 가리는 경우가 많기 때문이다.

> Q: 로그나 임시 파일을 image path에 두면 왜 안 좋나요?
> 핵심: immutable artifact와 write-heavy path가 섞여 copy-up, writeback, upperdir growth가 함께 생기기 때문이다.

## 한 줄 정리

OverlayFS는 컨테이너 파일 시스템을 단순하게 보여 주지만, 실제 write 비용은 copy-up과 upperdir growth 형태로 드러나므로 mutable path를 image layer와 분리해서 보는 감각이 중요하다.
