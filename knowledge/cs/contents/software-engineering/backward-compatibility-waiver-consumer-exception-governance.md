# Backward Compatibility Waivers and Consumer Exception Governance

> 한 줄 요약: backward compatibility gate가 있어도 현실에서는 lagging consumer와 temporary waiver가 생기므로, 어떤 예외를 얼마 동안 허용하고 어떤 compensating control과 removal 조건을 붙일지까지 관리하는 governance가 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Backward Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Contract Drift Detection and Rollout Governance](./contract-drift-detection-rollout-governance.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)
> - [Consumer Exception Operating Model](./consumer-exception-operating-model.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)

> retrieval-anchor-keywords:
> - backward compatibility waiver
> - compatibility exception
> - consumer exception
> - lagging consumer
> - waiver debt
> - supported version window
> - compatibility override
> - removal block
> - waiver retire vs absorb
> - dm waiver retire
> - compatibility allowlist absorb
> - exception capability gap

## 핵심 개념

호환성 governance는 "깨지면 안 된다"로 끝나지 않는다.
실제 운영에서는 일부 consumer가 늦게 따라오고, 그 때문에 producer가 temporary compatibility waiver를 허용해야 하는 순간이 생긴다.

문제는 waiver를 아무 기준 없이 허용하면:

- removal이 계속 미뤄지고
- support window가 무한정 늘어나고
- compatibility debt가 producer에 누적된다는 점이다

즉 backward compatibility governance는 gate뿐 아니라 **waiver lifecycle**도 포함해야 한다.

---

## 깊이 들어가기

### 1. waiver는 permanent support와 구분해야 한다

temporary waiver는 예외적이며 종료가 예정된 상태다.
permanent support는 정책적으로 계속 유지하기로 한 상태다.

이 둘이 섞이면 producer는 "잠깐만 유지"하던 코드를 수년간 끌고 가게 된다.

### 2. waiver에는 반드시 expiry와 owner가 있어야 한다

좋은 waiver 요소:

- 어떤 consumer를 위해 허용하는가
- 어떤 contract/version/field를 유지하는가
- 만료일은 언제인가
- 누가 migration을 완료해야 하는가
- producer가 감수하는 추가 비용은 무엇인가

waiver는 친절이 아니라 **time-boxed debt contract**다.

### 3. compensating control이 없으면 waiver는 hidden risk가 된다

호환성 예외를 허용하는 동안 최소한 다음이 필요할 수 있다.

- 특정 consumer allowlist
- old path 사용량 계측
- removal 전 final compatibility replay
- rollout 비율 제한
- dedicated support channel

waiver는 gate를 우회하는 것이 아니라, **더 강한 관측과 제한**을 붙여야 한다.

### 4. long-tail consumer 때문에 전체 evolution이 멈추면 안 된다

가장 어려운 상황은 소수 consumer가 전환을 계속 미루는 경우다.
이때 governance는 다음 중 하나를 선택해야 한다.

- waiver 연장
- removal 강행
- compatibility shim 제공
- migration sponsor escalation

즉 consumer exception은 개별 팀 사정이 아니라 **portfolio-level progress blocker**로 봐야 할 때가 있다.

### 5. repeated waiver handling은 retire와 absorb를 구분해야 한다

waiver governance가 성숙하지 않으면 공식 registry 옆에 작은 side path가 계속 생긴다.
이때 중요한 것은 "자동화할까 말까"가 아니라, 그 경로가 **없애야 할 bypass인지 흡수해야 할 capability gap인지** 구분하는 것이다.

- waiver request와 승인 경로가 이미 있는데 slack DM, 이메일, 팀 개인 문서가 승인을 대신한다면: 그 경로는 **retire** 대상이다
- 여러 waiver가 같은 structured field를 바깥에서 반복 관리한다면: 그 필드와 전이는 **absorb** 대상이다

예를 들어 `supported_version_window`, `consumer_tier`, `producer_flag_name`, `allowlist_scope`를 매번 시트에 적고 registry에는 못 넣는다면, 그것은 친절한 메모가 아니라 official exception tooling의 schema gap이다.
반대로 연장 승인만 비공식 채널에서 처리된다면, 새 도구를 더 만들기보다 [Consumer Exception Operating Model](./consumer-exception-operating-model.md)과 [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)의 공식 경로로 복귀시키는 쪽이 맞다.

즉 질문은 같다.

- 공식 경로가 이미 있는데 사람들이 우회하는가 -> retire
- 반복되는 structured waiver data가 공식 registry/control plane에 못 들어가고 있는가 -> absorb

이 언어를 [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)와 맞추면, compatibility waiver, deprecation extension, consumer exception review가 서로 다른 용어로 같은 부채를 다루지 않게 된다.

### 6. waiver debt는 deprecation과 removal policy로 회수해야 한다

waiver가 쌓이면 producer는 여러 버전과 fallback을 동시에 유지한다.
결국 deprecation/sunset 정책과 연결해 회수해야 한다.

필요한 질문:

- waiver가 removal block으로 자동 연결되는가
- 지원 종료일이 catalog/registry에 반영되는가
- repeated waiver consumer를 별도로 관리하는가

---

## 실전 시나리오

### 시나리오 1: 한 consumer가 strict parser를 못 고친다

모든 consumer를 기다릴 수 없다면, 해당 consumer만 old payload를 받게 하는 scoped waiver를 두고 expiry를 붙여야 한다.

### 시나리오 2: mobile 앱 배포 주기가 느리다

새 enum emission을 바로 켜지 못한다면 producer는 emission flag를 유지하되, app rollout timeline과 final cut date를 같이 잡아야 한다.

### 시나리오 3: removal이 매번 마지막 순간에 미뤄진다

이 경우 팀의 성실성 문제가 아니라 waiver governance가 없어서 removal block이 관리되지 않는 상태일 수 있다.

---

## 코드로 보기

```yaml
compatibility_waiver:
  consumer: mobile-app-v5
  contract: order-status-v4
  exception:
    keep_old_enum_set: true
  expires_at: 2026-10-01
  compensating_controls:
    - old_path_usage_metric
    - producer_emission_flag
  removal_block: true
```

좋은 waiver 기록은 이유와 종료 조건과 관측 지표를 같이 가진다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| waiver 금지 | 정책이 단순하다 | 현실을 못 담는다 | 매우 강한 통제 환경 |
| ad-hoc waiver | 당장은 빠르다 | debt가 숨는다 | 피해야 한다 |
| governed waiver | 현실적이다 | 운영 discipline이 필요하다 | 여러 consumer가 있는 시스템 |

compatibility waiver governance의 목적은 예외를 쉽게 만드는 것이 아니라, **예외가 구조적 부채로 굳지 않게 종료 조건과 비용을 보이게 만드는 것**이다.

---

## 꼬리질문

- 이 waiver는 temporary인가, 사실상 permanent support인가?
- waiver의 종료 책임은 consumer에게 있는가, producer에게 있는가?
- waiver가 removal block과 support 비용으로 어떻게 연결되는가?
- repeated waiver consumer를 portfolio 차원에서 보고 있는가?
- 남은 waiver side path는 retire 대상 bypass인가, absorb 대상 capability gap인가?

## 한 줄 정리

Backward compatibility waivers and consumer exception governance는 호환성 예외를 숨은 친절이 아니라, expiry와 compensating control과 removal 조건을 가진 관리 대상 부채로 다루는 방식이다.
