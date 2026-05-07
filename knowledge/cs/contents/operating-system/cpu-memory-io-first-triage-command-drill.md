---
schema_version: 3
title: '서버가 느릴 때 CPU / Memory / I/O 첫 분류 커맨드 드릴'
concept_id: operating-system/cpu-memory-io-first-triage-command-drill
canonical: false
category: operating-system
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 72
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- runtime-first-triage
- cpu-memory-io-split
- os-observation-commands
aliases:
- 서버 느림 첫 분류
- CPU memory IO triage
- top free iostat drill
- load average io wait memory pressure
- OS command drill
symptoms:
- 서버가 느린데 CPU 문제인지 메모리 문제인지 디스크 I/O 문제인지 모르겠다
- load average가 높지만 실제 병목 계층을 분리하지 못한다
- 애플리케이션 로그만 보고 OS 신호를 확인하지 않는다
intents:
- drill
- troubleshooting
prerequisites:
- operating-system/beginner-symptom-to-doc-map
- operating-system/scheduler-observation-starter-guide
next_docs:
- operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait
- operating-system/oom-killer-cgroup-memory-pressure
- operating-system/deleted-open-file-space-leak-log-rotation
linked_paths:
- contents/operating-system/beginner-symptom-to-doc-map.md
- contents/operating-system/scheduler-observation-starter-guide.md
- contents/operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md
- contents/operating-system/cgroup-cpu-throttling-quota-runtime-debugging.md
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/deleted-open-file-space-leak-log-rotation.md
- contents/operating-system/fd-exhaustion-ulimit-diagnostics.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- 서버가 느릴 때 CPU memory IO 중 어디 문제인지 첫 커맨드로 나눠보고 싶어
- load average가 높은데 top free iostat에서 무엇을 봐야 해?
- 운영체제 관점에서 느린 서버를 5분 안에 분류하는 연습을 하고 싶어
- 애플리케이션 로그 전에 OS 신호를 어떤 순서로 확인해?
contextual_chunk_prefix: |
  이 문서는 서버가 느릴 때 CPU saturation, memory pressure, disk I/O wait,
  fd leak 같은 OS 계층 원인을 첫 커맨드로 나누는 operating-system drill이다.
  top, free, vmstat, iostat, load average, io wait, OOM 같은 질의를 초급
  런타임 triage 연습으로 연결한다.
---
# 서버가 느릴 때 CPU / Memory / I/O 첫 분류 커맨드 드릴

> 한 줄 요약: "서버가 느리다"는 증상은 먼저 CPU가 바쁜지, 메모리가 밀리는지, I/O를 기다리는지, 파일 디스크립터 같은 한계에 걸렸는지 5분 안에 갈라야 한다.

**난이도: 🟢 Beginner**

## 드릴 1. load average만 보고 결론 내리지 않기

질문:

```text
load average가 8이다. CPU 문제라고 말해도 될까?
```

정답:

아직 안 된다. load average에는 CPU에서 실행 가능한 task뿐 아니라 일부 I/O wait 상태도 섞인다. `top`, `vmstat`, `iostat`로 나눠야 한다.

확인 순서:

```text
top      -> CPU us/sy/id/wa, runnable process
vmstat 1 -> r, b, si/so, us/sy/id/wa
iostat 1 -> await, util
```

## 드릴 2. CPU saturation 신호 찾기

장면:

- `top`에서 idle이 낮다.
- `vmstat`의 `r`이 CPU core 수보다 계속 크다.
- cgroup 환경에서는 host CPU는 남는데 container만 throttling된다.

다음 문서:

- [Load Average Triage](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)
- [cgroup CPU Throttling](./cgroup-cpu-throttling-quota-runtime-debugging.md)

## 드릴 3. Memory pressure 신호 찾기

장면:

- `free`의 available memory가 낮다.
- `vmstat`에서 swap in/out이 보인다.
- 로그에 `Killed` 또는 `OOMKilled`가 남는다.

주의:

Linux의 `free`에서 cache가 크다고 곧바로 메모리 부족은 아니다. available, reclaim, OOM event를 같이 봐야 한다.

## 드릴 4. I/O wait 신호 찾기

장면:

- CPU idle은 남는데 응답이 느리다.
- `top`의 `%wa`가 높다.
- `iostat`에서 await/util이 높다.

다음 질문:

- 디스크 자체가 느린가
- flush/writeback이 몰렸는가
- 로그 파일 삭제 후 open fd가 공간을 붙잡는가

## 미니 체크리스트

```text
1. top에서 CPU idle / iowait를 본다
2. vmstat 1에서 r, b, si, so를 본다
3. free -h에서 available과 swap을 본다
4. iostat 1에서 await/util을 본다
5. container면 cgroup throttling과 memory.events를 본다
```

## 한 줄 정리

느린 서버 triage는 `CPU 바쁨`, `memory pressure`, `I/O wait`, `limit hit`를 먼저 나누는 연습부터 시작한다.
