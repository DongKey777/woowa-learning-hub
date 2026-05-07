---
schema_version: 3
title: OOM Killer Scoring Victim Selection
concept_id: operating-system/oom-killer-scoring-victim-selection
canonical: true
category: operating-system
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- oom-killer-scoring
- victim-selection
- oom-score-adj
- badness-score
aliases:
- OOM killer scoring
- victim selection
- oom_score_adj
- badness score
- cgroup OOM victim
- memory protection ratio
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/major-minor-page-faults-runtime-diagnostics.md
- contents/operating-system/memory-management-numa-page-replacement-thrashing.md
- contents/operating-system/container-cgroup-namespace.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
- contents/operating-system/memory-low-min-reclaim-protection.md
expected_queries:
- OOM killer는 어떤 scoring으로 victim process를 선택해?
- oom_score_adj와 memory usage, protection ratio는 victim selection에 어떤 영향을 줘?
- cgroup OOM에서 아무 process나 죽는 게 아니라는 걸 어떻게 설명해?
- OOM victim selection을 운영에서 확인하려면 어떤 signal을 봐야 해?
contextual_chunk_prefix: |
  이 문서는 OOM killer가 아무 process나 죽이지 않고 memory usage, badness score,
  oom_score_adj, cgroup boundary와 protection context를 종합해 victim을 고르는 과정을 설명한다.
---
# OOM Killer Scoring, Victim Selection

> 한 줄 요약: OOM killer는 "아무나" 죽이지 않고, 메모리 사용량과 보호 비율을 종합해 가장 덜 적절한 희생자를 고른다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: oom_score, oom_score_adj, badness score, victim selection, memcg OOM, global OOM, killed process, score adjustment

## 핵심 개념

Linux OOM killer는 메모리 압박이 너무 심해서 더 이상 정상적인 reclaim이 어려울 때 희생자를 고른다. 이때 중요한 것은 단순 메모리 사용량이 아니라, **죽여도 되는 정도**를 정량화한 점수다.

- `oom_score`: 현재 프로세스의 OOM 점수다
- `oom_score_adj`: 점수를 인위적으로 올리거나 내려 보호/희생 정도를 조절한다
- `memcg OOM`: cgroup 경계 안에서 발생한 OOM이다
- `global OOM`: 시스템 전체 메모리 압박으로 발생한 OOM이다

왜 중요한가:

- "가장 많이 쓴 놈"이 꼭 죽는 것은 아니다
- 프로세스가 적게 써도 `oom_score_adj` 때문에 먼저 죽을 수 있다
- 컨테이너 OOM과 호스트 OOM은 원인과 대응이 다르다

이 문서는 [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)를 더 좁혀서, 점수와 희생자 선택을 운영 관점에서 해석한다.

## 깊이 들어가기

### 1. score는 메모리만으로 정해지지 않는다

OOM 점수는 단순 RSS만 보는 것이 아니다. 커널은 여러 요소를 반영해 "이 프로세스를 죽이면 전체가 덜 아픈가"를 보려 한다.

- 메모리 사용량
- `oom_score_adj`
- 프로세스 성격과 보호 설정
- cgroup 경계

즉 score는 숫자이지만, 실제 의미는 "희생 가능성"이다.

### 2. `oom_score_adj`는 강력하지만 위험하다

`oom_score_adj`는 특정 프로세스를 보호하거나 더 잘 죽게 만들 수 있다.

- 값이 낮으면 보호받는다
- 값이 높으면 희생자 후보가 되기 쉽다
- 잘못 쓰면 시스템이 덜 중요한 프로세스를 못 죽여 더 큰 장애로 번질 수 있다

운영에서는 보통 핵심 daemon과 재시작 가능한 worker를 구분한다.

### 3. memcg OOM과 global OOM은 희생자 범위가 다르다

- memcg OOM: 해당 cgroup 안에서 희생자를 고른다
- global OOM: 시스템 전체에서 가장 적절한 희생자를 고른다

이 차이를 모르면 "호스트 메모리는 남는데 왜 컨테이너가 죽었지?" 혹은 "컨테이너 하나 때문에 왜 노드 전체가 흔들리지?" 같은 질문에 막힌다.

### 4. 희생자 선택은 재시작 가능성과 별개다

실제로는 "무거운 프로세스"보다 "잘 복구되는 프로세스"를 죽이는 편이 낫다. 그래서 worker, cache, batch는 상대적으로 희생 가능성이 높다.

## 실전 시나리오

### 시나리오 1: 같은 메모리 사용량인데 항상 특정 프로세스만 죽는다

가능한 원인:

- `oom_score_adj`가 높다
- cgroup 경계 안에서 더 나쁜 점수를 받는다
- 프로세스 메모리 구성상 reclaim이 어렵다

진단:

```bash
cat /proc/<pid>/oom_score
cat /proc/<pid>/oom_score_adj
cat /proc/<pid>/status | grep -E 'VmRSS|VmSize|Threads'
```

### 시나리오 2: 컨테이너가 죽었는데 호스트는 안정적이다

가능한 원인:

- memcg limit을 넘었다
- 호스트 여유 메모리와 상관없이 cgroup에서 OOM이 났다

진단:

```bash
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.events
dmesg | tail -n 50
```

### 시나리오 3: 프로세스를 살리고 싶어서 `oom_score_adj`만 낮췄는데 효과가 이상하다

가능한 원인:

- 실제 압박은 cgroup 전체다
- 다른 프로세스가 더 큰 희생 대상으로 남아 있다
- reclaim이 이미 너무 늦어 OOM이 난다

즉 보호 설정은 보조 수단이지, 메모리 설계를 대신하지 않는다.

## 코드로 보기

### 현재 점수 확인

```bash
cat /proc/<pid>/oom_score
cat /proc/<pid>/oom_score_adj
```

### 보호 설정 예시

```bash
echo -500 > /proc/<pid>/oom_score_adj
```

주의점:

- 핵심 서비스만 과하게 보호하면 OOM이 더 큰 장애로 번질 수 있다
- 보통은 재시작 쉬운 worker를 더 먼저 죽이게 설계한다

### k8s/컨테이너 문맥에서 확인

```bash
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.peak
```

### 희생자 선정을 이해하는 단순 모델

```text
score = memory usage + penalty/bonus from oom_score_adj + cgroup context
highest score -> most killable
```

실제 커널은 더 복잡하지만, 운영 감각은 이 정도면 충분하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 낮은 `oom_score_adj` | 핵심 프로세스를 보호한다 | OOM 희생자 선택이 왜곡될 수 있다 | system daemon |
| 높은 `oom_score_adj` | 재시작 가능한 워커를 우선 희생시킨다 | 잘못 잡으면 중요한 worker가 죽는다 | 보조 작업 |
| cgroup 분리 | 범위를 명확히 한다 | 설정이 복잡하다 | 멀티테넌트 |
| 메모리 여유 확보 | OOM 자체를 줄인다 | 자원 효율이 떨어진다 | 핵심 API |

## 꼬리질문

> Q: OOM killer는 가장 많이 쓰는 프로세스를 죽이나요?
> 핵심: 꼭 그렇지 않다. 점수와 보호 설정을 함께 본다.

> Q: `oom_score_adj`를 낮추면 안전한가요?
> 핵심: 아니다. OOM 경계와 reclaim 상태를 같이 봐야 한다.

> Q: memcg OOM과 global OOM의 차이는?
> 핵심: 희생자 선택 범위가 cgroup 내부냐 시스템 전체냐의 차이다.

> Q: 희생자 선택만 조정하면 메모리 문제를 끝낼 수 있나요?
> 핵심: 아니다. pressure, reclaim, swap, limit 설계가 같이 가야 한다.

## 한 줄 정리

OOM killer의 핵심은 메모리를 많이 쓴 놈을 죽이는 것이 아니라, 시스템과 cgroup 경계에서 가장 덜 치명적인 희생자를 고르는 것이다.
