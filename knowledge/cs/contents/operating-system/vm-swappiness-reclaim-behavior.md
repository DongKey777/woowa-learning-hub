---
schema_version: 3
title: vm.swappiness Reclaim Behavior
concept_id: operating-system/vm-swappiness-reclaim-behavior
canonical: true
category: operating-system
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- vm-swappiness-reclaim
- behavior
- anonymous-memory-vs
- page-cache-reclaim
aliases:
- vm.swappiness reclaim behavior
- anonymous memory vs page cache reclaim
- swap preference hint
- reclaim tuning
- swap pressure
- page cache pressure
intents:
- deep_dive
- troubleshooting
- design
linked_paths:
- contents/operating-system/cgroup-swap-controller-basics.md
- contents/operating-system/kswapd-vs-direct-reclaim-latency.md
- contents/operating-system/swap-in-reclaim-fault-path-primer.md
- contents/operating-system/page-cache-active-inactive-reclaim-debugging.md
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
expected_queries:
- vm.swappiness는 swap을 얼마나 좋아하느냐의 단순 숫자가 아니야?
- reclaim이 anonymous memory와 page cache 사이에서 pressure를 어떻게 나누는지 설명해줘
- swappiness를 낮추거나 높이면 swap-in fault와 page cache reclaim이 어떻게 달라져?
- cgroup swap controller와 system swappiness는 어떻게 같이 봐?
contextual_chunk_prefix: |
  이 문서는 operating-system 카테고리에서 vm.swappiness Reclaim Behavior를 다루는 deep_dive 문서다. vm.swappiness reclaim behavior, anonymous memory vs page cache reclaim, swap preference hint, reclaim tuning, swap pressure 같은 lexical 표현과 vm.swappiness는 swap을 얼마나 좋아하느냐의 단순 숫자가 아니야?, reclaim이 anonymous memory와 page cache 사이에서 pressure를 어떻게 나누는지 설명해줘 같은 자연어 질문을 같은 개념으로 묶어, 학습자가 증상, 비교, 설계 판단, 코드리뷰 맥락 중 어디에서 들어오더라도 본문의 핵심 분기와 다음 문서로 안정적으로 이어지게 한다.
---
# vm.swappiness, Reclaim Behavior

> 한 줄 요약: swappiness는 스왑을 얼마나 좋아하느냐의 단순한 숫자가 아니라, reclaim이 anonymous memory와 page cache 사이에서 어떻게 압박을 나눌지에 대한 힌트다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [Swap-In, Reclaim, and Major Fault Path Primer](./swap-in-reclaim-fault-path-primer.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: vm.swappiness, swap, reclaim, kswapd, direct reclaim, anon memory, page cache pressure, swapin, swapout, major fault under pressure, reclaim-induced fault, memory latency

## 핵심 개념

Linux 메모리 관리에서 reclaim은 부족한 메모리를 만들기 위해 무엇을 회수할지 정하는 과정이다. `vm.swappiness`는 커널이 anonymous memory와 page cache 사이에서 어느 쪽을 더 압박할지에 대한 힌트를 준다.

- `swappiness`: swap을 얼마나 적극적으로 고려할지에 대한 조정 값이다
- `kswapd`: 백그라운드 reclaim을 수행하는 커널 스레드다
- `direct reclaim`: 프로세스가 직접 메모리를 얻으려다 reclaim에 끌려 들어가는 상황이다
- `swapin/swapout`: 페이지를 스왑 공간으로 내보내거나 다시 읽어오는 동작이다

왜 중요한가:

- swap이 너무 공격적이면 latency가 급격히 나빠질 수 있다
- page cache를 너무 쉽게 희생하면 디스크 I/O가 증가한다
- reclaim이 길어지면 CPU보다 메모리 대기가 먼저 장애가 된다

이 문서는 [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)와 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)를 reclaim 중심으로 연결한다.

## 깊이 들어가기

### 1. swappiness는 단일 원인 스위치가 아니다

swappiness는 "swap을 쓸까 말까"를 단순 결정하는 값이 아니다. 커널이 압박을 받을 때 어떤 종류의 페이지를 먼저 밀어낼지에 영향을 준다.

- 높으면 anonymous memory도 더 빨리 고려될 수 있다
- 낮으면 page cache를 더 오래 붙잡는 경향이 생길 수 있다
- 너무 극단적인 설정은 워크로드 특성과 어긋날 수 있다

### 2. reclaim은 백그라운드와 전면에서 다르게 일어난다

- `kswapd`는 느리지만 미리 회수한다
- direct reclaim은 요청 경로에 붙어 latency를 직접 늘린다

실무에서 더 무서운 건 direct reclaim이다. 요청이 느려지는 순간 이미 사용자 체감 장애가 된다.

### 3. swap은 완전한 악이 아니다

swap은 무조건 나쁜 것이 아니라, 순간적인 압박을 완충하는 장치다.

- 일시적 burst에는 도움이 될 수 있다
- 워킹셋이 메모리보다 살짝 큰 경우에는 완충 역할을 한다
- 하지만 스왑이 빈번하면 major fault와 latency가 커진다

### 4. reclaim은 page cache와 anon memory의 줄다리기다

메모리 압박이 오면 커널은 파일 캐시와 익명 메모리 사이에서 회수 우선순위를 잡는다.

- 파일 캐시는 재생성 가능성이 높다
- anon memory는 실제 프로세스 상태와 연결되어 더 민감하다
- 워크로드에 따라 무엇을 더 아끼는지가 달라진다

## 실전 시나리오

### 시나리오 1: 메모리는 남아 보이는데 응답 시간이 길어진다

가능한 원인:

- direct reclaim이 걸린다
- page cache가 빠르게 밀린다
- swapin/out이 늘어난다

진단:

```bash
vmstat 1
grep -E 'pswpin|pswpout|pgfault|pgmajfault' /proc/vmstat
cat /proc/pressure/memory
```

### 시나리오 2: swappiness를 바꿨는데 체감이 이상하다

가능한 원인:

- 워크로드가 swap보다 page cache에 더 민감하다
- 메모리 압박이 이미 심해서 reclaim 정책보다 용량이 문제다
- cgroup pressure가 먼저다

진단:

```bash
cat /proc/sys/vm/swappiness
cat /proc/meminfo | grep -E 'MemAvailable|SwapTotal|SwapFree|Cached|Dirty'
```

### 시나리오 3: 캐시 서버가 느려졌는데 CPU는 한가하다

가능한 원인:

- page cache를 너무 빨리 버린다
- swap 대신 cache 회수에 치우쳐 있다
- 디스크 I/O가 늘었다

이 경우는 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)와 같이 봐야 한다.

## 코드로 보기

### 현재 swappiness 확인

```bash
cat /proc/sys/vm/swappiness
```

### 일시적 조정 예시

```bash
sysctl vm.swappiness=10
```

주의점:

- 숫자가 낮다고 무조건 좋은 것은 아니다
- swap을 완전히 배제하면 갑작스러운 압박에 더 취약할 수 있다

### reclaim 징후 보기

```bash
grep -E 'allocstall|pgscan|pgsteal|pswpin|pswpout' /proc/vmstat
```

### pressure와 함께 보기

```bash
watch -n 1 'vmstat 1; echo; cat /proc/pressure/memory'
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 낮은 swappiness | swap으로 인한 지연을 줄인다 | page cache 회수가 늘 수 있다 | 지연 민감 API |
| 높은 swappiness | 압박 완충이 쉬워진다 | swapin으로 느려질 수 있다 | burst 허용 워크로드 |
| swap 사용 | OOM을 완화한다 | tail latency가 악화될 수 있다 | 여유 있는 서비스 |
| swap 최소화 | 예측 가능성이 높다 | 압박이 오면 바로 위험하다 | 핵심 실시간 경로 |

## 꼬리질문

> Q: swappiness가 높으면 항상 나쁜가요?
> 핵심: 아니다. 버스트를 완충할 수도 있지만 latency 요구와 충돌할 수 있다.

> Q: reclaim과 OOM은 어떤 관계인가요?
> 핵심: reclaim이 충분히 못 되면 OOM으로 넘어갈 수 있다.

> Q: direct reclaim이 왜 위험한가요?
> 핵심: 요청 경로에서 바로 지연을 늘리기 때문이다.

> Q: page cache와 swap 중 무엇이 먼저 문제인지 어떻게 보나요?
> 핵심: `vmstat`, `vm.swappiness`, `vmstat`의 swap 지표, PSI를 같이 본다.

## 한 줄 정리

swappiness는 메모리 압박이 왔을 때 reclaim의 방향을 조정하는 힌트이며, 직접적인 latency 문제는 direct reclaim과 swapin/out에서 드러난다.
