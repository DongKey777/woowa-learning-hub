# Observability to Incident Master Note

> 한 줄 요약: observability only becomes valuable when it turns symptoms into a timeline, a containment decision, and a learning loop that lowers the chance of the next incident.

## 이 노트의 역할

이 노트는 `observability` 군집의 **보조 노트**다.

- 먼저 [Observability Debugging Master Note](./observability-debugging-master-note.md)로 신호를 읽는 법을 본다.
- 그 다음 이 노트에서 incident timeline, containment, rollback gate, learning loop처럼 **운영 대응**을 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: incident timeline, containment, blast radius, runbook, rollback gate, kill switch, shadow traffic, p99, error budget, detection to recovery, blameless review, root cause, contributing factors, signal correlation

> related docs:
> - [Incident Review and Learning Loop Architecture](../contents/software-engineering/incident-review-learning-loop-architecture.md)
> - [Observability Debugging Master Note](./observability-debugging-master-note.md)
> - [Latency Debugging Master Note](./latency-debugging-master-note.md)
> - [Spring Observability / Micrometer / Tracing](../contents/spring/spring-observability-micrometer-tracing.md)
> - [cache, message, observability](../contents/software-engineering/cache-message-observability.md)
> - [eBPF, perf, strace production tracing](../contents/operating-system/ebpf-perf-strace-production-tracing.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
> - [Feature Flags, Rollout, Dependency Management](../contents/software-engineering/feature-flags-rollout-dependency-management.md)
> - [Kill Switch Fast-Fail Ops](../contents/software-engineering/kill-switch-fast-fail-ops.md)
> - [Strangler Verification, Shadow Traffic Metrics](../contents/software-engineering/strangler-verification-shadow-traffic-metrics.md)
> - [Technical Debt Refactoring Timing](../contents/software-engineering/technical-debt-refactoring-timing.md)
> - [Failure Amplification Master Note](./failure-amplification-master-note.md)
> - [Resource Exhaustion Master Note](./resource-exhaustion-master-note.md)
> - [Queue Worker Reliability Master Note](./queue-worker-reliability-master-note.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Retrieval Failure Modes](../rag/retrieval-failure-modes.md)

## 핵심 개념

Observability is not the dashboard itself.

It is the ability to answer four questions quickly:

- what changed
- where it changed
- how far it spread
- what action should happen next

An incident workflow uses observability to choose containment before root cause analysis finishes.

## 깊이 들어가기

### 1. Symptoms must become a timeline

Good incident handling starts with order:

- first user complaint
- first metric deviation
- first alert
- first mitigation
- first confirmed recovery

Without a timeline, every person remembers a different incident.

### 2. Containment beats perfect diagnosis

The first goal is to stop the blast radius:

- roll back
- disable a feature flag
- drain traffic
- stop a bad batch
- kill a runaway worker

Root cause can wait until the system is safe.

### 3. Different signals answer different questions

- logs explain a specific failure
- metrics show scope and trend
- traces show the path
- profiles show where time went

If one signal is missing, the narrative becomes incomplete.

### 4. The decision should be operational, not just analytical

Incident response needs to answer:

- can we reduce load
- should we switch traffic
- is the rollback gate healthy
- is the runbook current

This is where observability meets deployment safety.

### 5. Learning only works if it changes the system

An incident review is successful only if it improves something concrete:

- alert threshold
- dashboard
- runbook
- test coverage
- canary gate
- kill switch scope

Otherwise the incident becomes a story, not a capability upgrade.

## 실전 시나리오

### 시나리오 1: p99 latency spikes right after deploy

Possible actions:

- check canary diff
- compare trace spans before and after deploy
- inspect JIT warmup, cache cold start, and query plan changes
- roll back if the blast radius is growing

### 시나리오 2: queue lag keeps rising even though the app looks healthy

Possible actions:

- inspect worker saturation
- check downstream retry amplification
- verify whether a single partition or key is hot

### 시나리오 3: error rate is low but user complaints are high

Possible actions:

- look for one bad tenant or one region
- inspect sparse logs and trace sampling
- correlate complaints with a small but important path

### 시나리오 4: recovery happened, but the incident repeats

That usually means the action item did not change the system:

- alert was not updated
- rollback was too slow
- runbook was not used
- ownership stayed unclear

## 코드로 보기

### Incident action item template

```markdown
## Incident Action Item
- Owner: platform-team
- Due: 2026-05-01
- Change: add rollback gate for batch jobs
- Verification: runbook drill + canary drill
- Metric: reduce mean detection time by 30%
```

### Minimal timeline sketch

```text
00:00 first alert
00:02 user complaints begin
00:05 rollback decision made
00:08 containment complete
00:20 root cause identified
00:30 follow-up action item opened
```

### Containment checklist

```bash
check canary health
check rollback readiness
check kill switch scope
check downstream saturation
check whether the incident is still growing
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| More telemetry | Better diagnosis | Higher cost and noise | Critical paths |
| Narrow telemetry | Lower cost | Missing evidence | Stable, low-risk paths |
| Fast rollback | Shrinks blast radius | May hide the root cause temporarily | Deploy-related incidents |
| Deep forensic analysis | Better long-term learning | Slower mitigation | After containment |
| Blameless review | Better learning loop | Can become vague if undisciplined | Mature incident process |

The right order is containment first, then explanation, then prevention.

## 꼬리질문

> Q: Why is a timeline the first thing to build in an incident?
> Intent: checks whether the person can reconstruct causality.
> Core: without time order, diagnosis and mitigation both drift.

> Q: Why should containment happen before root cause analysis finishes?
> Intent: checks operational judgment.
> Core: an incident is still active until the blast radius is under control.

> Q: Why are logs, metrics, traces, and profiles all needed?
> Intent: checks multi-signal reasoning.
> Core: each signal answers a different part of the causal story.

> Q: Why does a postmortem need to change the system?
> Intent: checks learning-loop thinking.
> Core: if nothing in the system changes, the same failure will recur.

## 한 줄 정리

Observability-to-incident is the loop that turns noisy signals into a timeline, uses that timeline to contain the blast radius, and converts the incident into a system improvement.
