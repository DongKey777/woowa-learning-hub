# Deploy Rollback Safety / Compatibility Envelope 설계

> 한 줄 요약: deploy rollback safety와 compatibility envelope 설계는 코드, 스키마, config, traffic policy가 서로 어느 범위까지 호환되는지 명시해, 배포 후 이상 시 빠르게 되돌릴 수 있는 안전한 변경 경계를 만드는 운영 설계다.

retrieval-anchor-keywords: deploy rollback safety, compatibility envelope, backward compatibility, forward compatibility, rollback boundary, release freeze, config compatibility, artifact rollback, safe deploy, rollback matrix, point of no return, protocol version skew, write freeze rollback, mixed version window, reversible cutover, receiver warmup

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)
> - [Failure Injection / Resilience Validation Platform 설계](./failure-injection-resilience-validation-platform-design.md)
> - [Config Rollback Safety 설계](./config-rollback-safety-design.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)
> - [Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)

## 핵심 개념

배포에서 "rollback 가능하다"는 말은 자주 과장된다.
실제로는 다음이 모두 호환되어야 한다.

- 새 바이너리와 옛 바이너리
- 새 스키마와 옛 스키마
- 새 config와 옛 바이너리
- 새 traffic policy와 옛 backend

즉, rollback safety는 버튼 하나가 아니라 **어디까지 되돌릴 수 있는지의 compatibility envelope를 미리 설계하는 문제**다.

## 깊이 들어가기

### 1. 왜 rollback이 생각보다 어려운가

배포 직후 되돌리면 끝날 것 같지만, 실제로는 다음이 이미 바뀌어 있을 수 있다.

- destructive schema change
- new-only data writes
- config shape 변경
- external protocol 변경
- background migration 진행

즉, "코드만 되돌리면 된다"는 경우는 생각보다 적다.

### 2. Capacity Estimation

예:

- 하루 배포 50회
- 점진 배포 단계 4개
- 배포 후 관찰 창 30분
- rollback 목표 5분

이때 봐야 할 숫자:

- rollback detection latency
- config convergence time
- schema cleanup delay
- incompatible write volume
- rollback success rate

rollback safety는 실패 후 복구 속도뿐 아니라, 관찰 창 동안 얼마나 위험한 변경이 쌓이는지도 중요하다.

### 3. Compatibility envelope

보통 다음 축으로 본다.

- binary ↔ binary
- binary ↔ schema
- binary ↔ config
- binary ↔ protocol
- traffic policy ↔ dependency readiness

좋은 배포 설계는 각 축마다 다음을 적는다.

- backward compatible인가
- forward compatible인가
- mixed-version window가 허용되는가
- cleanup 전 rollback 가능한가

### 4. Release sequencing

안전한 배포는 보통 이 순서를 지킨다.

1. additive schema/config 준비
2. compatible binary 배포
3. dark launch / shadow / canary
4. behavior switch
5. cleanup and contract

이 순서를 어기면 rollback이 막히는 경우가 많다.

### 5. Rollback boundary와 point of no return

실전에서는 "되돌릴 수 있는 시점"과 "이제 correction이 필요한 시점"을 구분해야 한다.

대표 boundary:

- old binary가 new data를 아직 읽을 수 있음
- old config가 still valid
- old protocol consumer가 아직 살아 있음
- cleanup이 아직 실행되지 않음

이 경계를 넘으면 rollback보다 forward-fix가 더 현실적일 수 있다.

### 6. Kill switch와 freeze

rollback safety는 꼭 full binary rollback만 뜻하지 않는다.

대표 안전장치:

- feature kill switch
- traffic weight 0%
- config freeze
- write authority freeze
- cleanup job pause

즉, 작은 스위치로 먼저 출혈을 멈추고, 그다음 큰 rollback을 판단하는 편이 좋다.

### 7. Rollback observability

운영자는 즉시 알아야 한다.

- 지금 rollback 가능한가
- 어떤 축이 호환성을 깨고 있는가
- 이미 new-only write가 얼마나 쌓였는가
- cleanup / migration job이 어디까지 진행됐는가
- full rollback 대신 partial disable이 가능한가

이 정보가 없으면 rollback 논의가 감으로 흐른다.

## 실전 시나리오

### 시나리오 1: additive schema + new binary 배포

문제:

- 새 컬럼을 쓰는 바이너리를 배포했지만 오류율이 올라간다

해결:

- old binary가 새 컬럼을 무시할 수 있는지 확인한다
- cleanup 전이면 binary rollback을 허용한다
- 새 컬럼은 남겨 두고 나중에 다시 사용한다

### 시나리오 2: config shape 변경

문제:

- 새 config key 구조를 old binary가 이해하지 못한다

해결:

- config는 additive로 먼저 배포한다
- old/new가 모두 읽을 수 있는 envelope를 만든다
- rollout 중 incompatible key removal은 금지한다

### 시나리오 3: write authority cutover 직후 이상 발견

문제:

- new writer가 일부 요청을 잘못 처리한다

해결:

- kill switch로 write exposure를 즉시 줄인다
- authority rollback boundary 안이면 old writer로 되돌린다
- boundary 밖이면 correction + replay + partial disable로 전환한다

## 코드로 보기

```pseudo
function canRollback(release):
  return schema.compatibleWith(release.previousVersion) &&
         config.compatibleWith(release.previousVersion) &&
         !cleanupPassedPointOfNoReturn() &&
         !newOnlyWritesExceededThreshold()

function handleIncident(release):
  activateKillSwitch(release)
  if canRollback(release):
    rollbackBinaryAndTraffic(release)
  else:
    freezeFurtherChanges()
    startForwardFixPlan()
```

```java
public RollbackDecision decide(Release release) {
    CompatibilityReport report = compatibilityService.evaluate(release);
    return rollbackPolicy.decide(report);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Big-bang deploy | 빠르다 | rollback risk가 크다 | 작은 내부 시스템 |
| Compatibility-first release | 안전하다 | 배포 절차가 길어진다 | 대부분의 실서비스 |
| Binary rollback only | 단순하다 | schema/config incompatibility를 놓친다 | 아주 제한적 |
| Kill switch first | 출혈을 빨리 막는다 | 근본 원인은 남는다 | incident 초기 대응 |
| Forward fix after boundary | 현실적이다 | correction 비용이 든다 | point of no return 이후 |

핵심은 deploy rollback safety가 배포 도구 기능이 아니라 **코드, 스키마, config, traffic policy 사이의 호환 범위를 설계해 되돌릴 수 있는 변경 경계를 만드는 운영 설계**라는 점이다.

## 꼬리질문

> Q: canary가 있으니 rollback safety는 자동으로 해결되나요?
> 의도: 탐지와 되돌리기 차이 이해 확인
> 핵심: 아니다. canary는 문제를 빨리 찾게 도와주지만, 실제 rollback 가능 여부는 schema/config/data compatibility에 달려 있다.

> Q: additive schema면 항상 안전한가요?
> 의도: additive change의 한계 이해 확인
> 핵심: 대체로 안전하지만 config shape, protocol, new-only data semantics가 같이 바뀌면 여전히 rollback이 어려울 수 있다.

> Q: kill switch와 full rollback은 어떻게 다른가요?
> 의도: layered mitigation 이해 확인
> 핵심: kill switch는 빠르게 노출을 줄이는 응급조치이고, full rollback은 버전이나 경로 자체를 이전 상태로 되돌리는 큰 조치다.

> Q: point of no return은 어떻게 정하나요?
> 의도: rollback boundary 개념 확인
> 핵심: old path가 더 이상 new state를 해석하지 못하거나, cleanup / destructive migration이 진행된 시점을 기준으로 잡는 편이 많다.

## 한 줄 정리

Deploy rollback safety / compatibility envelope 설계는 코드, 스키마, config, traffic policy의 호환 경계를 미리 정의해 배포 후 이상 시 실제로 되돌릴 수 있는 운영 안전지대를 만드는 설계다.
