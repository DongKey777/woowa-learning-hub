# Deprecation Enforcement, Tombstone, and Sunset Guardrails

> 한 줄 요약: deprecation이 공지로만 끝나면 종료는 계속 밀리므로, 신규 사용 차단, warning, allowlist, tombstone mode, final removal 같은 enforcement ladder를 자동화된 guardrail로 운영해야 실제 sunset이 닫힌다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Deprecation Communication Playbook](./deprecation-communication-playbook.md)
> - [API Lifecycle Stage Model](./api-lifecycle-stage-model.md)
> - [Contract Registry Governance](./contract-registry-governance.md)
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)
> - [Tombstone Response Template and Consumer Guidance](./tombstone-response-template-and-consumer-guidance.md)
> - [Consumer Exception Operating Model](./consumer-exception-operating-model.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)

> retrieval-anchor-keywords:
> - deprecation enforcement
> - tombstone mode
> - sunset guardrail
> - new consumer block
> - removal enforcement
> - deprecation header
> - allowlist shutdown
> - sunset automation
> - retire vs absorb
> - sunset allowlist absorb
> - dm waiver retire
> - deprecation bypass cleanup

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Deprecation Enforcement, Tombstone, and Sunset Guardrails](./README.md#deprecation-enforcement-tombstone-and-sunset-guardrails)
> - 다음 단계: [Tombstone Response Template and Consumer Guidance](./tombstone-response-template-and-consumer-guidance.md)

## 핵심 개념

deprecation communication만 잘해도 혼란은 줄일 수 있다.
하지만 communication만으로는 실제 종료가 잘 안 된다.

그래서 deprecation lifecycle에는 보통 enforcement ladder가 필요하다.

예:

- 신규 사용 차단
- warning / header / banner
- 특정 consumer allowlist만 허용
- tombstone mode
- final removal

즉 sunset governance는 일정 관리가 아니라 **점진적 차단 정책**이다.

---

## 깊이 들어가기

### 1. 신규 유입 차단이 가장 먼저 와야 한다

deprecated 상태에서 가장 먼저 막아야 할 것은 old path의 신규 consumer다.
새로 들어오는 소비자를 허용하면 sunset window는 계속 늘어난다.

좋은 guardrail:

- registry stage가 deprecated면 신규 등록 실패
- template / gateway / lint 단계에서 old endpoint 사용 금지
- support 팀이 old contract 신규 사용 요청을 반려

### 2. warning과 block은 분리된 단계여야 한다

곧바로 hard block을 걸면 migration 충격이 크다.
반대로 warning만 오래 유지하면 아무도 안 움직인다.

보통 단계:

1. notice only
2. warning with deadline
3. new consumer block
4. allowlist only
5. tombstone
6. removal

### 3. tombstone mode는 종료 전 마지막 안전장치다

tombstone은 그냥 404를 주는 것이 아니다.
보통 다음을 포함한다.

- deprecated reason
- replacement path
- support channel
- traceable error code

즉 tombstone은 소비자에게 "왜 실패했는지와 어디로 가야 하는지"를 알려 주는 **제어된 종료 상태**다.

### 4. enforcement는 observability와 함께 가야 한다

차단을 걸기 전에 최소한 다음이 보여야 한다.

- who is still calling
- last access time
- request volume by consumer
- warning exposure count
- allowlist scope

관측 없이 enforcement를 걸면 sunset이 아니라 blind shutdown이 된다.

### 5. waiver와 tombstone은 같이 설계해야 한다

일부 consumer는 final removal 직전까지 waiver가 필요할 수 있다.
그래서 enforcement ladder에는 waiver path도 포함돼야 한다.

예:

- global block
- explicit allowlist consumer만 temporary pass
- waiver expiry가 지나면 tombstone 전환

즉 deprecation governance는 soft communication, hard guardrail, limited waiver가 함께 있는 구조다.

### 6. sunset 예외 경로는 retire할지 absorb할지 같은 언어로 판정해야 한다

sunset 운영에서 반복되는 예외 경로가 보이면, 모두 productize할 것도 아니고 모두 폐기할 것도 아니다.
먼저 그 경로가 **bypass인지 capability gap인지**를 구분해야 한다.

- 이미 waiver registry와 review cadence가 있는데 연장 승인만 slack DM이나 개인 메모에서 처리된다면: 그 경로는 **retire** 대상이다
- 서비스별 allowlist scope, tombstone override reason, consumer-specific cut date를 매번 같은 구조로 관리하지만 공식 guardrail이 그 필드를 못 담는다면: 그 데이터 경로는 **absorb** 대상이다

즉 질문은 두 개다.

- 공식 경로가 이미 있는데 사람들이 우회하는가 -> retire
- 반복되는 structured sunset data가 control plane에 못 들어가고 있는가 -> absorb

이렇게 써 두면 [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md), [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md), [Consumer Exception Operating Model](./consumer-exception-operating-model.md)이 같은 decision language를 공유하게 된다.
보다 일반화된 판정 기준은 [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)처럼 문서화해 두는 편이 stable하다.

---

## 실전 시나리오

### 시나리오 1: 구 API를 계속 새 팀이 쓰기 시작한다

이 경우 문제는 communication 부족이 아니라 new consumer block이 없다는 것이다.

### 시나리오 2: sunset date가 왔지만 일부 consumer가 남아 있다

전체 제거 대신 allowlist-only tombstone으로 들어가고, 남은 consumer만 좁혀 관리하는 편이 낫다.

### 시나리오 3: removal 후 왜 실패했는지 문의가 폭주한다

plain 404 대신 tombstone response와 traceable code가 있었다면 support 비용을 줄일 수 있다.

---

## 코드로 보기

```yaml
sunset_guardrail:
  api: legacy-order-detail-v1
  stage: sunset
  enforce:
    block_new_consumers: true
    warning_header: true
    allowlist_only_after: 2026-09-01
    tombstone_after: 2026-10-01
```

좋은 sunset guardrail은 공지와 차단과 예외를 하나의 ladder로 묶는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| communication only | 부드럽다 | 종료가 잘 안 된다 | 영향이 매우 작을 때 |
| immediate hard block | 깔끔하다 | 충격이 크다 | external impact가 거의 없을 때 |
| staged enforcement ladder | 현실적이다 | 운영 체계가 필요하다 | 일반적인 sunset |

deprecation enforcement의 목적은 빨리 끊는 것이 아니라, **종료를 계속 미루는 조직 습관을 guardrail로 바로잡는 것**이다.

---

## 꼬리질문

- deprecated 상태에서 신규 소비자 유입은 정말 막혀 있는가?
- warning과 block 사이의 단계가 정의돼 있는가?
- tombstone response가 replacement와 support 정보를 제공하는가?
- waiver와 allowlist가 sunset 종료를 방해하지 않도록 관리되는가?
- 남은 sunset exception path는 bypass라서 retire해야 하는가, capability gap이라서 absorb해야 하는가?

## 한 줄 정리

Deprecation enforcement, tombstone, and sunset guardrails는 종료를 공지에서 실제 차단으로 연결해, deprecation이 endless warning 상태로 남지 않게 만드는 운영 장치다.
