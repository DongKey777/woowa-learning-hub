# Causal Consistency Intuition

> 한 줄 요약: causal consistency는 “원인보다 결과를 먼저 보지 않게 한다”는 약속이고, 한 번 본 원인의 효과는 그 뒤에도 계속 보여야 한다.

관련 문서: [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md), [Monotonic Write Guarantees](./monotonic-write-guarantees.md), [Client Consistency Tokens](./client-consistency-tokens.md)
Retrieval anchors: `causal consistency`, `happens-before`, `session causality`, `read-your-writes`, `causal order`

## 핵심 개념

Causal consistency는 인과 관계가 있는 변경들이 관측 순서에서도 뒤집히지 않도록 하는 보장이다.  
즉 원인 A를 본 뒤에 그 결과 B를 보면, 다른 노드에서도 A 없이 B만 보이는 이상한 상태를 피한다.

왜 중요한가:

- 사용자는 “왜 결과만 보이고 원인은 없지?”를 이상하게 느낀다
- 단순 최신성보다 업무 흐름의 의미가 중요할 때가 많다
- read-your-writes, monotonic read/write는 causal consistency의 일부로 이해할 수 있다

causal consistency는 시간의 정렬이 아니라 **의미의 순서**를 지키는 약속이다.

## 깊이 들어가기

### 1. 인과 관계란 무엇인가

인과 관계는 한 사건이 다른 사건을 가능하게 하거나 유도할 때 생긴다.

- 게시글 작성 -> 댓글 작성
- 주문 생성 -> 결제 승인
- 권한 변경 -> 관리자 화면 반영

이 흐름에서 결과만 먼저 보이면 사용자는 시스템을 신뢰하기 어렵다.

### 2. causal consistency와 replica routing

단순히 가장 최신 replica를 보는 것만으로는 부족하다.  
인과 관계를 따라가려면 사용자가 본 이전 사건의 버전이 다음 읽기에도 반영돼야 한다.

### 3. session guarantee와의 관계

- read-your-writes: 내가 쓴 걸 다시 본다
- monotonic read: 내가 본 것보다 뒤로 가지 않는다
- monotonic write: 내 쓰기 순서가 뒤집히지 않는다

이 셋이 합쳐지면 causal consistency에 가까워진다.

### 4. 언제 꼭 필요한가

- 피드/댓글/알림
- 상태 전이가 있는 운영 화면
- 결제와 권한처럼 의미 순서가 중요한 경로

## 실전 시나리오

### 시나리오 1: 게시글은 있는데 댓글이 안 보임

댓글이 게시글보다 먼저 보이면 이상하지만, 그 반대는 자연스럽다.  
causal consistency는 이런 관측 이상을 줄인다.

### 시나리오 2: 주문을 본 뒤 결제 내역이 뒤늦게 사라짐

원인과 결과의 순서가 뒤집히면 사용자는 시스템이 불안정하다고 느낀다.

### 시나리오 3: 관리자 승인 후 권한이 늦게 보임

승인이라는 원인보다 결과가 늦게 보이면 운영자가 다시 클릭하게 된다.

## 코드로 보기

```text
cause -> effect
post created -> comment visible
order created -> payment status visible
role changed -> admin view changes
```

```java
class CausalContext {
    final String token;
    CausalContext(String token) { this.token = token; }
}
```

causal consistency는 “최신”보다 **원인과 결과가 관측 순서에서 뒤집히지 않는가**를 본다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| latest replica | 빠르다 | 인과가 깨질 수 있다 | 덜 민감한 조회 |
| session guarantees | 사용자 경험이 좋다 | 상태 관리가 필요하다 | 중요 사용자 흐름 |
| causal token routing | 의미 순서를 지킨다 | 복잡하다 | 핵심 업무 경로 |
| primary only | 가장 단순하다 | 확장성이 낮다 | critical read |

## 꼬리질문

> Q: causal consistency는 무엇을 보장하나요?
> 의도: 원인과 결과의 관측 순서를 아는지 확인
> 핵심: 인과 관계가 있는 변경이 뒤집혀 보이지 않게 한다

> Q: monotonic read와 causal consistency는 어떻게 다른가요?
> 의도: 세션 보장과 인과 보장을 구분하는지 확인
> 핵심: monotonic read는 뒤로 가지 않는 것이고 causal은 원인/결과 순서를 지킨다

> Q: causal consistency가 중요한 경로는 어디인가요?
> 의도: 의미 순서가 중요한 업무를 아는지 확인
> 핵심: 게시글/댓글, 주문/결제, 권한 변경 같은 흐름이다

## 한 줄 정리

Causal consistency는 인과 관계가 있는 사건의 관측 순서를 지키는 보장이고, read-your-writes와 monotonic guarantee가 그 하위에 있다.
