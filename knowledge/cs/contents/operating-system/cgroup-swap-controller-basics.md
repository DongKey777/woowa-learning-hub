# Cgroup Swap Controller, Basics

> 한 줄 요약: cgroup swap controller는 swap 사용량을 워크로드별로 제한해 메모리 압박을 분리하지만, 너무 빡빡하면 OOM이나 latency spike를 앞당길 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)
> - [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)

> retrieval-anchor-keywords: memory.swap.max, swap controller, swap accounting, swap current, cgroup swap, swap limit, memory pressure, swap throttling

## 핵심 개념

cgroup v2에서는 swap 사용량도 제한할 수 있다. 이는 특정 워크로드가 swap을 너무 많이 써서 노드 전체를 느리게 만드는 것을 막는 데 도움이 된다.

- `memory.swap.max`: cgroup의 swap 상한이다
- `memory.swap.current`: 현재 swap 사용량이다
- `swap accounting`: swap 사용을 추적하는 기능이다

왜 중요한가:

- swap이 과하면 latency가 급격히 나빠질 수 있다
- batch와 API의 swap 사용을 분리할 수 있다
- 메모리 압박이 swap으로 번지는 것을 제어할 수 있다

이 문서는 [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)와 [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)를 swap 관점에서 이어준다.

## 깊이 들어가기

### 1. swap controller는 압박 분리 도구다

- 한 cgroup이 swap을 독점하는 것을 막는다
- 메모리 압박이 전체 노드로 번지는 속도를 늦출 수 있다
- 워크로드별 책임을 분리하기 좋다

### 2. swap은 느린 안전망이다

swap은 OOM을 늦출 수 있지만, latency를 희생할 수 있다.

- swapin이 많아지면 응답성이 떨어진다
- page fault와 reclaim이 더 비싸진다
- 너무 많이 의존하면 tail latency가 흔들린다

### 3. limit이 너무 낮으면 오히려 급박해진다

swap을 완전히 못 쓰게 만들면 압박이 더 빨리 OOM으로 갈 수 있다.

### 4. no-swap과 low-swap 사이에 설계 여지가 있다

- 핵심 서비스는 swap을 적게 쓰게 한다
- batch는 좀 더 허용한다
- 노드 전체 정책과 맞춰야 한다

## 실전 시나리오

### 시나리오 1: batch가 swap을 다 써서 API가 느려진다

가능한 원인:

- swap limit이 없다
- batch가 reclaim에서 밀린다
- swapin/out이 늘어난다

진단:

```bash
cat /sys/fs/cgroup/memory.swap.max
cat /sys/fs/cgroup/memory.swap.current
grep -E 'pswpin|pswpout' /proc/vmstat
```

### 시나리오 2: swap을 줄였더니 OOM이 먼저 난다

가능한 원인:

- 완충층이 사라졌다
- working set이 너무 크다
- memory.max와 충돌한다

### 시나리오 3: swap controller가 있어도 latency가 여전히 나쁘다

가능한 원인:

- direct reclaim이 남아 있다
- page cache가 밀린다
- PSI memory pressure가 높다

## 코드로 보기

### swap controller 감각

```bash
cat /sys/fs/cgroup/memory.swap.max
cat /sys/fs/cgroup/memory.swap.current
```

### swap 압박 확인

```bash
vmstat 1
grep -E 'pswpin|pswpout' /proc/vmstat
```

### 감각 모델

```text
swap limit
  -> protects node from runaway swap use
  -> but too low can trigger OOM earlier
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| swap 허용 | 압박 완충 | latency 저하 | 덜 민감한 워크로드 |
| swap 제한 | 지연 예측 가능 | OOM이 빨라질 수 있다 | 핵심 API |
| 워크로드별 차등 | 간섭 분리 | 운영 복잡도 증가 | 멀티테넌트 |

## 꼬리질문

> Q: swap controller는 무엇을 막나요?
> 핵심: cgroup별 swap 사용량을 제한한다.

> Q: swap을 막으면 항상 좋은가요?
> 핵심: 아니다. OOM이 더 빨리 올 수 있다.

> Q: 언제 유용한가요?
> 핵심: batch와 API가 같은 노드를 공유할 때다.

## 한 줄 정리

cgroup swap controller는 워크로드별 swap 사용을 분리해 노드 압박을 제어하지만, 너무 빡빡하면 OOM과 latency를 앞당길 수 있다.
