# Rollout Safety Master Note

> 한 줄 요약: rollout safety is the practice of changing production gradually, observably, and reversibly so that a bad release can stop before it spreads.

**Difficulty: Advanced**

> retrieval-anchor-keywords: rollout safety, canary, blue-green, rollback, feature flag, kill switch, blast radius, progressive delivery, traffic shifting, safe deploy, release guardrail

> related docs:
> - [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
> - [Feature Flags, Rollout, Dependency Management](../contents/software-engineering/feature-flags-rollout-dependency-management.md)
> - [Feature Flag Cleanup / Expiration](../contents/software-engineering/feature-flag-cleanup-expiration.md)
> - [Branch by Abstraction vs Feature Flag vs Strangler](../contents/software-engineering/branch-by-abstraction-vs-feature-flag-vs-strangler.md)
> - [Failure Amplification Master Note](./failure-amplification-master-note.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Safe rollout is not just "deploy slowly".

It is the combination of:

- limited blast radius
- observable metrics
- reversible change
- compatibility with old and new traffic

If any one of those is missing, rollout becomes a gamble.

## 깊이 들어가기

### 1. Rollout and release are different

Code can be deployed but not yet released.

Read with:

- [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)

### 2. Feature flags are safety rails, not architecture

Use them to control exposure, not to keep permanent branches alive.

Read with:

- [Feature Flags, Rollout, Dependency Management](../contents/software-engineering/feature-flags-rollout-dependency-management.md)
- [Feature Flag Cleanup / Expiration](../contents/software-engineering/feature-flag-cleanup-expiration.md)

### 3. Reversibility is the real test

If rollback is impossible because data is already mutated, the rollout was unsafe.

### 4. Canary needs meaningful metrics

Measure error rate, latency, and business outcome. If the signal is noisy, the canary cannot protect you.

### 5. Safety must resist amplification

If a slow or broken path triggers retries, stampede, or queue growth, rollout safety is gone.

Read with:

- [Failure Amplification Master Note](./failure-amplification-master-note.md)

## 실전 시나리오

### 시나리오 1: canary looks fine until traffic shifts

Likely cause:

- metrics not representative
- hidden dependency not exercised

### 시나리오 2: feature flag rollback works but data is wrong

Likely cause:

- code rollback is reversible, data rollback is not

### 시나리오 3: rollout triggers retry storm

Likely cause:

- timeout and retry policies not aligned

## 코드로 보기

### Rollout guardrail sketch

```yaml
rollout:
  percent: 10
  rollback_threshold:
    error_rate: 0.5%
    p99_ms: 300
  kill_switch: true
```

### Feature flag gate

```java
if (flags.isEnabled("new-flow")) {
    return newFlow();
}
return oldFlow();
```

### Reversible change note

```text
deploy -> observe -> expand -> revert if thresholds fail
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Canary | Small blast radius | Slow rollout | Risky changes |
| Blue-green | Fast rollback | Double infra | Critical services |
| Rolling | Cheap | Mixed versions live together | Stateless services |
| Permanent flag | Easy to flip | Tech debt | Short-lived experiments only |

## 꼬리질문

> Q: What makes a rollout safe?
> Intent: checks operational guardrails.
> Core: small blast radius, visibility, and a real rollback path.

> Q: Why is a feature flag not enough?
> Intent: checks structural safety.
> Core: flags control exposure, but they do not fix data compatibility.

> Q: Why should rollout metrics include business outcomes?
> Intent: checks signal quality.
> Core: latency alone can miss broken user paths.

## 한 줄 정리

Rollout safety is progressive delivery with explicit metrics, reversibility, and blast-radius control.
