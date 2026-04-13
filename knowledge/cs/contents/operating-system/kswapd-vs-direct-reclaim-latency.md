# kswapd vs Direct Reclaim, Latency

> 한 줄 요약: kswapd는 미리 메모리를 치우는 백그라운드 작업이고, direct reclaim은 요청 경로에 침투해 latency를 직접 망가뜨린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)

> retrieval-anchor-keywords: kswapd, direct reclaim, reclaim latency, allocstall, pgscan, pgsteal, memory pressure, stall, reclaim path

## 핵심 개념

메모리가 부족해지면 커널은 페이지를 회수한다. 이때 `kswapd`가 백그라운드에서 먼저 움직일 수 있지만, 압박이 심하면 프로세스가 직접 reclaim 경로에 끌려 들어간다.

- `kswapd`: 백그라운드 reclaim을 수행한다
- `direct reclaim`: 할당 요청한 프로세스가 직접 메모리 회수 작업을 기다린다
- `allocstall`: allocation이 막혀 stall이 생긴 흔적이다

왜 중요한가:

- 같은 메모리 압박이라도 direct reclaim은 훨씬 더 아프다
- API latency는 direct reclaim에서 먼저 무너질 수 있다
- reclaim이 길어지면 OOM보다 먼저 사용자 체감 장애가 온다

이 문서는 [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)를 더 운영적으로 좁혀서, kswapd와 direct reclaim의 차이를 본다.

## 깊이 들어가기

### 1. kswapd는 "미리 치우는" 역할이다

커널은 메모리가 완전히 바닥나기 전에 여유를 확보하려 한다.

- 백그라운드에서 free memory를 확보한다
- reclaim을 선제적으로 진행한다
- 그러나 충분하지 않으면 요청 경로로 넘어간다

### 2. direct reclaim은 요청 경로를 막는다

프로세스가 메모리를 할당하려는데 당장 부족하면 직접 reclaim에 참여한다.

- 사용자 요청이 기다린다
- 페이지를 찾고 버리는 작업이 길어질 수 있다
- tail latency가 크게 흔들린다

### 3. reclaim은 page cache와 anon memory를 함께 건드린다

무엇을 회수할지에 따라 체감이 달라진다.

- page cache를 회수하면 파일 I/O가 더 비싸질 수 있다
- anonymous memory를 회수하면 swap과 fault가 늘 수 있다

### 4. reclaim이 심하면 CPU가 아니라 memory stall이 핵심이다

이 상태에서는 "CPU가 부족하다"보다 "메모리를 얻는 시간이 길다"가 핵심이다. PSI와 함께 봐야 한다.

## 실전 시나리오

### 시나리오 1: CPU는 멀쩡한데 요청이 가끔 멈춘다

가능한 원인:

- direct reclaim이 길어진다
- page cache와 anon reclaim이 충돌한다
- allocation path가 막힌다

진단:

```bash
grep -E 'allocstall|pgscan|pgsteal' /proc/vmstat
cat /proc/pressure/memory
vmstat 1
```

### 시나리오 2: 메모리 사용률이 크게 높지 않은데도 느리다

가능한 원인:

- working set이 압박받고 있다
- reclaim이 자주 발생한다
- swapin/out보다 reclaim stall이 먼저 보인다

### 시나리오 3: 배치 이후 API 지연이 길어진다

가능한 원인:

- 배치가 page cache를 밀어낸다
- API가 다시 page fault와 reclaim을 만난다
- kswapd가 뒤늦게 따라간다

이 경우는 [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)와 같이 본다.

## 코드로 보기

### reclaim 징후 확인

```bash
grep -E 'allocstall|pgscan|pgsteal|pgfault|pgmajfault' /proc/vmstat
```

### pressure 같이 보기

```bash
watch -n 1 'cat /proc/pressure/memory; echo; vmstat 1'
```

### 단순 모델

```text
free memory falls
  -> kswapd runs
  -> still not enough
  -> direct reclaim enters request path
  -> latency spikes
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| kswapd 중심 | 사용자 경로를 덜 막는다 | 미리 회수 못 하면 늦는다 | 일반 서버 |
| direct reclaim 허용 | 메모리 압박을 넘긴다 | latency를 직접 망친다 | 최후의 안전장치 |
| 메모리 여유 확대 | reclaim 빈도를 줄인다 | 자원 효율이 낮아진다 | 핵심 API |
| workload 분리 | reclaim 영향을 국소화한다 | 운영이 복잡하다 | 혼합 트래픽 |

## 꼬리질문

> Q: kswapd와 direct reclaim의 가장 큰 차이는 무엇인가요?
> 핵심: kswapd는 백그라운드, direct reclaim은 요청 경로에 들어온다는 점이다.

> Q: direct reclaim이 왜 무서운가요?
> 핵심: 사용자 요청 latency를 직접 늘리기 때문이다.

> Q: reclaim이 OOM보다 먼저 중요한 이유는?
> 핵심: OOM 전에 이미 응답성이 깨질 수 있기 때문이다.

## 한 줄 정리

kswapd는 메모리를 미리 치우는 안전장치이고, direct reclaim은 그 안전장치가 부족할 때 요청 경로를 직접 느리게 만드는 최후의 비용이다.
