# Artifact Supply Chain Master Note

> 한 줄 요약: artifact supply chain is the path from source code to signed, verifiable, deployable output, and every step must preserve provenance and trust.

**Difficulty: Advanced**

> retrieval-anchor-keywords: artifact supply chain, SBOM, signing, provenance, dependency management, build artifact, image trust, release artifact, attestation, checksum, tamper detection, supply chain security

> related docs:
> - [Supply Chain Security / SBOM / Signing Basics](../contents/security/supply-chain-security-sbom-signing-basics.md)
> - [Feature Flags, Rollout, Dependency Management](../contents/software-engineering/feature-flags-rollout-dependency-management.md)
> - [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
> - [Data Contract Ownership Lifecycle](../contents/software-engineering/data-contract-ownership-lifecycle.md)
> - [Service Ownership Catalog Boundaries](../contents/software-engineering/service-ownership-catalog-boundaries.md)
> - [Change Ownership Handoff Boundaries](../contents/software-engineering/change-ownership-handoff-boundaries.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Artifacts are not trusted just because they were built by your CI.

The supply chain must tell you:

- what source produced the artifact
- what dependencies were included
- what build steps were run
- whether the artifact was signed
- who owns the release and rollback

## 깊이 들어가기

### 1. Provenance matters

You need to know where the artifact came from and which inputs affected it.

Read with:

- [Supply Chain Security / SBOM / Signing Basics](../contents/security/supply-chain-security-sbom-signing-basics.md)

### 2. Dependency management is part of the artifact chain

If dependencies drift, the artifact is no longer the same release shape.

Read with:

- [Feature Flags, Rollout, Dependency Management](../contents/software-engineering/feature-flags-rollout-dependency-management.md)

### 3. Release artifacts need rollout and rollback ownership

An artifact is only useful if the deployment path knows how to promote or revert it safely.

Read with:

- [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)

### 4. Service ownership and handoff are supply-chain problems too

If no one owns the artifact after build, nobody owns the incident when it breaks.

Read with:

- [Service Ownership Catalog Boundaries](../contents/software-engineering/service-ownership-catalog-boundaries.md)
- [Change Ownership Handoff Boundaries](../contents/software-engineering/change-ownership-handoff-boundaries.md)

### 5. Contract changes need artifact discipline

Build and release artifacts should reflect schema and contract version changes explicitly.

Read with:

- [Data Contract Ownership Lifecycle](../contents/software-engineering/data-contract-ownership-lifecycle.md)

## 실전 시나리오

### 시나리오 1: artifact is built from unpinned dependencies

Likely cause:

- dependency drift
- unverifiable release

### 시나리오 2: signed artifact is deployed but provenance is unknown

Likely cause:

- missing SBOM or attestation

### 시나리오 3: rollback fails because only the artifact was versioned, not ownership

Likely cause:

- deploy path and service ownership were not aligned

## 코드로 보기

### Provenance sketch

```text
source + dependencies + build steps -> signed artifact -> deploy
```

### Release metadata sketch

```yaml
artifact:
  version: 1.4.2
  digest: sha256:...
  owner: payments-team
  sbom: present
```

### Verification gate

```bash
cosign verify <artifact>
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Unsigned artifacts | Simple | Untrusted | Prototypes only |
| Signed artifacts | Provenance | Tooling overhead | Production releases |
| Pinned dependencies | Reproducible | Update work | Stable release pipelines |
| Mutable latest tags | Convenient | Risky | Avoid in production |

## 꼬리질문

> Q: Why is the build artifact not enough by itself?
> Intent: checks provenance and ownership.
> Core: you also need dependency, signing, and release context.

> Q: Why do dependency updates affect supply chain trust?
> Intent: checks reproducibility.
> Core: the artifact changes if inputs are not pinned and verified.

> Q: Why is service ownership part of the supply chain?
> Intent: checks operational accountability.
> Core: someone must own the artifact after it ships.

## 한 줄 정리

Artifact supply chain is the provenance and trust chain that makes a built output safe to deploy, rollback, and audit.
