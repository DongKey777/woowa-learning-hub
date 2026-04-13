# Method Inlining Heuristics and Deoptimization Triggers

> 한 줄 요약: HotSpot inlining은 call profile, method size, hotness, polymorphism, code cache pressure를 보고 결정되고, 그 가정이 깨지면 uncommon trap과 deoptimization이 이어질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Lock Coarsening and Lock Elimination](./lock-coarsening-elimination.md)
> - [Escape Analysis and Scalar Replacement](./escape-analysis-scalar-replacement.md)
> - [JFR Event Interpretation](./jfr-event-interpretation.md)

> retrieval-anchor-keywords: inlining heuristics, method size, call profile, monomorphic, polymorphic, megamorphic, hot method, uncommon trap, deoptimization, code cache, compile threshold, HotSpot C2

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전 시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄 정리)

</details>

## 핵심 개념

Inlining은 메서드 호출을 호출 지점에 펼쳐 넣는 최적화다.  
HotSpot은 무조건 펼치지 않고, 실행 프로파일과 코드 크기, 호출 패턴을 보고 선택한다.

Inlining이 잘 되면 다음 이득이 있다.

- call overhead 감소
- 상수 전파와 분기 최적화
- escape analysis 기회 증가
- lock elimination 기회 증가

## 깊이 들어가기

### 1. 어떤 메서드가 잘 inline되나

대체로 다음이 유리하다.

- 작다
- 자주 호출된다
- call target이 안정적이다
- 너무 깊게 중첩되지 않는다

### 2. polymorphism이 커지면 어려워진다

호출 대상이 하나면 monomorphic, 몇 개면 polymorphic, 너무 많으면 megamorphic에 가까워진다.  
대상이 흔들릴수록 inlining이 보수적으로 된다.

### 3. method size는 중요한 신호다

메서드가 너무 크면 code size explosion이 생길 수 있다.  
JIT는 전체 성능을 위해 inline budget을 조절한다.

### 4. deoptimization 트리거는 inlining 가정과 연결된다

inline된 코드가 타입/분기 가정을 했는데 현실이 바뀌면 uncommon trap이 일어나고 deopt가 생길 수 있다.

대표 원인:

- call target 변화
- class loading으로 새 구현 등장
- branch profile 변화
- speculation 실패

### 5. code cache pressure도 영향을 준다

좋은 inlining은 성능에 이롭지만, 너무 많으면 code cache가 커지고 컴파일 비용도 늘 수 있다.

## 실전 시나리오

### 시나리오 1: 작은 getter/setter가 많다

Inlining이 잘 되면 call overhead가 거의 사라질 수 있다.

### 시나리오 2: 인터페이스 구현체가 자주 바뀐다

call profile이 흔들리면 inlining이 덜 공격적이거나 deopt가 생길 수 있다.

### 시나리오 3: 배포 후 갑자기 느려진다

새 클래스 로딩이나 profile 변화로 speculated inlining이 무효화됐을 수 있다.

## 코드로 보기

### 1. inline 후보 예

```java
public int add(int a, int b) {
    return a + b;
}
```

### 2. polymorphic call

```java
interface Formatter {
    String format(Object value);
}
```

### 3. deopt를 떠올리게 하는 예

```java
// call target이 갑자기 바뀌면 inline 가정이 깨질 수 있다.
```

### 4. 관측 명령

```bash
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintCompilation -XX:+PrintInlining -jar app.jar
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| aggressive inlining | call overhead를 줄인다 | code cache와 deopt 리스크가 늘 수 있다 |
| conservative inlining | 안정적이다 | 최적화 기회를 놓칠 수 있다 |
| monomorphic 설계 | JIT가 잘 읽는다 | 구조가 경직될 수 있다 |
| polymorphic 설계 | 확장하기 쉽다 | inlining이 어려워질 수 있다 |

핵심은 inlining을 "빠른 메서드"가 아니라 "JIT가 만든 call profile 기반 speculative optimization"으로 보는 것이다.

## 꼬리질문

> Q: 어떤 메서드가 inline되기 쉬운가요?
> 핵심: 작고 hot하며 호출 대상이 안정적인 메서드다.

> Q: deoptimization은 왜 생기나요?
> 핵심: inlining 시점의 가정이 깨지면 uncommon trap을 통해 되돌아갈 수 있기 때문이다.

> Q: inlining이 항상 좋은가요?
> 핵심: 아니다. code cache와 compile 비용, deopt 위험도 같이 본다.

## 한 줄 정리

HotSpot inlining은 hot path와 call profile에 기반한 추측적 최적화이고, 그 추측이 깨지면 deoptimization이 따라올 수 있다.
