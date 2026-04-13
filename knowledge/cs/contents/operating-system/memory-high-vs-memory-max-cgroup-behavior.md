# memory.high vs memory.max, Cgroup Behavior

> 한 줄 요약: `memory.high`는 압박을 먼저 주는 완충선이고, `memory.max`는 그 선을 넘었을 때의 하드 리밋이라 둘의 성격이 완전히 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [OOM Killer Scoring, Victim Selection](./oom-killer-scoring-victim-selection.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)

> retrieval-anchor-keywords: memory.high, memory.max, memory events, throttling, reclaim, cgroup v2, soft limit, hard limit, memory pressure

## 핵심 개념

cgroup v2에서 메모리 제어는 한 단계가 아니다. `memory.high`는 압박을 주며 reclaim을 유도하는 soft-ish 경계이고, `memory.max`는 절대 상한이다.

- `memory.high`: 넘으면 reclaim 압박이 강해진다
- `memory.max`: 넘으면 할당이 실패하거나 OOM으로 이어질 수 있다
- `memory.events`: high/max/oom 계열 이벤트를 본다

왜 중요한가:

- `memory.high`는 OOM 전에 느려지게 만들 수 있다
- `memory.max`는 즉시 실패를 만들 수 있다
- 둘을 혼동하면 "느려진 건지 죽은 건지"를 잘못 해석한다

이 문서는 [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)와 [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)를 cgroup 경계 관점에서 이어준다.

## 깊이 들어가기

### 1. `memory.high`는 브레이크가 아니라 경고선이다

이 선을 넘으면 커널은 해당 cgroup에 더 강한 reclaim 압박을 건다.

- alloc path가 느려질 수 있다
- page cache와 anon memory 회수가 늘 수 있다
- OOM 전에 latency가 먼저 오른다

### 2. `memory.max`는 하드 리밋이다

`memory.max`를 넘으면 더 이상 정상적인 allocation 경로를 보장할 수 없다.

- 실패가 표면화될 수 있다
- OOM으로 이어질 수 있다
- 서비스는 갑자기 죽거나 재시작한다

### 3. 둘의 역할은 다르다

- `memory.high`: "좀 줄여"라는 신호
- `memory.max`: "이 이상은 안 돼"라는 제한

### 4. 운영에서는 둘을 함께 설계해야 한다

한쪽만 잡으면 한계가 분명하다.

- high만 있으면 압박은 줄 수 있어도 안전 상한이 없다
- max만 있으면 급격한 OOM이 날 수 있다
- workload 특성에 맞는 완충 구간이 필요하다

## 실전 시나리오

### 시나리오 1: 죽지는 않는데 점점 느려진다

가능한 원인:

- `memory.high`를 자주 넘는다
- reclaim이 강해진다
- PSI memory pressure가 먼저 튄다

진단:

```bash
cat /sys/fs/cgroup/memory.high
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.pressure
```

### 시나리오 2: 일정 시점에 OOMKilled가 난다

가능한 원인:

- `memory.max`가 너무 낮다
- burst가 high를 지나 max까지 바로 간다
- working set이 limit보다 크다

### 시나리오 3: high를 낮췄더니 latency는 좋아졌는데 처리량이 줄었다

가능한 원인:

- reclaim이 너무 자주 일어난다
- page cache가 일찍 밀린다
- throttling이 과하다

## 코드로 보기

### cgroup 메모리 설정 확인

```bash
cat /sys/fs/cgroup/memory.high
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.current
```

### 이벤트와 pressure 함께 보기

```bash
watch -n 1 'cat /sys/fs/cgroup/memory.events; echo; cat /sys/fs/cgroup/memory.pressure'
```

### 설정 예시

```bash
echo 4294967296 > /sys/fs/cgroup/memory.high
echo 5368709120 > /sys/fs/cgroup/memory.max
```

### 감각 모델

```text
memory.current approaches high
  -> reclaim pressure rises
memory.current exceeds max
  -> allocations fail or OOM path triggers
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 낮은 `memory.high` | 압박을 조기에 막는다 | latency와 throughput이 줄 수 있다 | 느린 장애 방지 |
| 높은 `memory.high` | burst 흡수가 쉽다 | OOM에 가까워질 수 있다 | 트래픽 변동 큼 |
| 낮은 `memory.max` | 노드 안정성에 좋다 | 갑작스런 OOM 위험 | 강한 격리 필요 |
| 높은 `memory.max` | 여유가 생긴다 | noisy neighbor 위험 | 단일 워크로드 |

## 꼬리질문

> Q: `memory.high`와 `memory.max`의 차이는?
> 핵심: 전자는 압박을 유도하는 경계, 후자는 하드 리밋이다.

> Q: `memory.high`를 넘으면 바로 죽나요?
> 핵심: 아니다. 주로 reclaim 압박과 latency 증가가 먼저 온다.

> Q: `memory.max`만 있으면 충분한가요?
> 핵심: 아니다. high가 있어야 느린 장애를 더 일찍 본다.

## 한 줄 정리

`memory.high`는 느린 장애를 먼저 보게 하는 압박선이고, `memory.max`는 진짜 경계를 막는 하드 리밋이다.
