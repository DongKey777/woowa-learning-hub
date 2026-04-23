# Dual-Read Comparison / Verification Platform 설계

> 한 줄 요약: dual-read comparison과 verification 플랫폼은 old/new read path를 동시에 평가해 응답 차이, invariant 위반, 성능 편차를 측정하고, 안전한 read cutover를 위한 증거를 축적하는 검증 제어 시스템이다.

retrieval-anchor-keywords: dual read comparison, verification platform, shadow read, response diff, invariant check, read path cutover, compare budget, sampled verification, semantic diff, baseline response, read parity, promotion gate, migration verification evidence, projection freshness, read model cutover, watermark parity, strict screen fallback, database security bridge, auth shadow evaluation, authorization decision parity, tenant claim drift, policy shadow compare

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)
> - [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Document Search Ranking Platform 설계](./document-search-ranking-platform-design.md)
> - [Consistency Repair / Anti-Entropy Platform 설계](./consistency-repair-anti-entropy-platform-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md)
> - [Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)
> - [Read Model Cutover Guardrails](../design-pattern/read-model-cutover-guardrails.md)
> - [Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md)
> - [Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)
> - [Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md)
> - [Replica Lag and Read-after-write Strategies](../database/replica-lag-read-after-write-strategies.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)

## 핵심 개념

schema migration이나 read engine 교체에서 가장 어려운 질문은 이것이다.

- "새 경로가 old 경로와 정말 같은 의미를 내는가?"

테스트 환경에서는 같아 보여도 실제 production query mix에서는 다를 수 있다.
그래서 dual-read verification이 필요하다.

- primary path는 기존 응답을 계속 제공
- candidate path는 같은 입력을 별도로 읽음
- 비교 엔진은 semantic diff와 invariant 위반을 측정

즉, dual-read verification은 단순 shadow query가 아니라 **read cutover 전 검증 증거를 쌓는 비교 플랫폼**이다.

## 깊이 들어가기

### 1. 언제 필요한가

대표적인 상황:

- DB schema를 바꾸며 read path도 변경
- 검색 엔진이나 ranking stack 교체
- 캐시 / projection / denormalized view로 조회 경로 이전
- 권한 필터 또는 pricing 계산 로직 교체

write migration보다 read migration이 쉬워 보이지만, 실제로는 사용자 체감과 품질 회귀가 더 은밀하게 숨어 있다.

### 2. Capacity Estimation

예:

- 전체 조회 요청 12만 QPS
- sampled dual read 2%
- 평균 응답 payload 8 KB
- diff 대상 필드 30개

이때 봐야 할 숫자:

- verification QPS
- compare latency overhead
- diff storage volume
- mismatch ratio
- candidate read cost
- false positive rate

dual read는 응답에 사용하지 않아도 source, cache, index를 실제로 두 번 칠 수 있으므로 샘플링과 budget이 중요하다.

### 3. Comparison control plane

좋은 플랫폼은 다음을 제어한다.

- 어떤 route/query만 검증할지
- 샘플링 비율
- normalized diff 규칙
- 반드시 일치해야 하는 invariant
- mismatch 임계치와 promotion gate
- diff artifact 보관 기간

이 메타데이터가 없으면 dual read는 "로그를 잔뜩 남기는데 아무도 믿지 않는 시스템"이 된다.

### 4. Semantic diff와 raw diff는 다르다

많은 응답은 byte-for-byte 일치가 필요하지 않다.

예:

- 정렬이 조금 달라도 동등 집합이면 허용 가능
- score는 달라도 top-k membership은 중요
- timestamp / freshness는 오차 범위가 있을 수 있음
- null vs empty list는 도메인에 따라 같거나 다를 수 있음

그래서 비교 규칙은 보통 세 층으로 나뉜다.

- raw diff
- normalized diff
- invariant diff

### 5. Mismatch triage

diff가 났다고 전부 버그는 아니다.
보통 다음으로 분류한다.

- expected divergence
- stale-data divergence
- correctness bug
- performance-only regression
- insufficient context

이 triage가 없으면 mismatch가 쌓이기만 하고 cutover 증거로 못 쓴다.

### 6. Promotion evidence

dual-read 플랫폼은 단순 로그가 아니라 승격 근거를 제공해야 한다.

예:

- 최근 24시간 invariant mismatch 0건
- top-k diff 허용 범위 이하
- 특정 tenant segment만 divergence 있음
- candidate p95가 baseline 대비 3% 이내

즉, promotion gate는 canary analysis와 연결되지만, 더 correctness 중심의 증거를 준다.

### 7. read parity와 auth parity는 같은 bridge gate에서 닫혀야 한다

dual-read comparison은 read-model과 response invariant가 같은지 보여 주지만,
database/security bridge가 닫히는지까지 혼자 증명하지는 못한다.

- traffic shadowing은 실제 route, auth plugin, downstream load가 production request mix를 버티는지 본다
- dual-read comparison은 같은 row/projection/response invariant가 나오는지 본다
- auth shadow evaluation은 같은 request context에서 old/new policy가 같은 allow/deny를 내는지 본다

즉 read cutover가 claim semantic, tenant mapping, workload identity, auth plugin 교체와 겹치면
[Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md),
[Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md),
[Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)을 같은 verification path로 읽는 편이 안전하다.

대표적으로 다음 상태가 가능하다.

- dual-read diff는 0인데 shadow auth에서는 `old_deny -> new_allow`가 남는다
- response parity는 맞는데 shadow route의 auth plugin latency가 올라 canary에서만 실패한다
- projection freshness는 green인데 tenant claim drift 때문에 dedicated cell에서만 cross-tenant allow가 생긴다

따라서 dual-read evidence는 bridge gate의 한 축이지, 승격 전체를 닫는 단독 근거는 아니다.

### 8. Failure mode

verification 시스템이 production을 해치면 안 된다.

대응:

- bounded sample rate
- candidate timeout이 지나면 diff skip
- low-priority async compare
- diff store TTL
- compare worker bulkhead

검증 때문에 primary latency가 나빠지면 본말이 전도된다.

## 실전 시나리오

### 시나리오 1: 검색 조회 경로 교체

문제:

- 새 ranking pipeline이 relevance는 좋아 보이지만 실제 query mix에서 확인이 어렵다

해결:

- 일부 query를 dual read로 보낸다
- top-k overlap, empty result, ACL filter mismatch를 측정한다
- semantic diff 기준이 통과할 때만 cutover한다

### 시나리오 2: denormalized read model 도입

문제:

- 기존 join-heavy DB 조회를 precomputed projection으로 바꾸고 싶다

해결:

- old path와 projection path를 동시에 읽는다
- totals, status, entitlement 같은 invariant를 비교한다
- mismatch가 높은 tenant를 별도 repair 대상으로 보낸다

### 시나리오 3: 권한 정책 엔진 교체

문제:

- 새 authz evaluator가 예전과 같은 허용/거부를 내는지 불확실하다

해결:

- allow/deny와 explain reason을 비교한다
- false deny는 high severity로 분류한다
- candidate mismatch는 promotion gate에서 즉시 차단한다

## 코드로 보기

```pseudo
function verify(request):
  baseline = primary.read(request)
  if !policy.shouldSample(request):
    return baseline

  candidate = asyncReadCandidate(request, timeout=policy.candidateTimeout)
  diff = comparator.compare(
    normalize(baseline),
    normalize(candidate),
    policy.invariants
  )
  reportStore.record(request.key, diff)
  return baseline
```

```java
public DiffResult compare(Response baseline, Response candidate) {
    NormalizedResponse left = normalizer.normalize(baseline);
    NormalizedResponse right = normalizer.normalize(candidate);
    return diffEngine.compare(left, right, invariantSet.current());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Raw byte diff | 단순하다 | false positive가 많다 | strict protocol 응답 |
| Semantic diff | 실무적이다 | 규칙 관리가 어렵다 | 검색, 추천, projection |
| Full dual read | 증거가 풍부하다 | 비용이 크다 | 낮은 QPS, high-risk cutover |
| Sampled dual read | 운영 부담이 적다 | corner case를 놓칠 수 있다 | 대부분의 production |
| Async compare | primary를 보호한다 | 분석 지연이 생긴다 | high-QPS read path |

핵심은 dual-read comparison이 디버깅 보조가 아니라 **read cutover의 correctness 증거를 축적하고 promotion gate를 지원하는 검증 플랫폼**이라는 점이다.

## 꼬리질문

> Q: shadow read와 dual read comparison은 같은 건가요?
> 의도: 검증 범위 차이 이해 확인
> 핵심: shadow read는 candidate 실행 자체에 가깝고, dual read comparison은 normalized diff와 promotion evidence까지 포함하는 더 넓은 개념이다.

> Q: 왜 byte-level diff로 끝내면 안 되나요?
> 의도: semantic diff 필요성 이해 확인
> 핵심: ordering, score, freshness처럼 의미상 허용 가능한 차이가 많기 때문이다.

> Q: dual read mismatch가 조금 있어도 cutover할 수 있나요?
> 의도: 도메인별 허용 오차 감각 확인
> 핵심: invariant 위반 여부와 사용자 영향이 더 중요하며, expected divergence는 별도 분류해야 한다.

> Q: verification 시스템이 가장 피해야 할 것은 무엇인가요?
> 의도: 운영 보호 이해 확인
> 핵심: candidate 비교 때문에 primary latency나 downstream 부하를 악화시키는 것이다.

## 한 줄 정리

Dual-read comparison과 verification 플랫폼은 old/new read path의 차이를 semantic diff와 invariant 기준으로 측정해, 안전한 read cutover를 위한 증거를 production에서 축적하는 검증 제어 시스템이다.
