# Technical Debt Refactoring Timing

> 한 줄 요약: 기술 부채는 "나중에 고치자"가 아니라, 변경 비용과 장애 위험이 지금보다 커지는 순간을 정확히 잡아야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SOLID Failure Patterns](./solid-failure-patterns.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)

## 핵심 개념

기술 부채는 단순히 코드가 더럽다는 뜻이 아니다.

- 변경할 때마다 더 느려진다
- 장애가 날 때 원인 파악이 더 어려워진다
- 새로운 요구사항이 기존 구조에 잘 안 들어간다

즉, 부채는 **미래의 개발 속도와 안정성을 담보로 현재를 편하게 쓴 결과**다.

## 언제 리팩터링해야 하는가

### 1. 변경 비용이 기하급수로 증가할 때

같은 수정인데:

- 한 파일만 바꾸면 끝나던 것이
- 5개 파일, 3개 모듈, 2개 서비스로 퍼지기 시작하면

경계가 무너졌다는 신호다.

### 2. 버그가 특정 구조에서 반복될 때

같은 형태의 장애가 반복되면 우연이 아니다.

- null 방어 코드 반복
- if-else 분기 폭발
- 한 서비스에서 다른 서비스의 테이블을 직접 만짐

이런 패턴은 설계 부채가 쌓였다는 뜻이다.

### 3. 기능 추가보다 수정이 많은 경우

신규 기능보다 기존 코드 수정이 압도적으로 많아지면,
이건 기능이 아니라 **구조 자체가 요구사항을 못 따라가는 상태**다.

### 4. 팀이 이 구조를 설명하지 못할 때

설계를 잘 아는 사람만 수정할 수 있으면 이미 위험하다.
리팩터링 시점은 팀이 구조를 이해하는 비용이 유지비보다 싸게 느껴질 때다.

## 깊이 들어가기

### 1. 리팩터링은 3가지로 나뉜다

- 안전성 확보: 테스트 추가, 관측성 강화
- 구조 개선: 책임 분리, 경계 조정
- 모델 재설계: 도메인 변경, 모듈 재편

이 셋을 섞으면 실패한다.

### 2. 리팩터링 신호

| 신호 | 의미 |
|------|------|
| 신규 기능 하나가 여러 계층을 건드린다 | 경계가 깨졌다 |
| 테스트가 너무 느리거나 자주 깨진다 | 구조가 불안정하다 |
| 기능을 추가할수록 기존 코드가 더 위험해진다 | 확장 포인트가 없다 |
| 장애 후 원인 파악이 오래 걸린다 | 가시성이 부족하다 |

### 3. 리팩터링 타이밍을 놓치면 생기는 일

- 나중에 한 번에 고치려다 더 큰 장애를 만든다
- 새 기능 개발이 구조 보수로 변한다
- 팀이 구조를 두려워해서 손을 못 댄다

즉, 기술 부채는 시간이 갈수록 이자가 붙는다.

## 실전 시나리오

### 시나리오 1: if-else 지옥

결제 수단이 3개에서 7개로 늘었다.
분기문이 늘고, 예외 케이스가 늘고, 테스트가 폭발한다.

이때 Strategy나 정책 객체로 재구성해야 한다.

### 시나리오 2: 서비스 경계가 모호함

한 서비스가 다른 서비스의 테이블을 직접 읽고 쓴다.
작동은 하지만, 장애 시 책임 경계가 사라진다.

이건 모듈 분리나 ACL 도입 신호다.

### 시나리오 3: 오래된 공통 모듈

모든 곳에서 import하는 util이 자꾸 예외를 만든다.
이런 모듈은 잘못된 추상화일 가능성이 높다.

## 코드로 보기

### 리팩터링 전

```java
public int calculateFee(PaymentType type, int amount) {
    if (type == PaymentType.CARD) return amount * 3 / 100;
    if (type == PaymentType.TRANSFER) return amount * 1 / 100;
    if (type == PaymentType.POINT) return 0;
    throw new IllegalArgumentException("unsupported");
}
```

### 리팩터링 후

```java
public interface FeePolicy {
    int calculate(int amount);
}

public class CardFeePolicy implements FeePolicy {
    public int calculate(int amount) { return amount * 3 / 100; }
}
```

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 지금 리팩터링 | 미래 비용 감소 | 현재 일정 지연 | 반복 장애가 보일 때 |
| 나중에 리팩터링 | 즉시 속도 확보 | 이자 누적 | 실험 단계 |
| 부분 리팩터링 | 위험 분산 | 중간 상태가 오래 감 | 큰 시스템의 점진적 개선 |
| 전면 재작성 | 구조를 새로 잡을 수 있음 | 실패 확률이 높음 | 기존 구조가 회복 불가일 때 |

## 꼬리질문

- 리팩터링과 기능 개발의 우선순위를 어떤 기준으로 정하는가?
- 기술 부채를 측정 가능한 신호로 바꿀 수 있는가?
- 전면 재작성 대신 점진적 리팩터링을 선택하는 이유는 무엇인가?
- 테스트가 없는 레거시 코드에서 어디부터 손대는가?

## 한 줄 정리

기술 부채는 감정이 아니라 경제성 문제이고, 리팩터링 시점은 "이 구조를 더 쓰는 비용"이 "고치는 비용"을 넘는 순간이다.

