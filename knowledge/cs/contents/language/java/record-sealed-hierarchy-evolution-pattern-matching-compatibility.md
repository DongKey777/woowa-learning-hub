# Record/Sealed Hierarchy Evolution and Pattern Matching Compatibility

> 한 줄 요약: record와 sealed hierarchy는 닫힌 모델을 잘 표현하지만, API와 payload가 진화하면 그 닫힘이 곧 호환성 제약이 된다. component 추가, variant 추가, default branch 남용, unknown variant 처리 부재는 컴파일 안정성과 runtime compatibility를 서로 어긋나게 만들 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md)
> - [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
> - [Java Binary Compatibility and Runtime Linkage Errors](./java-binary-compatibility-linkage-errors.md)
> - [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)

> retrieval-anchor-keywords: record evolution, sealed hierarchy evolution, pattern matching compatibility, exhaustive switch, default branch hazard, unknown variant, API evolution, payload variant, record component addition, closed world model, compatibility tradeoff

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

record와 sealed hierarchy는 "닫힌 모델"에 강하다.  
하지만 시스템이 진화하는 순간 이 장점은 제약으로도 돌아온다.

대표적인 진화 축:

- record component 추가/삭제
- sealed variant 추가
- pattern matching switch 분기 변경
- payload unknown variant 처리

즉 닫힌 타입 모델은 설계 안정성을 주지만,  
호환성 전략 없이 확장하면 old consumer와 new producer가 쉽게 어긋난다.

## 깊이 들어가기

### 1. record component 추가는 payload contract 변경이다

record에 component를 추가하면 소스상으론 단순해 보여도:

- canonical constructor 시그니처 변화
- JSON binding 요구 변화
- old payload compatibility 변화

가 한꺼번에 생긴다.

즉 "필드 하나 추가"가 단순 refactor가 아니다.

### 2. sealed hierarchy variant 추가는 exhaustive switch에 직접 영향 준다

새 variant를 추가하면 그 장점이 드러난다.

- exhaustive switch는 컴파일 타임에 누락을 더 잘 드러낸다

하지만 동시에 단점도 있다.

- old binary/payload consumer는 새 variant를 모를 수 있다
- default branch가 있으면 새 variant가 조용히 삼켜질 수 있다

즉 compile-time safety와 cross-version runtime safety는 다른 문제다.

### 3. default branch는 안전망이 아니라 호환성 선택이다

sealed hierarchy에서 `default`를 두면 편하다.  
하지만 그 순간 "새 variant가 들어왔을 때 어떻게 할지"를 조용히 결정해버린다.

- fail-fast
- unknown variant로 보존
- fallback 처리

즉 default branch는 문법 편의가 아니라 evolution policy다.

### 4. internal closed world와 external payload world를 구분해야 한다

서비스 내부 도메인은 sealed로 닫아도 좋다.  
하지만 외부 payload까지 완전히 닫혀 있다고 가정하면 위험할 수 있다.

그래서 흔한 패턴은 이렇다.

- 외부 입력: unknown variant 허용 또는 보존
- 내부 도메인: sealed hierarchy로 닫기

즉 boundary에서 anti-corruption mapping이 필요하다.

### 5. pattern matching은 가독성 도구이면서 migration 경계다

pattern matching switch는 좋지만, 분기 누락이나 unknown handling이 숨어들 수 있다.  
특히 payload replay나 이벤트 버전 혼재 상황에선 compile success보다 runtime variant strategy가 더 중요하다.

## 실전 시나리오

### 시나리오 1: 이벤트 결과 타입에 새 variant를 추가했다

`PendingReview`를 추가했더니 최신 코드는 안전해졌지만,  
old consumer는 이 값을 모르고 실패하거나 default로 삼켜버린다.

### 시나리오 2: record component를 추가한 뒤 old client 요청이 깨진다

record DTO가 깔끔해 보였지만 새 필수 component가 생기며  
예전 payload가 더 이상 바인딩되지 않는다.

### 시나리오 3: default branch가 장애를 숨긴다

새 variant가 왔는데 default에서 그냥 generic failure로 바꿔버린다.  
컴파일은 통과하지만 도메인 의미가 사라진다.

### 시나리오 4: 외부 API variant를 sealed로 직접 모델링했다

partner API가 variant를 추가하자 sealed model이 곧바로 깨졌다.  
이 경우는 raw DTO와 내부 sealed model을 분리하는 편이 낫다.

## 코드로 보기

### 1. sealed hierarchy와 pattern matching

```java
public sealed interface PaymentState permits Authorized, Captured, Failed {}

public record Authorized(String id) implements PaymentState {}
public record Captured(String id) implements PaymentState {}
public record Failed(String reason) implements PaymentState {}
```

### 2. 새 variant 추가 시 생각할 것

```java
public record PendingReview(String reviewer) implements PaymentState {}
```

이 순간 switch exhaustiveness는 좋아지지만, old consumer/runtime payload compatibility는 따로 검토해야 한다.

### 3. boundary 분리 감각

```java
// external DTO는 unknown variant를 보존하고,
// 내부 도메인은 sealed hierarchy로 닫는 편이 더 안전할 수 있다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| sealed + exhaustive switch | 내부 모델 안정성과 분기 누락 방지에 좋다 | variant 추가 시 cross-version 호환성 전략이 필요하다 |
| default branch 적극 사용 | 코드는 빨리 쓸 수 있다 | unknown variant를 조용히 숨길 수 있다 |
| external DTO / internal sealed 분리 | 진화와 내부 안정성을 함께 가져가기 쉽다 | 매핑 계층이 늘어난다 |
| record DTO 직접 노출 | 간결하다 | component 변화가 곧 payload 계약 변화가 된다 |

핵심은 record/sealed를 문법 선택이 아니라 closed-world modeling과 compatibility boundary의 선택으로 보는 것이다.

## 꼬리질문

> Q: sealed hierarchy에 variant를 추가하면 좋은 것 아닌가요?
> 핵심: 내부 compile-time safety에는 좋지만, old consumer/runtime payload compatibility는 별도 문제다.

> Q: default branch는 왜 조심해야 하나요?
> 핵심: 새로운 variant를 조용히 삼켜 evolution bug를 숨길 수 있기 때문이다.

> Q: record DTO는 왜 진화에 민감한가요?
> 핵심: component 구조와 canonical constructor가 곧 binding/serialization 계약이 되기 쉽기 때문이다.

> Q: 외부 payload도 sealed로 바로 모델링해도 되나요?
> 핵심: 외부 세계가 truly closed라는 보장이 약하면 boundary DTO와 내부 sealed model을 분리하는 편이 안전하다.

## 한 줄 정리

record와 sealed는 내부 도메인을 단단하게 만들지만, payload와 버전이 진화하는 환경에서는 unknown handling과 boundary 분리를 같이 설계해야 진짜 안전하다.
