---
schema_version: 3
title: Kill Switch Fast-Fail Ops
concept_id: software-engineering/kill-switch-fast-fail
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- kill-switch
- fast-fail
- incident-response
- blast-radius
aliases:
- Kill Switch Fast-Fail Ops
- kill switch emergency stop
- operational fast fail guardrail
- side effect kill switch
- write kill switch
- 사고 확산 차단 스위치
symptoms:
- 결제, 알림, 외부 API, 데이터 쓰기 경로에서 문제가 번지는데 feature flag처럼 느슨한 제어만 있어 피해 확산을 즉시 멈추지 못해
- kill switch 상태를 장애 난 DB나 remote config에서만 읽어 정작 사고 때 스위치 자체가 동작하지 않아
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/feature-flag-dependency-management
- software-engineering/configuration-governance
next_docs:
- software-engineering/incident-review-learning-loop
- software-engineering/deployment-rollout-strategy
- spring/resilience4j-retry-circuit-breaker-bulkhead
linked_paths:
- contents/software-engineering/feature-flags-rollout-dependency-management.md
- contents/software-engineering/feature-flag-cleanup-expiration.md
- contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md
- contents/spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/configuration-governance-runtime-safety.md
- contents/software-engineering/incident-review-learning-loop-architecture.md
confusable_with:
- software-engineering/feature-flag-dependency-management
- spring/resilience4j-retry-circuit-breaker-bulkhead
- software-engineering/configuration-governance
forbidden_neighbors: []
expected_queries:
- kill switch와 feature flag와 circuit breaker는 각각 무엇이 다르고 언제 써야 해?
- 결제, 알림, 데이터 쓰기 사고에서 side-effect kill switch나 write kill switch를 어떻게 설계해?
- 원격 설정 서버나 DB가 죽어도 kill switch가 동작하려면 어떤 control plane과 cache가 필요해?
- kill switch를 켠 뒤 read-only degraded mode나 queueing fallback을 어떻게 설계해야 해?
- 누가 언제 왜 어떤 scope로 kill switch를 켰는지 audit trail이 필요한 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 feature flag보다 보수적인 운영용 kill switch를 traffic, side-effect, write, downstream scope로 나눠 fast-fail과 피해 확산 차단을 설계하는 advanced playbook이다.
---
# Kill Switch Fast-Fail Ops

> 한 줄 요약: Kill switch는 기능을 숨기는 플래그가 아니라, 장애가 번지기 전에 피해 범위를 강제로 끊는 운영용 최종 차단장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Feature Flag Cleanup and Expiration](./feature-flag-cleanup-expiration.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Resilience4j, Retry, Circuit Breaker, Bulkhead](../spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [API Design, Error Handling](./api-design-error-handling.md)
> - [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)

> retrieval-anchor-keywords:
> - kill switch
> - emergency stop
> - safe default
> - fast fail
> - operational guardrail
> - circuit breaker
> - feature freeze
> - blast radius

## 핵심 개념

Kill switch는 "기능을 껐다 켠다"는 수준의 일반 플래그가 아니다.
더 정확히는 **운영 중 발생한 위험을 즉시 멈추기 위한 하드 스톱 메커니즘**이다.

여기서 중요한 점은 멈추는 대상이 코드 경로가 아니라 **실제 피해의 확산**이라는 것이다.

- 잘못된 지급
- 대량 알림 발송
- 외부 API 연쇄 장애
- 잘못된 데이터 쓰기

Kill switch는 이런 상황에서 "계속 진행하면 더 나빠진다"는 판단을 시스템적으로 반영한다.

---

## 깊이 들어가기

### 1. kill switch는 feature flag보다 더 보수적이다

Feature flag는 보통 기능 노출을 제어한다.
Kill switch는 문제가 났을 때 **기본적으로 끄는 쪽**으로 설계한다.

차이점:

- feature flag: 새 기능 공개를 점진적으로 조절
- kill switch: 위험한 동작을 즉시 차단

즉 feature flag는 제품 운영에 가깝고, kill switch는 사고 대응에 가깝다.

### 2. kill switch는 외부 의존성에 기대면 안 된다

가장 위험한 패턴은 kill switch 판정 자체가 이미 장애 난 시스템에 의존하는 것이다.

예:

- 원격 설정 서버가 죽었는데 그 서버를 통해서만 스위치를 끌 수 있다
- DB가 장애인데 DB에서 kill switch 상태를 읽는다
- 메인 서비스가 죽었는데 그 서비스 안에서만 스위치를 조작한다

좋은 kill switch는 최소한의 경로로 동작해야 한다.

- 로컬 캐시
- 별도 운영 채널
- 저의존성 control plane
- 읽기 전용 안전 상태

즉 kill switch 자체도 configuration governance의 대상이다.

### 3. kill switch에는 대상이 여러 종류 있다

| 종류 | 끄는 것 | 예시 |
|---|---|---|
| traffic kill switch | 요청 유입 | 신규 endpoint 차단 |
| side-effect kill switch | 외부 동작 | 메일, 결제, 푸시 중지 |
| write kill switch | 데이터 변경 | 특정 테이블 업데이트 금지 |
| downstream kill switch | 연동 호출 | 장애난 외부 API 호출 중단 |

하나의 switch로 모든 문제를 푸는 것보다, **피해 유형별로 분리**하는 편이 안전하다.

### 4. kill switch는 fallback과 함께 설계해야 한다

단순히 "끄기"만 하면 서비스가 비어 버릴 수 있다.
그래서 보통 다음을 함께 둔다.

- read-only degraded mode
- 큐잉 후 지연 처리
- 안전한 기본값 반환
- 사용자에게 명시적 안내

예를 들어 추천 시스템이 죽으면 추천을 꺼도 되지만, 결제는 완전히 꺼 버리면 안 된다.

### 5. kill switch는 감사 가능해야 한다

누가, 언제, 왜, 어떤 범위로 껐는지 기록이 없으면 나중에 복구가 어렵다.

필요한 기록:

- operator identity
- change reason
- scope
- start/end time
- related incident id

kill switch는 결국 운영 판단이기 때문에, **판단의 흔적**이 남아야 한다.

---

## 실전 시나리오

### 시나리오 1: 이메일 폭주를 멈춘다

템플릿 버그 때문에 가입자에게 같은 메일이 수십만 건 나가기 시작했다.

대응:

1. 메일 발송 kill switch on
2. 큐 적재만 유지
3. 중복 제거 정책 확인
4. 수정 후 제한적으로 재개

### 시나리오 2: 결제 외부 연동이 오작동한다

외부 PG가 timeout과 재시도를 반복하면서 트래픽을 증폭시킨다.

여기서는 retry만 끄는 것이 아니라, 필요하면 **결제 시도 자체를 잠시 막고** 대체 안내를 보여줘야 한다.

### 시나리오 3: 잘못된 데이터 쓰기가 시작됐다

새 배포 후 특정 조건에서 잘못된 상태값이 저장된다.

이때 kill switch는:

- 쓰기 차단
- 손상 경로 격리
- 읽기만 허용
- 보정 배치 준비

순서로 사용된다.

---

## 코드로 보기

```java
public class KillSwitchGuard {
    private final KillSwitchRepository repository;

    public void ensureWritable(String scope) {
        if (repository.isDisabled(scope)) {
            throw new ServiceUnavailableException("writes disabled for " + scope);
        }
    }

    public boolean allowSideEffect(String action) {
        return !repository.isDisabled(action);
    }
}
```

핵심은 "켜짐/꺼짐"보다 **어떤 범위에 어떤 의미로 적용되는지**다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| feature flag | 유연하고 친숙하다 | 사고 대응 용도로는 느슨할 수 있다 | 일반 릴리스 제어 |
| kill switch | 빠르게 피해를 멈춘다 | 과도하면 서비스가 너무 쉽게 꺼진다 | 사고 확산 차단 |
| circuit breaker | 자동 반응이 가능하다 | 운영자의 의도가 즉시 반영되진 않는다 | 외부 호출 장애 완충 |

kill switch는 자동화보다 우선하는 경우가 있다.
특히 결제, 알림, 데이터 변경처럼 피해 비용이 큰 영역이 그렇다.

---

## 꼬리질문

- kill switch가 너무 쉽게 켜지면 서비스 가용성이 과도하게 떨어지지 않는가?
- 스위치의 범위는 기능 단위인가, 사용자군 단위인가, 연동 단위인가?
- 스위치를 끈 뒤 안전하게 복구하려면 어떤 degraded mode가 필요한가?
- 원격 설정이 죽어도 kill switch는 어떻게 살아남는가?

## 한 줄 정리

Kill switch는 배포를 편하게 만드는 장치가 아니라, 사고가 커지기 전에 시스템을 강제로 안전 상태로 돌리는 최종 방어선이다.
