# Anti-Corruption Rollout and Provider Sandbox Pattern

> 한 줄 요약: ACL 변경은 코드 배포가 아니라 계약 변경 rollout에 가깝기 때문에, provider sandbox 한계 인식, contract-test gate, shadow/canary, fallback governance를 함께 설계해야 안전하다.

**난이도: 🔴 Expert**

> related-docs:
> - [Anti-Corruption Layer Operational Pattern](./anti-corruption-layer-operational-pattern.md)
> - [Anti-Corruption Contract Test Pattern](./anti-corruption-contract-test-pattern.md)
> - [Anti-Corruption Translation Map Pattern](./anti-corruption-translation-map-pattern.md)
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)

retrieval-anchor-keywords: acl rollout governance, provider sandbox parity, contract test gate, shadow translation diff, integration canary policy, fallback governance, rollback switch, quarantine decision matrix, external provider drift, sandbox production gap

---

## 핵심 개념

ACL 변경은 merge보다 **운영 의미**가 더 크다.

- mapping table 변경
- provider version 전환
- translator/facade 교체
- sandbox와 production 간 행동 차이
- fallback 정책 변경

겉보기에는 작은 코드 diff여도 실제로는 다음이 바뀐다.

- 어떤 외부 계약을 신뢰하는지
- 어디까지 tolerant하게 받아들이는지
- 이상 징후가 나면 누구 권한으로 어디까지 되돌릴지

그래서 ACL rollout은 단순 배포가 아니라 **계약 가설을 단계적으로 검증하는 governance 패턴**으로 봐야 한다.

- sandbox verification
- fixture regression / contract test
- shadow or dual translation
- staged canary
- rollback / degrade / quarantine policy

### Retrieval Anchors

- `acl rollout governance`
- `provider sandbox parity gap`
- `contract test gate`
- `shadow translation diff`
- `integration canary threshold`
- `fallback governance`
- `translator rollback switch`
- `quarantine decision matrix`

---

## 깊이 들어가기

### 1. rollout 단위는 deploy artifact가 아니라 translation contract다

ACL에서 위험한 건 JAR 하나가 아니라 "외부 입력을 어떤 의미로 해석하느냐"다.

- enum/status mapping 변경
- optional field 허용 범위 변경
- missing-required 처리 방식 변경
- degraded result 기준 변경

즉 ACL rollout은 새 코드 배포보다 "해석 규칙의 교체"에 가깝다.  
그래서 변경 단위마다 stage, gate, owner를 가져야 한다.

### 2. provider sandbox는 필요하지만 truth source가 아니다

provider sandbox는 preflight로는 유용하다.  
하지만 production parity를 보장하지는 않는다.

- sample payload만 제공
- 일부 enum/value가 빠짐
- latency, timeout, rate-limit 패턴이 다름
- async callback 순서나 재전송 정책이 다름
- 테스트 계정만 허용되어 tenant 다양성이 없음

즉 sandbox의 역할은 "연결과 기본 shape가 살아 있는지"를 보는 것이지, 실제 운영 의미를 증명하는 게 아니다.

### 3. sandbox는 환경이 아니라 capability matrix로 관리하는 편이 낫다

"sandbox를 통과했다"는 말만으로는 정보가 부족하다.  
최소한 다음 질문에 답할 수 있어야 한다.

| 차원 | sandbox가 줄 수 있는 신호 | production과 다른 흔한 지점 | 필요한 guardrail |
|---|---|---|---|
| 인증/서명 | credential, request signing smoke | 실계정 권한/tenant 조합 부재 | 별도 prod shadow 또는 제한적 canary |
| payload shape | happy-path 응답 확인 | rare enum, optional field, partial payload 미노출 | fixture corpus + prod sample 회귀 |
| 실패 모델 | 일부 error code 재현 | timeout, burst failure, rate-limit 의미 차이 | transport alert 분리, sampled prod compare |
| async callback | 기본 webhook 흐름 확인 | 순서 역전, 중복 전송, 지연 재시도 차이 | idempotency + replay test |
| 운영 부하 | 기본 round-trip 확인 | 실부하 latency, throttling 차이 | canary budget, fast rollback |

이렇게 capability matrix로 관리하면 sandbox를 과신하지 않고, 어떤 공백을 다른 단계가 메워야 하는지 선명해진다.

### 4. contract test는 rollout 앞뒤를 고정하는 gate다

fixture regression과 sandbox verification은 역할이 다르다.

- fixture contract test: deterministic regression
- sandbox smoke: live integration connectivity
- shadow diff: real payload 의미 비교
- canary metrics: 실제 사용자 영향 감시

여기서 contract test는 시작 전에만 돌리는 게 아니라, **rollout 전체의 입구와 출구를 고정하는 기준선** 역할을 한다.

- rollout 전: translator/facade 기대 semantics 고정
- shadow 중: diff가 나면 fixture로 환원할 수 있게 증거 수집
- incident 후: 실제 drift payload를 회귀 fixture로 편입

즉 contract test는 ACL governance의 감사 로그 역할도 겸한다.

### 5. shadow translation은 JSON diff보다 semantic diff가 중요하다

새 translator를 바로 primary로 쓰지 않고, old/new 결과를 나란히 계산해 diff만 기록하면 실제 payload 다양성을 안전하게 관찰할 수 있다.

이때 비교 포인트는 raw JSON equality보다 다음이 더 중요하다.

- 내부 enum/status가 같은가
- 필수 invariant가 보존되는가
- degraded/quarantine 분기 결과가 같은가
- downstream command/event shape가 같은가

즉 shadow는 "출력 바이트가 같은가"보다 "도메인 의미가 같은가"를 보는 단계다.

### 6. canary는 percentage보다 blast radius 경계가 먼저다

ACL canary는 단순히 1%, 5%, 10%만 올리는 문제가 아니다.  
무엇을 묶어서 제한할지가 더 중요하다.

- 특정 provider tenant만 포함할지
- 특정 endpoint 또는 operation만 열지
- webhook callback path는 제외할지
- read-only translation만 먼저 열지

외부 provider 연동은 오류가 생기면 재시도와 중복 부작용이 함께 따라오므로, canary 경계는 트래픽 비율보다 **피해면적 제어** 관점으로 잡는 편이 안전하다.

### 7. fallback governance는 rollback, degrade, quarantine를 분리해야 한다

문제가 생겼을 때 "fallback한다"는 표현만으로는 부족하다.  
적어도 네 가지를 구분해야 한다.

| 상황 | 대표 신호 | 기본 대응 | 왜 분리해야 하는가 |
|---|---|---|---|
| translator regression | shadow/canary semantic diff 증가 | 이전 translator로 rollback | 코드/매핑 문제면 경로 자체를 되돌려야 한다 |
| provider transport 장애 | timeout, 5xx, rate-limit | retry or circuit open | 계약 drift와 transport failure를 섞으면 대응이 틀어진다 |
| unknown enum/optional drift | unknown mapping rate 증가 | degraded result + metric | 무조건 실패보다 제한적 허용이 나을 수 있다 |
| missing-required/semantic anomaly | 필수 필드 누락, 금액 의미 불일치 | quarantine | 재시도보다 격리가 안전하다 |

즉 fallback governance의 핵심은 "무엇을 old path로 되돌리고, 무엇을 degraded로 허용하고, 무엇을 격리하는가"를 미리 분기하는 것이다.

### 8. stage마다 exit criteria와 owner가 있어야 감으로 운영하지 않는다

다음처럼 단계별 질문이 고정돼야 한다.

| Stage | 확인할 것 | 최소 gate | owner 질문 |
|---|---|---|---|
| Contract baseline | fixture suite, mapping diff | 핵심 fixture 100% 통과 | 새 해석 규칙이 문서화됐는가 |
| Sandbox smoke | auth, request signing, happy path | sandbox 호출 성공 | 연결 자체는 살아 있는가 |
| Shadow | old/new semantic diff | diff rate, unknown rate threshold 이내 | prod payload에서 의미 차이가 없는가 |
| Canary | 제한된 실제 트래픽 | alert/fallback rate 안정 | blast radius 안에서 운영 가능한가 |
| Primary + rollback window | 전체 전환 후 관찰 | rollback window 동안 이상 없음 | old path 제거 시점이 정당한가 |

이 표가 없으면 rollout이 "분위기상 괜찮아 보여서" 진행된다.

### 9. rollback window는 old translator를 지우지 않는 기간이다

full rollout 직후 old path를 제거하면, 이상 징후가 나와도 즉시 되돌리기 어렵다.

- old translator binary 또는 mapping snapshot 보관
- old path metric 이름 유지
- config 기반 route switch 유지
- rollback 권한자와 기준 문서화

이 기간이 있어야 canary 이후 늦게 드러나는 semantic drift도 빠르게 통제할 수 있다.

### 10. incident가 끝나면 governance 자산이 늘어나야 한다

좋은 ACL 팀은 incident를 "일단 복구"로 끝내지 않는다.

- prod raw payload redaction
- regression fixture 등록
- missing-required / degraded / quarantine 기준 보정
- sandbox parity matrix 갱신
- rollback 기준 재조정

즉 운영에서 배운 사실이 다음 rollout의 guardrail로 누적돼야 한다.

---

## 운영 체크리스트

### rollout 전에 고정할 질문

1. 이번 변경은 새 provider, 새 mapping, 새 translator 중 무엇을 바꾸는가
2. sandbox가 검증하지 못하는 production gap은 무엇인가
3. 어떤 fixture가 이번 변경의 semantic baseline인가
4. shadow에서 어떤 diff를 equivalent로 보고 어떤 diff를 blocking으로 볼 것인가
5. canary blast radius는 tenant, endpoint, operation 중 어디로 제한할 것인가
6. fallback은 rollback, degrade, quarantine 중 무엇이 기본인가
7. old path를 얼마나 오래 유지할 것인가

### rollout 중 관측 포인트

- unknown mapping rate
- semantic diff rate
- degraded response rate
- quarantine enqueue count
- provider timeout / 5xx / throttling rate
- tenant 또는 operation별 canary error skew

### rollout 종료 후 남겨야 할 것

- 실제 diff 사례와 해석
- 추가된 regression fixture
- sandbox parity gap 메모
- rollback window 종료 근거

---

## 실전 시나리오

### 시나리오 1: PG API v2 전환

sandbox smoke로 auth/signature를 확인한 뒤, production shadow translation으로 old/new 결과 diff를 쌓는다.  
canary는 특정 가맹점 그룹만 열고, semantic diff가 임계치를 넘으면 즉시 이전 translator로 rollback한다.

### 시나리오 2: 물류 provider 교체

새 provider adapter는 fixture와 sandbox를 통과해도 callback 순서와 지연 재전송이 production과 다를 수 있다.  
그래서 webhook path는 늦게 열고, missing-required payload는 retry 대신 quarantine로 보낸다.

### 시나리오 3: mapping table 변경

코드 diff는 작아 보여도 status 의미가 달라질 수 있다.  
shadow diff와 unknown mapping rate를 gate로 두고, old mapping snapshot을 config switch로 즉시 복구할 수 있게 둔다.

### 시나리오 4: provider sandbox가 지나치게 깨끗한 경우

sandbox에서는 항상 정상 payload만 오지만 production에서는 rare enum이 나온다.  
이 경우 sandbox 통과를 "연결 확인"으로만 해석하고, 실제 rollout 판단은 fixture corpus와 prod shadow evidence에 더 크게 둬야 한다.

---

## 코드로 보기

### rollout stage와 gate

```java
public enum TranslationRolloutStage {
    CONTRACT_BASELINE,
    SANDBOX_SMOKE,
    SHADOW,
    CANARY,
    PRIMARY,
    ROLLBACK
}
```

```java
public record TranslationRolloutGate(
    TranslationRolloutStage stage,
    double maxSemanticDiffRate,
    double maxUnknownMappingRate,
    double maxDegradedRate,
    boolean rollbackWindowOpen
) {}
```

### fallback decision 분기

```java
public sealed interface TranslationFallbackAction
    permits RollbackToPreviousTranslator, ReturnDegradedResult, QuarantinePayload, BlockProviderRoute {}

public record RollbackToPreviousTranslator(String translatorVersion)
    implements TranslationFallbackAction {}

public record ReturnDegradedResult(String reason)
    implements TranslationFallbackAction {}

public record QuarantinePayload(String reason)
    implements TranslationFallbackAction {}

public record BlockProviderRoute(String providerRoute)
    implements TranslationFallbackAction {}
```

```java
// shadow 경로에서는 old/new translator를 모두 계산하되
// semantic diff만 기록하고 primary 결과는 기존 translator에서 유지한다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 rollout | 빠르다 | semantic mismatch blast radius가 크다 | 매우 작은 내부 연동 |
| sandbox + fixture + shadow + canary | 안전하다 | 운영 단계와 자료 관리 비용이 든다 | 외부 provider 핵심 연동 |
| sandbox만 의존 | smoke는 빠르다 | production parity gap을 놓치기 쉽다 | 보조 신호로만 사용 |
| rollback/degrade/quarantine 구분 | incident 대응이 명확하다 | 정책 문서화와 운영 훈련이 필요하다 | drift 가능성이 큰 연동 |

판단 기준은 다음과 같다.

- sandbox와 production parity gap을 전제로 설계한다
- contract test를 rollout 전후의 기준선으로 사용한다
- shadow translation diff는 semantic 의미 기준으로 본다
- fallback은 rollback, degrade, quarantine를 분리한다

---

## 꼬리질문

> Q: sandbox가 있으면 production shadow는 필요 없나요?
> 의도: sandbox와 production parity gap을 이해하는지 본다.
> 핵심: 보통 필요하다. sandbox는 연결 확인에 가깝고, 실제 payload 다양성 검증은 shadow가 더 강하다.

> Q: mapping table 변경도 rollout이 필요한가요?
> 의도: 작은 변경이 semantic blast radius를 가질 수 있음을 아는지 본다.
> 핵심: 그렇다. enum/status mapping은 내부 의미를 바꾸므로 staged rollout과 rollback snapshot이 유용하다.

> Q: contract test와 sandbox smoke 중 무엇이 더 중요한가요?
> 의도: deterministic baseline과 live smoke를 구분하는지 본다.
> 핵심: 둘 다 필요하지만 역할이 다르다. contract test는 의미 기준선, sandbox는 연결 검증이다.

> Q: fallback 하나로 추상화하면 안 되나요?
> 의도: rollback/degrade/quarantine의 운영 차이를 이해하는지 본다.
> 핵심: 안 된다. 원인과 blast radius가 달라 대응 경로도 분리해야 한다.

## 한 줄 정리

ACL rollout은 sandbox smoke만 통과했다고 끝나는 작업이 아니라, contract-test baseline, prod shadow/canary, rollback window, fallback governance까지 묶어서 외부 계약 drift를 통제하는 운영 패턴이다.
