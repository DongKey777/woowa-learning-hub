# Slab Allocator, Kernel Memory Pressure

> 한 줄 요약: slab 메모리는 프로세스 RSS에 잘 안 보이지만, 커널 객체가 쌓이면 system memory pressure와 OOM의 숨은 원인이 될 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [OOM Killer Scoring, Victim Selection](./oom-killer-scoring-victim-selection.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)

> retrieval-anchor-keywords: slab allocator, SLUB, kmalloc, kmem_cache, slabtop, /proc/slabinfo, shrinker, kernel memory pressure, reclaimable slab

## 핵심 개념

슬랩 allocator는 커널이 자주 쓰는 작은 객체를 빠르게 할당하기 위한 메모리 관리 방식이다. 유저 프로세스의 `RSS`만 봐서는 잡히지 않는 커널 메모리 압박이 여기서 생길 수 있다.

- `slab`: 같은 크기의 객체를 묶어 관리하는 캐시 구조다
- `SLUB`: Linux에서 널리 쓰이는 slab 구현이다
- `kmalloc`: 커널의 일반 목적 메모리 할당 경로다
- `shrinker`: 메모리 압박 시 커널 캐시를 회수하려는 메커니즘이다

왜 중요한가:

- 네트워크 연결, inode, dentry, socket buffer 같은 커널 객체가 쌓이면 시스템 메모리를 압박한다
- 유저 메모리는 멀쩡해 보여도 커널 쪽 캐시가 문제일 수 있다
- slab pressure는 reclaim과 OOM을 뒤틀어서 장애 원인을 헷갈리게 만든다

이 문서는 [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)와 [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)을 커널 메모리 관점으로 연결한다.

## 깊이 들어가기

### 1. slab은 빠르지만 누적되면 무겁다

slab은 객체를 재사용하기 쉬워 성능이 좋다. 하지만 다음 상황에서 메모리가 크게 늘 수 있다.

- 연결 수가 많다
- inode나 dentry cache가 커진다
- 커널 네트워크 객체가 쌓인다
- 특정 타입의 객체가 해제되지 않는다

### 2. reclaim 가능한 slab과 아닌 slab이 있다

커널 캐시가 모두 똑같이 쉽게 회수되는 것은 아니다.

- 일부 cache는 shrinker가 쉽게 줄일 수 있다
- 일부는 참조가 살아 있어 잘 안 내려간다
- "reclaim 가능"과 "즉시 회수 가능"은 다르다

### 3. slab pressure는 유저 RSS보다 늦게 보일 수 있다

유저 공간에서 보이는 메모리와 커널 내부 객체는 다른 축이다.

- 프로세스 RSS는 작아 보이는데 메모리 부족이 온다
- `free`만 보면 이유가 안 보일 수 있다
- `/proc/slabinfo`와 `slabtop`이 답을 준다

### 4. 커널 메모리 문제는 특정 워크로드에서 폭발한다

- 많은 파일 열기/닫기
- 네트워크 connection storm
- container density가 높은 호스트
- metadata-heavy filesystem workload

## 실전 시나리오

### 시나리오 1: 프로세스 RSS는 낮은데 노드가 메모리 압박을 받는다

가능한 원인:

- dentry/inode cache가 커졌다
- socket-related slab이 늘었다
- 커널 객체가 해제되지 않는다

진단:

```bash
slabtop
cat /proc/slabinfo | head
cat /proc/meminfo | grep -E 'Slab|SReclaimable|SUnreclaim'
```

### 시나리오 2: connection surge 이후 메모리 사용량이 회복되지 않는다

가능한 원인:

- socket 관련 slab이 남아 있다
- cache shrink가 느리다
- reclaim pressure가 뒤늦게 왔다

### 시나리오 3: 파일 시스템 작업 후 메모리 압박이 심해진다

가능한 원인:

- dentry/inode cache 성장
- metadata churn
- reclaim 우선순위가 꼬임

이 경우는 [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)와 같이 본다.

## 코드로 보기

### slab 상태 확인

```bash
cat /proc/slabinfo | head -n 20
slabtop -o
```

### 메모리 구성 확인

```bash
cat /proc/meminfo | grep -E 'MemFree|MemAvailable|Slab|SReclaimable|SUnreclaim'
```

### 단순 모델

```text
many kernel objects
  -> slab grows
  -> reclaim pressure rises
  -> if shrinkers cannot catch up, latency and OOM risk rise
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| slab 캐시 유지 | 빠른 재할당 | 메모리 점유 증가 | 일반 커널 경로 |
| 공격적 shrink | 메모리 회수 | 재할당 비용 증가 | 압박 해소 필요 |
| workload 제한 | 커널 객체 폭증 완화 | 처리량 감소 | connection/file storm |
| 노드 여유 확보 | slab 압박 완화 | 자원 효율 저하 | 핵심 인프라 |

## 꼬리질문

> Q: slab 메모리는 왜 안 보이나요?
> 핵심: 유저 RSS보다 커널 객체와 캐시로 잡히기 때문이다.

> Q: SReclaimable과 SUnreclaim의 차이는?
> 핵심: 전자는 상대적으로 회수 가능한 캐시, 후자는 더 회수 어려운 커널 메모리다.

> Q: slab pressure가 OOM으로 이어질 수 있나요?
> 핵심: 그렇다. 커널 메모리 압박이 reclaim을 밀어 OOM을 유발할 수 있다.

## 한 줄 정리

slab allocator는 커널 성능의 핵심이지만, 커널 객체가 누적되면 유저 메모리와 별개로 시스템 메모리 압박과 OOM의 원인이 될 수 있다.
