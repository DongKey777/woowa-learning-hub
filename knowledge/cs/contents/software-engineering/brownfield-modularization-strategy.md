# Brownfield Modularization Strategy

> 한 줄 요약: brownfield modularization은 새 시스템을 만드는 일이 아니라, 기존 코드와 데이터의 제약을 인정한 채 경계를 점진적으로 세우는 전환 전략이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Architecture Runway and Refactoring Window](./architecture-runway-refactoring-window.md)
> - [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)
> - [Service Split, Merge, and Absorb Evolution Framework](./service-split-merge-absorb-evolution-framework.md)

> retrieval-anchor-keywords:
> - brownfield modularization
> - incremental modularization
> - legacy constraints
> - boundary carving
> - module extraction
> - dependency inversion
> - strangler path
> - refactor sequencing

## 핵심 개념

brownfield modularization은 새로 시작하는 greenfield가 아니다.
이미 돌아가는 시스템을 멈추지 않고, 경계와 의존을 다시 정리하는 일이다.

핵심은 "깨끗하게 다시 쓰자"가 아니라, **실제 제약 속에서 개선 순서를 정하는 것**이다.

---

## 깊이 들어가기

### 1. 먼저 경계를 그릴 수 있어야 한다

기존 시스템에서 모듈화가 가능하려면:

- 도메인 용어가 어느 정도 보이고
- 변경이 자주 일어나는 축이 드러나고
- 데이터 접근 경로가 파악되어야 한다

즉 경계를 모르면 분리도 못 한다.

### 2. 가장 먼저 해야 할 일은 추상화가 아니라 관찰이다

brownfield에서는 보통 리팩터링보다 먼저 해야 할 것이 있다.

- 호출 흐름 파악
- 데이터 의존성 파악
- 순환 참조 발견
- 배포 위험 포인트 찾기

관찰 없이 바로 분리하면 더 큰 혼란이 난다.

### 3. extraction은 작은 단위로 해야 한다

한 번에 많은 것을 옮기면 실패 반경이 커진다.

권장 순서:

1. 읽기 경로 분리
2. 공통 유틸/계산 분리
3. 쓰기 경로 캡슐화
4. 계약 테스트 추가
5. 필요 시 서비스 분리

이 순서는 [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)와 잘 맞는다.

### 4. 데이터 경계가 가장 어렵다

코드는 모듈로 나눠도 데이터가 섞여 있으면 경계가 약하다.

그래서:

- 테이블 직접 접근을 줄이고
- repository/port를 캡슐화하고
- 필요한 경우 ACL이나 별도 read model을 둬야 한다

### 5. 모듈화는 목표가 아니라 수단이다

모듈을 나누는 이유는 다음 중 하나여야 한다.

- 변경 충돌 감소
- 배포 독립성 증가
- 책임 명확화
- 테스트 단순화

그 자체가 목적이면 구조만 복잡해진다.

---

## 실전 시나리오

### 시나리오 1: 주문/결제/배송이 한 서비스에 섞여 있다

우선 경계가 자주 바뀌는 영역부터 분리하고, 공용 데이터는 포트로 감싼다.

### 시나리오 2: 레거시 테이블이 많다

바로 DB를 쪼개기보다, 읽기/쓰기 진입점을 먼저 모듈 경계로 만든다.

### 시나리오 3: 분리가 오래 걸린다

architecture runway를 만들고 refactoring window를 정해서 단계적으로 옮긴다.

---

## 코드로 보기

```java
public interface BillingPort {
    BillingResult bill(BillingCommand command);
}
```

brownfield modularization은 새 경계를 먼저 뚫고, 기존 구현을 그 경계 뒤로 밀어 넣는 작업이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 재작성 | 깔끔하다 | 위험이 매우 크다 | 아주 작은 시스템 |
| 점진적 모듈화 | 안정적이다 | 시간이 든다 | 운영 중 시스템 |
| 모듈화 후 분리 | 전환이 쉽다 | 준비 비용이 있다 | 장기 진화가 필요할 때 |

brownfield modularization은 완벽한 설계가 아니라, **운영 중인 시스템을 덜 아프게 바꾸는 전략**이다.

---

## 꼬리질문

- 어떤 경계부터 먼저 잘라야 하는가?
- 데이터 경계는 언제 분리할 것인가?
- extraction 순서를 누가 정하는가?
- 모듈화가 실제로 변경 비용을 줄였는가?

## 한 줄 정리

Brownfield modularization strategy는 기존 시스템의 제약을 인정한 채, 경계와 의존을 점진적으로 재배치해 진화 가능한 구조로 바꾸는 접근이다.
