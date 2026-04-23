# Page Cache, Dirty Writeback, fsync

> 한 줄 요약: 디스크 쓰기는 보이는 순간 끝난 게 아니라, page cache와 writeback 정책을 거쳐야 진짜 안전해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)
> - [file descriptor, socket, syscall cost](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)
> - [Dirty Throttling, balance_dirty_pages, Writeback Stalls](./dirty-throttling-balance-dirty-pages-writeback-stalls.md)
> - [Fsync Batching Semantics](./fsync-batching-semantics.md)
> - [Fsync Tail Latency, Dirty Writeback, Backend Debugging](./fsync-tail-latency-dirty-writeback-debugging.md)
> - [Rename Atomicity, Directory fsync, Crash Consistency](./rename-atomicity-directory-fsync-crash-consistency.md)

> retrieval-anchor-keywords: page cache, dirty writeback, fsync, fdatasync, durable write, dirty page, writeback, journal commit, page cache flush, backend durability

## 핵심 개념

`page cache`는 파일 I/O를 빠르게 하기 위해 커널이 메모리에 두는 캐시다.  
파일에 쓰면 항상 디스크에 즉시 쓰는 것이 아니라, 먼저 page cache에 반영되고 나중에 writeback 된다.

왜 중요한가:

- 쓰기 성능은 좋아지지만, 데이터가 아직 디스크에 없을 수 있다.
- `dirty page`가 쌓이면 writeback이 몰리고 지연이 폭발할 수 있다.
- `fsync()`는 안정성을 위해 필요하지만, 비용이 크다.

## 깊이 들어가기

### 1. page cache가 하는 일

파일을 읽을 때는 page cache가 히트하면 디스크를 안 가도 된다.  
파일을 쓸 때는 dirty page로 먼저 반영하고, 커널이 나중에 디스크로 밀어낸다.

즉 애플리케이션이 `write()` 성공을 봤다고 해서 디스크에 저장됐다는 뜻은 아니다.

### 2. dirty page와 writeback

파일 시스템에 데이터가 쓰이면 page cache 안의 해당 페이지는 dirty 상태가 된다.  
이 dirty 페이지가 많아지면 커널은 writeback을 시작한다.

문제는 writeback이 너무 늦어지면 갑자기 대량 flush가 발생할 수 있다는 점이다.

- `dirty_ratio`
- `dirty_background_ratio`
- flush thread
- journal commit

이 값들이 꼬이면 "갑자기 디스크가 느려진다"는 현상이 나온다.

### 3. fsync의 의미

`fsync()`는 파일 내용을 디스크에 강제로 반영해 달라는 요청이다.  
하지만 실제로는 파일 데이터만이 아니라 메타데이터와 저널링 정책까지 관련된다.

실전에서는 다음을 구분해야 한다.

- `write()`: 커널 버퍼에 반영
- `fsync()`: 디스크 안정성 확보
- `fdatasync()`: 데이터 중심 동기화

### 4. 데이터가 안전해지는 시점

애플리케이션은 종종 "응답이 나갔으니 저장됐다"고 생각하지만, 실제로는 아니라는 점이 중요하다.

- DB binlog
- WAL/redo log
- file flush

이 중 무엇이 안정성 기준인지 서비스마다 다르다.

## 실전 시나리오

### 시나리오 1: 로그 파일이 갑자기 밀린다

로그를 한 줄씩 flush하면 CPU보다 디스크 대기가 먼저 병목이 된다.

진단:

```bash
iostat -x 1
vmstat 1
cat /proc/meminfo | grep -E 'Dirty|Writeback'
```

체크 포인트:

- `Dirty`가 계속 증가하는가
- `writeback`이 장시간 유지되는가
- `await`가 튀는가

### 시나리오 2: fsync를 넣었더니 TPS가 급락한다

DB나 파일 기반 큐에서 fsync는 안전하지만 비싸다.  
특히 작은 쓰기를 자주 fsync하면 디스크의 배치 효과를 못 얻는다.

### 시나리오 3: 서버 재시작 후 일부 파일이 사라진다

write 성공만 보고 종료된 프로세스는 dirty page가 아직 디스크에 안 내려갔을 수 있다.  
이때 `fsync()` 전략이 없으면 전원 장애나 커널 패닉 시 손실이 생긴다.

## 코드로 보기

### Python-style pseudo example

```python
with open("events.log", "a") as f:
    f.write(line)
    f.flush()
    os.fsync(f.fileno())
```

`flush()`는 사용자 공간 버퍼를 밀고, `fsync()`는 커널 페이지 캐시 뒤의 디스크 안정성을 요구한다.

### Linux 관찰 커맨드

```bash
cat /proc/meminfo | grep -E 'Dirty|Writeback'
iostat -x 1
pidstat -d 1
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 빠른 write + 나중 flush | 처리량 높음 | 장애 시 손실 가능성 | 로그/캐시성 데이터 |
| fsync 자주 사용 | 안정성 높음 | TPS 급락 | 결제, 주문, 큐 적재 |
| 배치 flush | 성능과 안정성 균형 | 지연 증가 | append-heavy workload |
| WAL/저널링 의존 | 일관성 관리 쉬움 | 구현/복구 비용 | DB/파일 시스템 설계 |

## 꼬리질문

> Q: `write()`가 성공하면 디스크에 저장된 건가?
> 의도: page cache와 durable write 구분 여부 확인
> 핵심: 커널 버퍼 성공과 디스크 내구성은 다르다.

> Q: `fsync()`는 왜 그렇게 비싼가?
> 의도: flush, barrier, journal 비용 이해 여부 확인
> 핵심: 디스크 회전/flush 배치가 깨지고 대기 시간이 늘어난다.

> Q: dirty page가 많아지면 왜 서버가 갑자기 느려질 수 있는가?
> 의도: writeback burst와 latency spike 이해 여부 확인
> 핵심: 커널이 뒤늦게 몰아서 쓰면 I/O 큐가 포화된다.

## 한 줄 정리

page cache는 쓰기를 빠르게 만들지만, `fsync`와 writeback 정책을 모르고 쓰면 내구성과 지연 시간 둘 다 놓치게 된다.
