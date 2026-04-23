# Tenant-Scoped Config Incident Recovery 설계

> 한 줄 요약: tenant-scoped config incident recovery 설계는 특정 tenant override, tenant-class 정책, route/entitlement cutover 오배포가 났을 때 global config는 유지한 채 영향 scope만 write-freeze, scoped rollback, reversible soak으로 복구하는 multi-tenant 운영 설계다.
>
> 문서 역할: 이 문서는 multi-tenant config 장애를 "global rollback"이 아니라 "scope-local rollback + reversible cutover"로 다루는 deep dive다.

retrieval-anchor-keywords: tenant scoped config recovery, tenant override rollback, config incident recovery, tenant config freeze, scoped last known good, tenant policy rollback, override blast radius, tenant-specific config incident, scoped config recovery, tenant config quarantine, tenant write freeze, tenant rollback window, reversible config cutover, scoped safe default, tenant config thaw, tenant override freeze, config soak window

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Config Rollback Safety 설계](./config-rollback-safety-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)
> - [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)
> - [멀티 테넌트 SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Cell-Based Architecture / Blast Radius Isolation 설계](./cell-based-architecture-blast-radius-isolation-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)

## 핵심 개념

multi-tenant 시스템에서는 잘못된 config가 항상 전체 장애로 번질 필요는 없다.
문제는 영향 범위를 얼마나 빨리 좁히고, 그 scope를 얼마나 안전하게 되돌릴 수 있느냐다.

대표 상황:

- 특정 enterprise tenant override 실수
- 일부 tenant class만 잘못된 entitlement 정책
- 특정 region+tenant 조합의 route cutover mismatch
- config publish는 끝났지만 일부 consumer만 old/new 버전이 섞인 partial propagation

이런 경우 global snapshot 전체 rollback은 과하다.
이미 배포된 안전한 global fix까지 같이 사라질 수 있고, 정상 tenant도 불필요하게 흔들린다.

즉, 목표는 **전체 시스템을 되감지 않고 영향 scope만 격리, 동결, 복구하고 잠시 reversible 상태로 관찰하는 것**이다.

## 깊이 들어가기

### 1. incident 유형부터 나눠야 한다

tenant-scoped config incident는 모두 같은 방식으로 복구되지 않는다.
먼저 "무엇이 잘못되었는지"를 유형으로 나눠야 한다.

| incident 유형 | 대표 예시 | 초동 조치 | 복구 포인트 |
|---|---|---|---|
| override value 오류 | 특정 tenant rate limit을 10배 낮춤 | override freeze | 해당 tenant LKG로 롤백 |
| precedence / merge 오류 | tenant class 정책이 region 정책을 덮어씀 | publish halt | merge rule 수정 후 scoped republish |
| partial propagation | 일부 agent만 새 policy를 적용 | scope pin | convergence 확인 후 replay |
| dependency cutover mismatch | tenant route는 바뀌었는데 target receiver가 cold | write-freeze + safe default route | old route로 reversible cutback |
| entitlement leak | premium 기능이 일부 tenant에 과다 노출 | feature quarantine | tenant list 확정 후 correction |

즉, tenant incident는 단순히 "config가 틀렸다"가 아니라
"어느 계층이 틀렸고 지금 당장 무엇을 멈춰야 하는가"를 먼저 분리해야 한다.

### 2. scope graph가 recovery 속도를 결정한다

좋은 시스템은 config key만 저장하지 않고 scope graph도 같이 저장한다.

필요한 메타데이터:

- `change -> affected scopes`
- `scope -> active override chain`
- `scope -> current consumers / agents / route targets`
- `scope -> freeze 대상 write path`
- `scope -> safe default or previous route`

보통 config layering은 다음 레이어를 가진다.

- global default
- environment
- region
- tenant class
- tenant-specific override

incident recovery의 핵심은 "어느 레이어가 문제인지"뿐 아니라
"그 레이어가 실제로 어떤 tenant와 어떤 경로를 건드렸는지"를 바로 찾는 것이다.

그래야 다음이 가능하다.

- 영향 tenant 자동 식별
- unaffected tenant 계속 진행
- suspect scope만 strict validation path로 전환
- support/CS에 영향 범위를 바로 설명

### 3. scoped last-known-good는 rollback safety envelope와 함께 저장해야 한다

전체 LKG만 있으면 tenant incident 대응이 둔해진다.
하지만 scope snapshot만 저장해도 충분하지 않다.

실전에서 필요한 것은 다음 묶음이다.

- per-tenant last-known-good
- per-tenant-class last-known-good
- per-region+tenant scope snapshot
- scope를 읽는 consumer version 정보
- dependency readiness 정보
- freeze / thaw policy

예를 들어 route override를 tenant 단위로 롤백하더라도,
old route receiver가 이미 정리되었거나 old parser가 새 schema를 이해하지 못하면 rollback은 명목상으로만 가능하다.

그래서 scoped LKG는 단순 config bytes가 아니라
**"이 scope를 어떤 consumer 집합이 어떤 dependency 상태에서 안전하게 읽을 수 있었는가"라는 rollback safety envelope**를 같이 가져야 한다.

이게 없으면 다음 문제가 생긴다.

- LKG는 있는데 old receiver가 이미 cleanup됨
- tenant class 정책만 되돌렸는데 tenant override와 충돌함
- rollback 후에도 일부 agent는 new config를 계속 참조함
- frozen override를 너무 빨리 thaw해서 재발함

### 4. tenant-scoped write-freeze window가 필요한 순간이 있다

모든 config incident가 write-freeze를 요구하지는 않는다.
하지만 아래처럼 write path나 authority transfer가 얽히면 short freeze가 필요하다.

- route cutover가 잘못돼 old/new 경로가 동시에 write를 받을 수 있음
- entitlement 정책이 billing side effect와 연결됨
- tenant partition reassignment와 config override가 함께 움직임
- override correction 중 operator가 또 다른 change를 겹쳐 보낼 수 있음

이때 보통 다음 순서를 사용한다.

1. scope-local publish halt
2. tenant override freeze
3. 필요한 write path만 fence token으로 동결
4. in-flight 요청 drain 또는 buffer
5. scoped LKG 또는 safe default publish

원칙:

- freeze 대상은 가능한 좁게 잡는다
- freeze 시간은 짧게 유지한다
- reject / buffer / retry 정책을 명시한다
- freeze 종료 조건은 soak 관찰과 연결한다

즉, tenant-scoped write-freeze는 stateful migration의 대형 freeze를 tenant scope로 축소한 형태다.
핵심은 전역 정지 없이 "문제가 난 authority 경계만 잠깐 얼리는 것"이다.

### 5. rollback은 끝이 아니라 reversible cutover의 시작일 수 있다

tenant incident 복구는 종종 다음 상태 전이를 가진다.

```text
DETECT
 -> FREEZE_SCOPE
 -> PUBLISH_SCOPED_LKG_OR_SAFE_DEFAULT
 -> REVERSIBLE_SOAK
 -> THAW_SCOPE
 -> CLEANUP_OVERRIDE
```

여기서 중요한 것은 `PUBLISH_SCOPED_LKG`와 `CLEANUP_OVERRIDE`를 바로 붙이지 않는 것이다.

`REVERSIBLE_SOAK` 구간에서는 다음을 유지한다.

- bad override를 삭제하지 않고 quarantine 상태로 보존
- old/new route diff와 error burst를 관찰
- 필요하면 rollback 전 상태로 forensic replay 가능하게 audit trail 유지
- support 응대를 위한 영향 tenant timeline 유지

즉, scoped rollback 자체가 하나의 reversible cutover다.
특히 route, throttling, entitlement처럼 의미가 큰 config는 "되돌렸다"가 아니라
"되돌린 뒤 잠시 지켜보는 state transition"으로 봐야 안전하다.

### 6. rollback보다 quarantine이 나은 경우도 있다

다음 상황에서는 즉시 rollback보다 quarantine 또는 safe default cutback이 낫다.

- LKG도 이미 의미적으로 오래되었음
- rollback 대상 route가 이미 warm state를 잃었음
- tenant class 정책을 통째로 되돌리면 다른 tenant까지 흔들림
- 원인 분석 전 잘못된 override를 다시 배포할 위험이 큼

대표 조치:

- tenant request quarantine
- temporary feature kill
- safe baseline route 강제
- cell/tenant reassignment
- support-visible maintenance mode

즉, config incident recovery는 "무조건 되돌리기"가 아니라
"scope를 안전 상태에 붙들어 두고 재승격 전까지 blast radius를 제한하는 것"이다.

### 7. Capacity Estimation

예:

- tenant override 수만 개
- tenant별 config merge depth 4단계
- scoped rollback 대상 tenant 수 최대 수백 개
- per-scope freeze 허용 시간 5초
- reversible soak 목표 10분

이때 봐야 할 숫자:

- scope resolution latency
- affected tenant cardinality
- scoped rollback fan-out
- override diff size
- tenant freeze duration
- soak 동안 error budget burn
- thaw 전 manual review backlog

multi-tenant config는 전체 크기보다
**scope isolation latency와 reversible window 운영 비용**이 더 중요하다.

### 8. Observability와 support workflow

운영자는 다음을 즉시 봐야 한다.

- 어떤 tenant가 어떤 config layer를 쓰는가
- 어느 override가 최근 변경되었는가
- 어떤 scope가 freeze / quarantine / soak 상태인가
- scoped rollback 이후 rollback window가 얼마나 남았는가
- 어떤 agent가 아직 old/new config에 머물러 있는가
- support / CS 대응용 tenant timeline이 준비되었는가

tenant incident는 기술 복구와 고객 커뮤니케이션이 같이 가야 한다.
특히 enterprise tenant 상대라면 "언제 freeze했고, 언제 safe default로 전환했고, 언제 thaw했는가"가 바로 설명 가능해야 한다.

## 실전 시나리오

### 시나리오 1: enterprise tenant rate limit 오배포

문제:

- 특정 대형 tenant override 때문에 요청이 과도하게 차단된다

해결:

- tenant scope만 LKG로 롤백한다
- global policy는 유지한다
- tenant override를 freeze하고 일정 시간 soak 관찰한다
- support에는 영향 요청량과 복구 시점을 tenant timeline으로 제공한다

### 시나리오 2: tenant class entitlement leak

문제:

- 상위 요금제 tenant class 정책이 잘못 배포되어 일부 tenant에 기능이 과다 노출된다

해결:

- tenant class publish를 halt한다
- feature kill 또는 quarantine으로 추가 노출을 막는다
- impacted tenant 목록을 확정한 뒤 scoped correction을 내보낸다
- reversible soak 동안 audit log와 billing side effect를 같이 본다

### 시나리오 3: region+tenant route cutover mismatch

문제:

- 특정 region의 일부 tenant만 새 backend route를 탔는데 receiver warmup이 끝나지 않았다

해결:

- 해당 tenant scope write path만 짧게 freeze한다
- route override를 old safe route로 cutback한다
- reversible soak 동안 stale route miss와 latency를 본다
- soak 종료 전까지 bad override를 삭제하지 않는다

### 시나리오 4: partial propagation으로 old/new policy가 섞임

문제:

- 중앙 publish는 끝났지만 일부 agent가 여전히 old config를 유지해 tenant별 동작이 갈린다

해결:

- scope pin으로 추가 publish를 막는다
- affected consumer 집합을 추적한다
- scoped replay로 convergence를 맞춘다
- convergence 전까지 operator가 수동 thaw하지 못하게 gate를 둔다

## 코드로 보기

```pseudo
function recoverTenantScope(incident):
  scopes = scopeAnalyzer.affectedScopes(incident)
  for scope in scopes:
    if incident.requiresFreeze(scope):
      writer.freeze(scope, token=fenceToken(scope), timeout=5s)

    target = scopedLastKnownGood(scope) or safeDefault(scope)
    publisher.pin(scope, target)
    quarantine.mark(scope, incident.badOverrideVersion)
    soak.start(scope, duration=10m)

function finishSoak(scope):
  if guardrail.healthy(scope):
    writer.thaw(scope)
    cleanup.schedule(scope.badOverrideVersion)
  else:
    escalate(scope)
```

```java
public ScopedRecoveryPlan plan(ConfigIncident incident) {
    AffectedScopes scopes = scopeAnalyzer.analyze(incident.changedKeys(), scopeInventory.current());
    return recoveryPlanner.plan(scopes, rollbackEnvelopeRepository.current());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Global rollback | 단순하다 | 과잉 복구가 된다 | truly global issue |
| Tenant-scoped rollback | blast radius가 작다 | scope metadata가 필요하다 | 대부분의 override incident |
| Freeze only | 빠르다 | 근본 복구는 아니다 | incident 초동 대응 |
| Freeze + scoped rollback + soak | 안전하다 | 운영 상태가 늘어난다 | route, entitlement, billing 연동 config |
| Quarantine + safe default | 재발을 막기 쉽다 | 기능 축소가 생긴다 | LKG도 애매하거나 dependency가 불안정할 때 |

핵심은 tenant-scoped config incident recovery가 override 기능의 부가물이 아니라
**tenant별 blast radius를 줄이기 위해 rollback safety, write-freeze window, reversible cutover를 함께 운영하는 multi-tenant 복구 설계**라는 점이다.

## 꼬리질문

> Q: override가 잘못됐으면 그냥 전체 config를 rollback하면 안 되나요?
> 의도: scoped recovery 가치 이해 확인
> 핵심: 그렇게 하면 정상 tenant까지 불필요하게 영향받고, 이미 반영된 안전한 global fix도 함께 사라질 수 있다.

> Q: scoped last-known-good만 있으면 충분한가요?
> 의도: rollback safety envelope 이해 확인
> 핵심: 아니다. consumer version, dependency readiness, cleanup 여부까지 함께 알아야 실제로 되돌릴 수 있다.

> Q: config incident인데 왜 write-freeze가 필요하죠?
> 의도: config와 write path 결합 이해 확인
> 핵심: route, entitlement, partition reassignment처럼 write authority가 움직이는 config는 pure rollback만으로 race를 막을 수 없기 때문이다.

> Q: rollback 후 왜 바로 thaw하지 않나요?
> 의도: reversible soak 필요성 확인
> 핵심: rollback 직후에야 stale routing, hidden side effect, partial propagation 문제가 드러날 수 있어서 잠시 reversible 상태로 관찰해야 한다.

> Q: tenant incident에서 기술 복구 외에 무엇이 중요하나요?
> 의도: operator ergonomics 이해 확인
> 핵심: 영향 tenant 목록, freeze/soak timeline, 고객 커뮤니케이션 근거, audit trail이 함께 있어야 한다.

## 한 줄 정리

Tenant-scoped config incident recovery 설계는 특정 tenant나 tenant class에 한정된 config 사고를 global rollback 없이 scope-local하게 격리하고, 필요한 경우 tenant-scoped write-freeze와 reversible soak까지 포함해 복구하는 multi-tenant 운영 설계다.
