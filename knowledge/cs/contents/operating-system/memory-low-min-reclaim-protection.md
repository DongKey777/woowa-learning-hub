---
schema_version: 3
title: memory.low memory.min Reclaim Protection
concept_id: operating-system/memory-low-min-reclaim-protection
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- memory-low-min
- reclaim-protection
- memory-low-memory
- min
aliases:
- memory.low memory.min
- cgroup reclaim protection
- protected memory workload
- cache heap reclaim protection
- memory min hard protection
- memory low best effort protection
intents:
- deep_dive
- design
- troubleshooting
linked_paths:
- contents/operating-system/memory-high-vs-memory-max-cgroup-behavior.md
- contents/operating-system/memory-reclaim-cgroup-v2-proactive-reclaim.md
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
- contents/operating-system/kswapd-vs-direct-reclaim-latency.md
symptoms:
- 중요한 workload의 heap이나 page cache를 reclaim에서 어느 정도 보호하고 싶다.
- memory.high/max만 설정했더니 protected workload와 background workload가 같은 압박을 맞는다.
- memory.low와 memory.min의 보호 강도 차이를 이해하지 못해 OOM/reclaim tradeoff가 흐려진다.
expected_queries:
- memory.low와 memory.min은 cgroup reclaim protection에서 어떻게 달라?
- 중요한 workload의 cache와 heap을 reclaim에서 보호하려면 어떤 cgroup knob를 써?
- memory.low는 best-effort protection이고 memory.min은 더 강한 protection이라는 뜻은?
- memory.high max와 low min을 함께 설계할 때 어떤 tradeoff가 있어?
contextual_chunk_prefix: |
  이 문서는 memory.low와 memory.min을 cgroup이 reclaim에서 우선 보호받을 memory amount를
  표현하는 knob로 설명한다. 중요한 workload의 heap/page cache 완충, reclaim pressure,
  OOM trade-off를 함께 다룬다.
---
# memory.low, memory.min, Reclaim Protection

> 한 줄 요약: `memory.low`와 `memory.min`은 cgroup이 reclaim에서 우선적으로 보호받을 메모리를 정하는 장치라서, 중요한 워크로드의 cache와 heap을 완충하는 데 유용하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
> - [memory.reclaim, Cgroup v2 Proactive Reclaim](./memory-reclaim-cgroup-v2-proactive-reclaim.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)

> retrieval-anchor-keywords: memory.low, memory.min, reclaim protection, protected memory, cgroup v2 memory, reclaim priority, memory pressure, protected cache

## 핵심 개념

cgroup v2의 `memory.low`와 `memory.min`은 reclaim 대상이 되었을 때 특정 워크로드의 메모리를 더 보호해 주는 역할을 한다.

- `memory.low`: 이 값 아래의 메모리는 가급적 보호한다
- `memory.min`: 더 강한 보호 경계다
- `reclaim protection`: 압박이 와도 우선적으로 덜 건드리는 전략이다

왜 중요한가:

- 핵심 API의 heap이나 page cache를 보호할 수 있다
- batch와 foreground를 같은 노드에서 돌릴 때 간섭을 줄일 수 있다
- OOM 전에 느려지는 경로를 완화할 수 있다

이 문서는 [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)와 같이 읽으면 좋다.

## 깊이 들어가기

### 1. low와 min은 같은 말이 아니다

- `memory.low`: 최대한 보호하고 싶다는 힌트에 가깝다
- `memory.min`: 더 강하게 보호하고 싶은 최소 경계다

### 2. 보호는 공짜가 아니다

한 cgroup을 보호하면 다른 cgroup이 더 많이 reclaim당할 수 있다.

- noisy neighbor를 다른 쪽으로 밀어낼 수 있다
- 전체 노드 메모리 압박은 여전히 존재한다
- 잘못 쓰면 다른 워크로드가 먼저 느려진다

### 3. foreground와 background를 분리할 때 유용하다

- API heap
- 핵심 cache
- latency-sensitive worker

이런 것들을 `memory.low`로 보호하고, batch는 더 쉽게 reclaim되도록 설계할 수 있다.

### 4. protection은 PSI와 함께 봐야 한다

보호를 해도 실제 stall이 줄었는지 확인해야 한다.

## 실전 시나리오

### 시나리오 1: 배치가 돌아도 API cache가 덜 흔들린다

가능한 원인:

- `memory.low`로 핵심 cgroup이 보호된다
- batch가 reclaim을 더 많이 맞는다
- latency-sensitive 영역이 완충된다

### 시나리오 2: 보호를 걸었는데 다른 cgroup이 느려진다

가능한 원인:

- 보호가 너무 강하다
- 노드 여유가 없다
- reclaim 압박이 전이됐다

### 시나리오 3: `memory.high`와 조합이 이상하다

가능한 원인:

- high와 low의 계층이 충돌한다
- 보호 경계가 너무 넓다
- overall pressure가 그대로다

## 코드로 보기

### 설정 감각

```bash
echo 2147483648 > /sys/fs/cgroup/memory.low
echo 1073741824 > /sys/fs/cgroup/memory.min
```

### 상태 확인

```bash
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.pressure
```

### 감각 모델

```text
protected cgroup
  -> reclaim hits other cgroups first
  -> latency-sensitive memory stays warmer
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| memory.low 사용 | 핵심 워크로드를 보호한다 | 다른 워크로드가 더 희생된다 | API 우선 |
| memory.min 사용 | 더 강하게 보호한다 | 노드 공정성이 나빠질 수 있다 | 핵심 cache |
| 보호 없음 | 단순하다 | noisy neighbor에 취약 | 비중요 워크로드 |

## 꼬리질문

> Q: memory.low와 memory.min 차이는?
> 핵심: 둘 다 보호지만 min이 더 강한 경계다.

> Q: 보호하면 무엇이 희생되나요?
> 핵심: 다른 cgroup의 reclaim 압박이 커진다.

> Q: 언제 유용한가요?
> 핵심: API와 batch를 같은 노드에서 돌릴 때다.

## 한 줄 정리

`memory.low`와 `memory.min`은 reclaim에서 특정 cgroup을 보호하는 장치라서, latency-sensitive 워크로드를 배치 간섭으로부터 완충하는 데 유용하다.
