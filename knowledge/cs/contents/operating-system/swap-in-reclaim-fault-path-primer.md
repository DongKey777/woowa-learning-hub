# Swap-In, Reclaim, and Major Fault Path Primer

> 한 줄 요약: major fault는 단순한 "디스크에서 읽었다"가 아니라, 조금 전 reclaim이 남긴 빈자리를 swap-in이나 page-cache refault가 메우는 순간으로 읽어야 runtime memory pressure 시나리오가 보인다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [Workingset Refault, Page Cache Reclaim, Runtime Debugging](./workingset-refault-page-cache-reclaim-debugging.md)
> - [Page Cache Active/Inactive Reclaim, Hot-Page Debugging](./page-cache-active-inactive-reclaim-debugging.md)
> - [Cgroup Swap Controller, Basics](./cgroup-swap-controller-basics.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [vmstat Counters, Runtime Pressure](./vmstat-counters-runtime-pressure.md)

> retrieval-anchor-keywords: swap-in primer, reclaim fault path, major fault under memory pressure, reclaim-induced major fault, swapin major fault, anonymous page swapin, page cache refault, cold-page refault, hot-page churn, workingset_refault_file, workingset_activate_file, pswpin, pswpout, pgmajfault, pgscan, pgsteal, allocstall, direct reclaim on page fault, fault debt

## 핵심 개념

major fault는 "지금 이 페이지를 바로 쓸 수 없다"는 현재 시점의 사건이지만, 원인은 종종 **조금 전 reclaim이 무엇을 치웠는가**에 있다.

- anonymous page가 reclaim으로 swap-out됐다가 다시 필요해지면 swap-in fault가 된다
- file-backed page가 page cache reclaim으로 밀려났다가 다시 필요해지면 refault가 된다
- 그 refault가 실제 storage read를 동반하면 major fault로 체감된다
- 메모리 여유가 더 부족하면 fault를 처리하는 과정 자체가 direct reclaim에 끌려 들어가며 더 비싸진다

이 문서의 핵심은 fault를 "단일 순간"이 아니라 **reclaim이 남긴 부채를 나중에 청구하는 경로**로 읽는 감각을 잡는 것이다.

## 한눈에 보기

| 지금 보이는 현상 | 조금 전에 있었을 가능성 | 다음에 볼 것 |
|------|------|------|
| startup 직후 `pgmajfault` 증가 | 아직 안 읽은 file page를 처음 가져오는 중 | `pgscan`, `pswpout`, `workingset`이 같이 높지 않은가 |
| `pgmajfault`와 `pswpin`이 함께 증가 | anonymous page가 swap-out됐다가 다시 들어오는 중 | `pswpout`, `memory.swap.current`, PSI memory |
| `pgmajfault`와 `workingset_refault_file`이 함께 증가 | page cache reclaim 뒤 같은 file page를 다시 읽는 중 | `pgscan`, `pgsteal`, read I/O, `workingset_activate_file` |
| refault는 있지만 반복 activation이 약하다 | 진짜로 식었던 cold page가 나중에 다시 필요해진 것일 수 있음 | 시간축상 phase change인지, 지속 churn인지 |
| fault 처리 구간에서 stall이 길다 | fault service 중 free page 확보를 위해 direct reclaim까지 걸렸을 수 있음 | `allocstall`, PSI memory, `vmstat`의 `b` |

## 1. major fault는 종종 reclaim의 후행 신호다

demand paging 입문에서는 major fault를 보통 "파일이나 swap에서 실제로 가져와야 하는 fault"라고 배운다. 맞는 말이지만, 운영에서는 한 단계 더 봐야 한다.

질문은 "왜 지금 가져와야 했나"다. 그 답은 자주 아래 순서로 이어진다.

```text
memory pressure
  -> kswapd / direct reclaim이 페이지를 스캔한다
  -> anon page는 swap-out될 수 있다
  -> file-backed page는 page cache에서 밀려날 수 있다
  -> 나중에 같은 페이지가 다시 필요해진다
  -> page fault handler가 페이지를 다시 채운다
  -> blocking refill이면 major fault로 체감된다
```

즉 major fault는 단순한 storage miss가 아니라, **reclaim이 무엇을 버렸고 그 판단이 맞았는지**를 뒤늦게 보여 주는 신호이기도 하다.

## 2. anonymous memory 경로: reclaim -> swap-out -> later swap-in

anonymous memory는 실행 파일처럼 다시 읽어 올 원본 파일이 없다. 그래서 메모리 압박이 강해지면 익명 페이지는 swap으로 밀려날 수 있다.

대표 흐름은 이렇다.

```text
anonymous page in RSS
  -> pressure grows
  -> reclaim chooses anon page
  -> page is swapped out
  -> process touches same virtual address later
  -> page fault occurs
  -> kernel reads page back from swap and remaps it
```

여기서 배울 포인트는 두 가지다.

- 현재의 swap-in fault는 과거의 swap-out 결정이 없었다면 생기지 않았을 수 있다
- swap-in 자체만 보는 것이 아니라, 그 fault 직전과 직후에 reclaim stall이 붙는지도 봐야 한다

관측 감각:

- `pswpout`이 먼저 올랐고, 뒤이어 `pswpin`과 `pgmajfault`가 붙으면 swapped anon reuse 가능성이 높다
- `memory.swap.current`가 줄었다 늘었다를 반복하면 swap이 완충재가 아니라 latency 부채로 쓰이고 있을 수 있다
- PSI memory가 같이 높다면 "swap I/O만 느린 것"이 아니라 reclaim으로 요청 경로가 멈추는 중일 수 있다

## 3. file-backed 경로: page-cache reclaim -> later refault

file-backed page는 backing file이 있으므로 reclaim 때 상대적으로 쉽게 버릴 수 있다. 문제는 그 페이지가 정말 차가운 데이터였는지, 아니면 조금 뒤 다시 필요한 hot page였는지다.

흐름은 대체로 이렇다.

```text
file page is resident in page cache
  -> reclaim drops it under pressure
  -> workload touches same mapping again
  -> refault happens
  -> if page must be fetched again, fault path blocks
```

이 경로에서 중요한 구분:

- 이미 다른 경로로 page cache에 복귀해 있었다면 minor fault로 끝날 수 있다
- 실제 storage read가 다시 필요하면 major fault로 체감된다
- refault 자체보다 `workingset_refault_file` 뒤에 `workingset_activate_file`이 붙는지가 더 의미 있다

즉 file-backed major fault는 "파일을 처음 읽었다"일 수도 있지만, **조금 전에 reclaim이 잘못 버린 page cache를 다시 채우는 비용**일 수도 있다.

## 4. cold-page refault와 hot-page churn은 다르다

refault가 있다고 해서 항상 나쁜 것은 아니다. refault는 크게 두 감각으로 나눠 읽는 편이 실전적이다.

### cold-page refault

- 배치 phase가 바뀌어 한동안 안 쓰던 파일을 다시 읽는다
- idle 후 사용자가 돌아와 이전에 보던 화면의 데이터를 다시 연다
- deploy 후 한 번 읽고 긴 시간 뒤 다시 접근한다

이 경우는 "예전에 필요했지만 지금은 다시 필요해진 page"라서, refault 자체가 이상 징후는 아닐 수 있다.

### hot-page churn

- batch scan이 API hot file page를 밀어낸다
- `memory.high` 근처에서 같은 cgroup의 working set이 반복적으로 쓸린다
- page cache를 지우자마자 같은 페이지를 곧바로 다시 읽는다

이 경우는 reclaim 판단이 working set 보존에 실패한 것이다. `workingset_refault_file`, `workingset_activate_file`, `pgscan`, `pgsteal`, read I/O, PSI memory가 함께 오르면 hot-page churn 쪽 해석이 맞아진다.

핵심은 refault를 숫자 하나로 보지 않고, **짧은 시간 안에 재등장했는지, 다시 hot하다고 판정됐는지**를 같이 보는 것이다.

## 5. fault path가 reclaim을 다시 호출할 수도 있다

memory pressure가 심한 구간에서는 "이미 예전에 reclaim된 페이지를 다시 채우는 fault"가, 그 처리 도중 또 free page 부족을 만나 direct reclaim에 들어갈 수 있다.

즉 지연은 단순히 아래 하나가 아니다.

- swap에서 읽는 시간
- 파일에서 읽는 시간

여기에 다음이 추가될 수 있다.

- free page 확보를 위한 direct reclaim
- reclaim 중 lock 경쟁과 wakeup 지연
- PSI memory stall

그래서 같은 `pgmajfault` 증가라도 어떤 구간은 startup warm-up이고, 어떤 구간은 **fault + reclaim + I/O**가 겹친 runtime pressure 사건이 된다.

## 실전 시나리오

### 시나리오 1: 오랫동안 idle이던 서비스가 첫 요청에서 멈칫한다

가능한 원인:

- anonymous working set 일부가 swap-out돼 있었다
- 첫 요청이 그 heap/page table 경로를 다시 건드린다
- `pswpin`과 `pgmajfault`가 같이 증가한다

이때는 cold start라기보다 "idle 동안 밀려난 anon state 복귀"일 수 있다.

### 시나리오 2: 야간 배치 시간대에만 API file-read p99가 튄다

가능한 원인:

- batch가 page cache를 크게 흔든다
- API hot file page가 reclaim으로 밀려난다
- 이후 같은 파일을 다시 읽으며 refault와 major fault가 붙는다

이때는 storage가 느리다기보다, **hot file page를 오래 못 지키는 구조**가 먼저다.

### 시나리오 3: startup 때도 major fault가 있고, 장애 시에도 major fault가 있다

둘은 같아 보이지만 주변 counter가 다르다.

- 정상 startup: `pgmajfault`는 오르지만 `pgscan`, `pswpout`, PSI memory는 조용하다
- 압박 장애: `pgmajfault`와 함께 `pgscan`, `pgsteal`, `pswpin/pswpout`, PSI memory가 같이 오른다

따라서 major fault는 단독 숫자보다 **앞뒤 reclaim 문맥**이 더 중요하다.

## 코드로 보기

### 노드 단위로 reclaim과 fault를 같이 보기

```bash
grep -E 'pgfault|pgmajfault|pswpin|pswpout|pgscan|pgsteal|workingset' /proc/vmstat
cat /proc/pressure/memory
vmstat 1
```

### cgroup 단위로 좁히기

```bash
cat /sys/fs/cgroup/<cg>/memory.stat | rg 'pgfault|pgmajfault|workingset|pgscan|pgsteal|swap'
cat /sys/fs/cgroup/<cg>/memory.pressure
cat /sys/fs/cgroup/<cg>/memory.swap.current
```

### 시간순 해석 cheat sheet

```text
pswpout rises first
  -> later pswpin + pgmajfault rise
    -> swapped anon pages are returning

pgscan/pgsteal rise first
  -> later workingset_refault_file + read IO + pgmajfault rise
    -> reclaimed file cache is being reread

pgmajfault rises alone during startup
  -> cold population may explain it without reclaim trouble
```

주의:

- counter 이름은 커널 버전과 cgroup 관찰 지점에 따라 다를 수 있다
- 절대값보다 "무엇이 먼저 올랐는가"라는 시간 순서가 중요하다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| swap 여유를 조금 남긴다 | 순간 압박 완충 | swap-in tail이 생길 수 있다 | burst를 넘겨야 하는 워크로드 |
| 핵심 cgroup의 working set 보호 | hot-page churn 감소 | 다른 그룹 압박 증가 | API 보호 우선 |
| batch와 API 분리 | file refault 간섭 감소 | 운영 복잡도 증가 | mixed workload |
| startup prewarm | cold major fault 감소 | 메모리와 I/O를 앞당겨 쓴다 | 첫 요청 지연 민감 |

## 꼬리질문

> Q: major fault가 보이면 곧바로 storage 문제라고 봐야 하나요?
> 핵심: 아니다. 바로 앞선 reclaim이 원인일 수 있고, 특히 swap-in이나 page-cache refault 문맥을 같이 봐야 한다.

> Q: refault가 있으면 무조건 cache churn인가요?
> 핵심: 아니다. 오랫동안 식었던 cold page의 정상 재사용일 수 있다. 짧은 시간 내 반복 activation이 더 위험 신호다.

> Q: swap-in fault와 file refault를 어떻게 구분하나요?
> 핵심: `pswpin/pswpout`는 anon swap 경로 쪽, `workingset_refault_file`과 read I/O는 file cache reclaim 경로 쪽 힌트다.

> Q: 왜 CPU는 낮은데 요청이 멈춘 것처럼 보이나요?
> 핵심: fault service 중 reclaim과 I/O 대기가 겹치면 CPU 계산보다 memory stall이 지배적이기 때문이다.

## 한 줄 정리

runtime memory pressure에서 major fault는 결과 신호일 뿐이고, 그 앞에는 reclaim이 남긴 빈자리, swap-in으로 돌아오는 anon page, 그리고 cold-page refault와 hot-page churn을 가르는 page-cache 재사용 문맥이 있다.
