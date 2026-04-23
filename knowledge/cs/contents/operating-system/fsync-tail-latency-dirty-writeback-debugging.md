# Fsync Tail Latency, Dirty Writeback, Backend Debugging

> 한 줄 요약: 백엔드 서비스에서 `fsync()`가 느려 보일 때, 진짜 원인은 storage 자체보다 page cache에 쌓인 write debt, dirty writeback, journal commit, writer throttling이 서로 다른 시점에 드러나는 데 있는 경우가 많다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)
> - [Dirty Throttling, balance_dirty_pages, Writeback Stalls](./dirty-throttling-balance-dirty-pages-writeback-stalls.md)
> - [Fsync Batching Semantics](./fsync-batching-semantics.md)
> - [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: fsync tail latency, dirty writeback, page cache debt, balance_dirty_pages, jbd2, writeback congestion, backend service latency, fdatasync, journal commit, io pressure

## 핵심 개념

백엔드 서비스에서 파일 기반 WAL, 로컬 큐, audit log, snapshot, 임시 업로드 파일을 다룰 때 `write()`와 `fsync()`는 같은 "디스크 쓰기"처럼 보이지만 실제로는 다른 지점을 노출한다.

- `write()`: 우선 page cache에 dirty page를 만든다
- `dirty writeback`: 커널이 dirty page를 실제 저장장치로 밀어낸다
- `balance_dirty_pages()`: dirty page가 너무 쌓이면 writer를 일부러 늦춘다
- `fsync()`: 데이터와 메타데이터를 durable state로 밀어붙이는 경계다
- `journal commit`: ext4 같은 저널링 파일시스템에서 `fsync()`가 기다릴 수 있는 내부 단계다

왜 중요한가:

- request handler가 느린 이유가 애플리케이션 코드가 아니라 `fsync()` 대기일 수 있다
- 반대로 `fsync()`가 느려 보였지만 실제로는 그 전에 `write()`가 이미 throttling 되고 있을 수 있다
- 같은 노드의 다른 배치 작업이 쌓아 둔 dirty page debt가 API 서버의 p99에서 터질 수 있다

이 문서는 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)의 기본 개념을, 운영 장애에서 "왜 지금 이 요청만 몇백 ms 또는 몇 초씩 멈추는가"라는 질문으로 좁혀 본다.

## 깊이 들어가기

### 1. page cache는 지연을 숨기다가 sync point에서 폭로한다

많은 백엔드 엔지니어가 `write()`가 빨랐으니 저장도 빨랐다고 착각한다. 실제로는 page cache가 쓰기 비용을 미뤄 준 것뿐이다.

- 평소에는 작은 append가 아주 빠르다
- dirty page가 쌓이는 동안 request latency는 멀쩡해 보일 수 있다
- 나중에 `fsync()`나 background writeback이 debt를 한꺼번에 정산한다

그래서 tail latency는 평균보다 "debt를 누가 언제 갚느냐"의 문제로 보는 편이 정확하다.

### 2. `write()`가 느리면 storage보다 dirty throttling을 먼저 의심한다

쓰기 경로가 항상 `fsync()`에서만 느려지는 것은 아니다. dirty page가 임계치를 넘기면 `balance_dirty_pages()`가 writer를 늦춘다.

- API 스레드가 `write()`나 `pwrite()`에서 오래 머문다
- `Dirty`가 높고 `Writeback`도 같이 올라간다
- CPU는 한가한데 스레드는 `D` state로 보일 수 있다

이 경우는 "디스크가 느리다"보다 "커널이 더 쓰지 말라고 속도를 조절한다"에 가깝다. 즉, 문제 지점은 syscall 이름보다 dirty state의 누적과 flush 진척이다.

### 3. `fsync()` tail latency는 journal과 queueing의 결과일 수 있다

`fsync()`는 단순히 한 파일만 flush하는 행위가 아니다.

- 해당 파일의 dirty data flush
- inode, size, timestamp 같은 메타데이터 반영
- 파일시스템 journal commit 대기
- block layer queue와 device cache flush

예를 들어 ext4에서는 `jbd2/*` journal thread가 보이기도 한다. 이때 앱 스레드가 느린 이유는 "내 코드가 느려서"가 아니라, 파일시스템이 durability boundary를 닫는 데 걸리는 시간일 수 있다.

즉 `fsync()` p99는 storage 하나의 지표가 아니라, page cache debt와 파일시스템 commit 경로가 합쳐진 결과다.

### 4. 같은 노드의 다른 writer가 API 서버 p99를 망칠 수 있다

이 특성 때문에 로컬 로그, 배치 export, object staging, DB checkpoint 성격의 쓰기가 같은 볼륨을 공유하면 문제가 전염된다.

- 배치가 dirty page를 크게 쌓는다
- background writeback이 storage queue를 점유한다
- API 서버의 `fsync()`나 작은 `write()`가 갑자기 길어진다

그래서 백엔드 장애 분석에서는 "이 프로세스가 얼마나 썼나"뿐 아니라 "이 디바이스에 누가 debt를 쌓았나"를 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: WAL append는 빠른데 commit 순간만 p99가 튄다

가능한 원인:

- `fsync()`가 journal commit을 기다린다
- 저장장치 queue depth가 이미 높다
- 다른 프로세스의 writeback과 flush 타이밍이 겹친다

진단:

```bash
sudo strace -ff -ttT -p <pid> -e trace=write,pwrite64,fdatasync,fsync
iostat -x 1
cat /proc/pressure/io
ps -eLo pid,tid,comm,state,wchan:32 | rg 'jbd2| D '
```

판단 포인트:

- `write()`는 짧고 `fsync()`만 유독 긴가
- `await`, `aqu-sz`, `%util`이 spike와 같이 오르는가
- ext4 환경이면 `jbd2`가 깨어 있는가

### 시나리오 2: `fsync()`를 안 해도 request write path 자체가 느리다

가능한 원인:

- dirty page가 너무 많이 쌓여 writer throttling이 걸린다
- background writeback이 storage를 따라가지 못한다
- 메모리 압박과 writeback이 겹친다

진단:

```bash
grep -E 'Dirty|Writeback|WritebackTmp' /proc/meminfo
grep -E 'nr_dirty|nr_writeback|nr_dirtied|nr_written|dirty_(background_)?threshold' /proc/vmstat
sysctl vm.dirty_ratio vm.dirty_background_ratio vm.dirty_bytes vm.dirty_background_bytes
cat /proc/pressure/io
```

판단 포인트:

- `nr_dirtied` 증가 속도가 `nr_written`보다 계속 빠른가
- `Dirty`가 높게 유지되면서 request latency가 같이 오르는가
- `io.pressure`가 batch 시간대와 함께 상승하는가

이 패턴은 앱이 explicit `fsync()`를 하지 않아도 나타날 수 있다. 커널이 이미 write debt를 애플리케이션 쓰기 경로에 되돌려 주고 있기 때문이다.

### 시나리오 3: CPU는 낮은데 특정 스레드만 멈춘 것처럼 보인다

가능한 원인:

- 스레드가 block I/O completion을 기다리며 sleep한다
- `fsync()` 또는 writeback path에서 `D` state로 머문다
- 커널 thread가 flush와 journal commit을 처리 중이다

진단:

```bash
top -H -p <pid>
pidstat -d -t 1 -p <pid>
ps -eLo pid,tid,comm,state,wchan:32 | rg ' D |flush-|jbd2|kworker'
cat /proc/pressure/io
```

이때 "CPU가 낮으니 디스크 문제는 아니다"라는 결론은 자주 틀린다. tail latency는 CPU burn보다 off-CPU wait로 더 많이 무너진다.

### 시나리오 4: 컨테이너 하나만 유독 느리지만 노드 전체도 완전히 멈추진 않았다

가능한 원인:

- 특정 cgroup의 write-heavy workload가 자기 pressure를 먼저 높인다
- volume sharing 때문에 일부 서비스만 durable write 영향이 크다
- 같은 노드라도 workload마다 `fsync()` 의존도가 다르다

진단:

```bash
cat /sys/fs/cgroup/io.pressure
cat /sys/fs/cgroup/memory.pressure
pidstat -d 1 -p <pid>
iostat -x 1
```

이 경우는 [cgroup I/O Controller Basics](./cgroup-io-controller-basics.md)와 함께 보면 해석이 쉬워진다.

## 코드로 보기

### 1. `write()`와 `fsync()`를 먼저 분리해서 본다

```bash
sudo strace -ff -ttT -p <pid> -e trace=write,pwrite64,fdatasync,fsync,close,rename
```

가장 먼저 답해야 하는 질문은 이것이다.

```text
느린 syscall이 write 계열인가
  -> dirty throttling, page cache pressure, allocation path를 의심
느린 syscall이 fsync 계열인가
  -> journal commit, flush, block queue congestion을 의심
```

### 2. dirty writeback debt를 본다

```bash
grep -E 'Dirty|Writeback|WritebackTmp' /proc/meminfo
grep -E 'nr_dirty|nr_writeback|nr_dirtied|nr_written|nr_dirty_threshold|nr_dirty_background_threshold' /proc/vmstat
```

해석 감각:

- `Dirty`가 계속 누적된다: 아직 디스크로 안 내려간 write debt가 많다
- `Writeback`이 높다: 지금 flush가 진행 중이다
- `nr_dirtied - nr_written` 차이가 벌어진다: writeback이 생산 속도를 못 따라간다

### 3. block layer와 pressure를 같은 타임라인으로 맞춘다

```bash
iostat -x 1
cat /proc/pressure/io
pidstat -d -t 1 -p <pid>
```

같이 봐야 하는 이유:

- `iostat`만 보면 디바이스가 바쁜지는 알 수 있다
- PSI를 같이 보면 실제 태스크가 얼마나 오래 못 움직였는지 보인다
- `pidstat`를 같이 보면 어느 스레드가 I/O wait를 소비하는지 보인다

### 4. 커널 쪽 증거를 짧게 붙인다

```bash
ps -eLo pid,tid,comm,state,wchan:32 | rg 'jbd2|flush-|kworker| D '
```

ext4 기반이면 `jbd2`가, writeback 경로면 `flush-*`나 관련 `kworker`가 힌트가 된다. 이 단계는 root cause를 확정하는 용도라기보다, "유저 스페이스가 아니라 커널 flush 경로가 실제 대기 지점"이라는 것을 확인하는 데 유용하다.

### 5. `fsync()` 분포를 히스토그램으로 잡는 예

```bash
sudo bpftrace -e '
tracepoint:syscalls:sys_enter_fsync { @start[tid] = nsecs; }
tracepoint:syscalls:sys_exit_fsync /@start[tid]/ {
  @fsync_ms = hist((nsecs - @start[tid]) / 1000000);
  delete(@start[tid]);
}'
```

평균값보다 분포가 중요하다. `fsync()`는 평상시 1ms대여도 배치 쓰기나 checkpoint 타이밍에만 수백 ms로 튈 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `fsync` batching 강화 | flush 횟수를 줄인다 | durability window가 늘어난다 | WAL, queue, append log |
| `dirty_background_bytes`를 더 보수적으로 잡기 | writeback burst를 줄인다 | steady-state throughput이 줄 수 있다 | 큰 메모리 서버, p99 민감 서비스 |
| write-heavy 배치와 API 분리 | 상호 간섭을 줄인다 | 운영 복잡도가 오른다 | 같은 볼륨 공유로 p99가 흔들릴 때 |
| `fdatasync()` 검토 | 불필요한 메타데이터 flush를 줄일 수 있다 | 의미론이 다르면 위험하다 | append-only 성격이 강한 경로 |
| 로컬 디스크 의존 경로 축소 | host-local tail latency를 줄인다 | 아키텍처 변경 비용이 크다 | durability 경로가 병목일 때 |

운영에서는 "더 자주 sync"와 "더 늦게 sync" 둘 다 정답일 수 없다. 어떤 요청이 durability boundary를 실제로 필요로 하는지 먼저 구분해야 한다.

## 꼬리질문

> Q: `fsync()`가 느린데 왜 `write()`도 같이 느려질 수 있나요?
> 핵심: dirty page가 임계치를 넘으면 `balance_dirty_pages()`가 writer 자체를 늦추기 때문이다.

> Q: CPU 사용률이 낮은데 왜 p99가 무너지나요?
> 핵심: block I/O와 journal commit 대기는 off-CPU wait로 나타나며, 이 시간이 tail latency를 직접 만든다.

> Q: `Dirty` 메모리가 많으면 무조건 문제인가요?
> 핵심: 아니다. 중요한 건 누적 속도와 flush 속도의 차이, 그리고 그 시점에 request latency가 흔들리는지다.

> Q: `drop_caches`를 하면 해결되나요?
> 핵심: 보통 아니다. page cache를 비우는 것은 원인 제거가 아니라 증상 이동에 가깝고, 읽기 성능과 쓰기 재가열 비용만 악화시킬 수 있다.

## 한 줄 정리

백엔드 서비스의 `fsync()` tail latency는 "디스크가 느리다" 한 줄로 끝나지 않으며, page cache에 쌓인 dirty debt, writer throttling, journal commit, block queue pressure를 같은 타임라인에서 봐야 풀린다.
