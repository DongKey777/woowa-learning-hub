# memory.reclaim, Cgroup v2 Proactive Reclaim

> 한 줄 요약: `memory.reclaim`은 이미 터진 OOM을 고치는 장치가 아니라, 특정 cgroup의 page cache나 cold memory를 의식적으로 줄여 pressure를 앞당겨 정리하려는 운영 제어 수단이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
> - [memory.low, memory.min, Reclaim Protection](./memory-low-min-reclaim-protection.md)
> - [Workingset Refault, Page Cache Reclaim, Runtime Debugging](./workingset-refault-page-cache-reclaim-debugging.md)
> - [Page Cache Active/Inactive Reclaim, Hot-Page Debugging](./page-cache-active-inactive-reclaim-debugging.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: memory.reclaim, cgroup v2 proactive reclaim, proactive reclaim, page cache cleanup, reclaim cold memory, memory pressure control, memcg reclaim, workingset hygiene

## 핵심 개념

보통 reclaim은 pressure가 생긴 뒤 커널이 수동적으로 수행한다. `memory.reclaim`은 특정 cgroup에 대해 reclaim을 더 의식적으로 유도하는 인터페이스로, background batch나 끝난 작업의 차가운 cache를 미리 줄여 pressure를 정리하고 싶을 때 생각할 수 있다.

- `memory.reclaim`: 해당 cgroup에 reclaim을 유도하는 제어 인터페이스다
- proactive reclaim: 압박이 터지기 전에 cold memory를 줄이려는 운영 전략이다
- memcg reclaim: cgroup 경계 안에서 일어나는 reclaim이다

왜 중요한가:

- batch job이 남긴 cold page cache를 앞당겨 정리하고 싶을 수 있다
- foreground API 보호를 위해 background cgroup을 먼저 정리할 수 있다
- 하지만 잘못 쓰면 hot cache를 밀어 refault와 latency를 키울 수 있다

## 깊이 들어가기

### 1. proactive reclaim은 치료보다 위생에 가깝다

이 인터페이스는 "시스템이 이미 죽기 직전인데 살려 주는 버튼"으로 보면 안 된다.

- 가장 유효한 순간은 작업이 끝난 직후다
- 지금 당장 안 쓸 cold page cache를 줄이는 데 더 적합하다
- live hot working set을 강제로 비우면 오히려 다음 요청이 느려진다

즉 `memory.reclaim`은 응급처치보다 working set hygiene 도구다.

### 2. reclaim 대상은 workload 특성에 따라 다르게 체감된다

같은 reclaim이라도 다음은 체감이 다르다.

- streaming batch가 남긴 file cache: proactive reclaim이 유용할 수 있다
- API hot index cache: reclaim하면 바로 refault와 p99가 튄다
- tmpfs/shmem: memory.current를 낮출 수는 있지만 다시 필요하면 곧바로 pressure가 복귀한다

그래서 reclaim은 양보다 "어떤 memory class를 건드리나"가 중요하다.

### 3. `memory.low`/`memory.min`과 같이 봐야 한다

한 cgroup을 proactively reclaim하고 싶다면, 동시에 보호하고 싶은 cgroup의 working set도 정해 두는 편이 좋다.

- background batch: reclaim 대상
- latency-sensitive API: 보호 대상

이 조합이 없으면 reclaim은 결국 가장 아픈 곳을 먼저 건드릴 수 있다.

### 4. 좋은 reclaim은 refault를 적게 만든다

성공적인 proactive reclaim 뒤에는 다음이 줄어야 한다.

- `Inactive(file)` 잔존량
- background cgroup의 cold cache footprint
- 이후 foreground refault와 PSI pressure

반대로 reclaim 후 곧바로 `workingset refault`가 늘면 잘못 건드린 것이다.

## 실전 시나리오

### 시나리오 1: nightly batch 후 API cgroup이 아침에 느리다

가능한 원인:

- batch가 큰 file cache를 남긴다
- foreground가 사용할 메모리 여유가 줄어든다
- batch 종료 후 proactive reclaim이 없었다

대응 감각:

- batch cgroup에 cold cache가 남는지 본다
- 종료 직후 controlled reclaim을 검토한다
- foreground는 `memory.low` 또는 `memory.min`로 보호한다

### 시나리오 2: reclaim을 걸었더니 오히려 다음 요청이 더 느리다

가능한 원인:

- hot cache를 밀었다
- 대상 cgroup이 실제로는 다시 곧 사용할 working set을 갖고 있었다
- reclaim 정책이 운영 시간대와 안 맞는다

이 경우는 reclaim을 pressure 완화가 아니라 cache eviction으로 사용한 셈이다.

### 시나리오 3: 메모리 여유는 있는데 특정 cgroup만 계속 pressure가 높다

가능한 원인:

- node 전체가 아니라 memcg 내부 cache hygiene가 나쁘다
- tmpfs/shmem 또는 batch cache가 예산을 잡고 있다
- background workload 정리가 뒤로 밀려 있다

## 코드로 보기

### 상태 확인

```bash
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.stat | rg 'file|inactive_file|active_file|workingset'
cat /sys/fs/cgroup/memory.pressure
```

### mental model

```text
background batch ends
  -> cold cache remains
  -> proactively reclaim background cgroup
  -> preserve foreground hot cache
```

주의:

- 이 제어는 workload를 모를 때 무작정 누르는 버튼이 아니다
- reclaim 전후 refault/pressure 변화를 같이 봐야 한다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 수동 proactive reclaim | cold cache hygiene에 유리하다 | hot cache를 밀면 역효과다 | batch 종료 직후 |
| `memory.high`만 사용 | 자동 pressure를 준다 | 시점 제어가 약하다 | 일반적 제한 |
| `memory.low/min` 보호 병행 | foreground를 지키기 쉽다 | 정책이 복잡해진다 | batch/API 혼재 |
| 아무 것도 안 함 | 단순하다 | cold cache 잔존과 noisy neighbor가 심해질 수 있다 | 소규모 단일 workload |

## 꼬리질문

> Q: `memory.reclaim`은 OOM 해결 버튼인가요?
> 핵심: 아니다. pressure가 터진 뒤보다 cold memory를 미리 정리하는 용도에 더 가깝다.

> Q: proactive reclaim이 항상 좋은가요?
> 핵심: 아니다. hot working set을 건드리면 refault와 latency가 오히려 커질 수 있다.

> Q: 무엇으로 효과를 검증하나요?
> 핵심: reclaim 전후의 `inactive_file`, workingset refault, PSI, foreground latency를 같이 본다.

## 한 줄 정리

`memory.reclaim`은 cgroup memory pressure를 앞당겨 정리하는 수단이지만, 좋은 사용법은 "많이 비웠다"가 아니라 "foreground hot cache를 덜 흔들었다"로 판단해야 한다.
