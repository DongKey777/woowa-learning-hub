# ABA Problem, `AtomicStampedReference`, and `AtomicMarkableReference`

> 한 줄 요약: CAS는 값이 "지금 A인가"만 본다. 그 사이 A -> B -> A가 일어나도 다시 A면 성공해버리므로, pointer-like state나 lock-free 구조에선 ABA 문제가 correctness bug가 될 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [`StampedLock` Optimistic Read and Conversion Pitfalls](./stampedlock-optimistic-read-conversion-pitfalls.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)

> retrieval-anchor-keywords: ABA problem, compare-and-set, CAS, AtomicStampedReference, AtomicMarkableReference, lock-free bug, versioned CAS, reference stamp, mark bit, pointer reuse, non-blocking algorithm

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

CAS는 보통 이런 질문만 한다.

- "현재 값이 기대값 A인가?"

문제는 값이 한 번 바뀌었다가 다시 A로 돌아와도,  
CAS 입장에서는 그냥 A로 보인다는 점이다.

이게 ABA 문제다.

- thread 1이 A를 읽는다
- thread 2가 A -> B -> A로 바꾼다
- thread 1의 CAS는 여전히 성공한다

즉 "값이 같음"과 "중간에 변화가 없었음"은 다른 문제다.

## 깊이 들어가기

### 1. ABA는 단순 counter보다 pointer-like state에서 더 아프다

숫자 카운터처럼 현재 값만 중요할 때는 ABA가 덜 치명적일 수 있다.  
하지만 다음은 다르다.

- lock-free stack top
- free-list head
- 상태 전이 노드 참조
- logical deletion 플래그

여기서는 "같은 참조로 돌아왔다"가 안전을 뜻하지 않는다.

### 2. stamp나 mark는 값 외의 추가 차원을 붙인다

`AtomicStampedReference`는 reference + version stamp를 같이 CAS한다.  
즉 reference가 다시 A로 돌아왔어도 stamp가 달라지면 변화가 감지된다.

`AtomicMarkableReference`는 reference + boolean mark를 같이 관리한다.  
logical deletion 같은 상황에 자주 언급된다.

즉 핵심은 CAS 기준을 "참조 하나"에서 "참조 + 메타정보"로 확장하는 것이다.

### 3. ABA가 항상 실무 핵심 문제는 아니다

일반 서비스 코드에서 lock-free linked structure를 직접 구현하지 않는다면,  
ABA가 주인공일 일은 많지 않다.

하지만 다음 순간엔 갑자기 중요해진다.

- custom non-blocking 자료구조
- object pool/free-list
- intrusive node 재사용
- 극단적 성능 최적화 코드

즉 자주 안 만나지만, 만나면 correctness에 직접 닿는다.

### 4. stamp를 쓴다고 만능은 아니다

stamp/mark를 넣으면 다음 비용이 생긴다.

- 코드 복잡도 증가
- 읽기/쓰기 절차 장황화
- stamp overflow나 정책 관리 고민

그래서 lock-free를 무조건 옹호하기보다,  
단순한 lock이나 더 높은 수준 유틸리티가 맞는지 먼저 봐야 한다.

### 5. ABA는 "경합"이 아니라 "이력 상실" 문제다

많은 사람이 ABA를 단순히 경쟁 상태로 이해하지만,  
본질은 이력 손실이다.

CAS는 현재 상태만 보고 과거의 변화를 모른다.  
stamp는 이력을 완전히 저장하진 않지만, 최소한 변화 흔적을 남긴다.

## 실전 시나리오

### 시나리오 1: lock-free stack top이 재사용된다

head가 A였고 pop/push가 여러 번 일어난 뒤 다시 A가 됐다.  
기존 CAS는 성공하지만, 그 사이 구조가 바뀌었을 수 있다.

### 시나리오 2: logical delete와 physical remove를 분리한다

`AtomicMarkableReference`의 mark bit를 이용해  
"삭제 예정" 상태를 표시하고 나중에 정리하는 패턴이 등장할 수 있다.

### 시나리오 3: pool/free-list 최적화가 오히려 버그를 만든다

노드를 재사용하면 reference가 같은 값으로 빨리 돌아오기 쉬워진다.  
이때 ABA 가능성이 커진다.

## 코드로 보기

### 1. stamp를 붙인 reference

```java
import java.util.concurrent.atomic.AtomicStampedReference;

AtomicStampedReference<String> ref = new AtomicStampedReference<>("A", 0);

int[] stampHolder = new int[1];
String current = ref.get(stampHolder);
boolean updated = ref.compareAndSet(current, "B", stampHolder[0], stampHolder[0] + 1);
```

### 2. mark bit 감각

```java
import java.util.concurrent.atomic.AtomicMarkableReference;

AtomicMarkableReference<String> ref = new AtomicMarkableReference<>("node", false);
boolean[] markHolder = new boolean[1];
String current = ref.get(markHolder);
```

### 3. 핵심 감각

```java
// CAS는 값 동일성만 본다.
// stamp/mark는 "중간 변화가 있었는가"를 더 잘 드러내기 위한 추가 차원이다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| plain CAS | 빠르고 단순하다 | ABA를 감지하지 못할 수 있다 |
| `AtomicStampedReference` | versioned CAS가 가능하다 | 코드와 상태 관리가 복잡해진다 |
| `AtomicMarkableReference` | logical deletion 같은 패턴에 유용하다 | boolean mark로 표현 가능한 경우에 한정된다 |
| lock 기반 설계 | reasoning이 쉽다 | 극단적 lock-free 성능은 못 얻을 수 있다 |

핵심은 ABA를 "CAS의 edge case"가 아니라 non-blocking correctness 모델의 일부로 보는 것이다.

## 꼬리질문

> Q: ABA 문제는 무엇인가요?
> 핵심: 값이 A에서 다른 값으로 바뀌었다가 다시 A로 돌아와도 plain CAS는 그 변화를 감지하지 못하는 문제다.

> Q: 왜 `AtomicStampedReference`가 도움이 되나요?
> 핵심: reference와 함께 stamp를 CAS해 중간 변화 흔적을 더 잘 드러내기 때문이다.

> Q: 모든 CAS 코드에 ABA 대책이 필요한가요?
> 핵심: 아니다. pointer-like state와 node 재사용이 있는 lock-free 구조에서 특히 중요하다.

> Q: 왜 그냥 lock을 쓰지 않나요?
> 핵심: 많은 경우 lock이 더 단순하고 안전하다. ABA 대응은 정말 lock-free가 필요한 경우에나 고려할 문제다.

## 한 줄 정리

ABA는 "현재 값이 같아 보여도 중간 변화 이력이 사라지는" 문제이므로, plain CAS로 pointer-like state를 다룰 땐 stamp나 mark 같은 추가 차원을 검토해야 한다.
