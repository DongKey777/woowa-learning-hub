# Quorum Write와 Read Intuition

> 한 줄 요약: quorum은 “몇 개가 살아 있으면 안전한가”를 결정하는 규칙이고, 앱 팀은 그 규칙을 일관성 예산으로 이해해야 한다.

**난이도: 🟢 Beginner**

관련 문서: [Replication Failover and Split Brain](./replication-failover-split-brain.md), [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md), [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
retrieval-anchor-keywords: quorum, majority write, majority read, quorum intuition, consistency budget

## 핵심 개념

Quorum은 분산 저장에서 일부 노드가 장애나 지연이 있어도 안전성을 유지하기 위해, 일정 수 이상의 응답을 요구하는 방식이다.

왜 중요한가:

- 앱 팀은 “이 요청이 언제 성공한 것으로 볼 수 있는가”를 알아야 한다
- read/write quorum은 지연과 정합성의 trade-off를 직관적으로 설명한다
- split brain을 막는 사고방식과도 연결된다

이 문서의 초점은 알고리즘 구현이 아니라, **앱 팀이 어떤 믿음을 가질 수 있는지**다.

## 깊이 들어가기

### 1. quorum의 직관

노드가 3개일 때, 2개 이상이 같은 답을 주면 그 답을 신뢰하는 식으로 생각할 수 있다.

- write quorum: 충분한 노드에 쓰여야 성공
- read quorum: 충분한 노드에서 읽어와야 최신성을 신뢰

핵심은 전체가 아니라 **다수 의견**을 신뢰하는 것이다.

### 2. 왜 이게 유용한가

quorum은 다음을 이해하는 데 도움이 된다.

- 느린 replica가 하나 있어도 전체가 안전할 수 있다
- 다수에 도달하지 못하면 write를 실패시켜야 할 수 있다
- read는 빠를 수 있지만, 충분히 모아야 최신성을 얻는다

### 3. 앱 팀이 흔히 오해하는 점

- quorum이면 항상 즉시 일관성이라고 생각한다
- quorum이면 느린 노드를 무시해도 된다고 생각한다
- quorum은 단순히 성능 최적화라고 생각한다

실제로 quorum은 성능이 아니라 **안전성과 관측 신뢰도**를 조절하는 장치다.

### 4. 언제 느려지는가

- 노드가 많이 죽었을 때
- 네트워크가 불안정할 때
- majority를 맞추기 어려운 지역 분산 환경일 때

즉 quorum은 안전하지만, 때로는 “느린 정답”이 된다.

## 실전 시나리오

### 시나리오 1: 일부 replica가 뒤처져도 write를 확정해야 함

quorum write가 있으면 일정 수 이상에 성공한 뒤에만 커밋한다.  
앱은 이 기준을 알고 retry와 timeout을 설계해야 한다.

### 시나리오 2: read가 자꾸 옛값을 보여줌

단일 replica read만 믿으면 최신성을 보장하지 못할 수 있다.  
read quorum이나 primary fallback이 필요할 수 있다.

### 시나리오 3: 장애 중에 “성공인지 실패인지”가 애매함

quorum 미달로 실패했는지, 일부만 반영됐는지 애매해질 수 있다.  
이럴 때 멱등성과 재조회가 중요하다.

## 코드로 보기

```text
3 replicas:
  write succeeds when 2 replicas confirm
  read trusts result when 2 replicas agree
```

```java
if (!quorumReached(acks, 2)) {
    throw new RetryableConsistencyException();
}
```

quorum은 “DB가 알아서 다 맞춰준다”가 아니라, **앱이 신뢰할 수 있는 최소 합의선**을 정하는 개념이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| majority write/read | 안전하다 | 지연이 늘 수 있다 | 정합성이 중요한 분산계 |
| single primary + replica | 단순하다 | failover/lag에 취약 | 일반 OLTP |
| read quorum only | 읽기 신뢰성이 높다 | 구현이 복잡하다 | critical reads |
| write quorum only | 쓰기 안전성이 높다 | 읽기 최신성은 별도 필요 | append-heavy 시스템 |

## 꼬리질문

> Q: quorum은 왜 필요한가요?
> 의도: 분산 합의의 안전선 개념을 이해하는지 확인
> 핵심: 일부 노드가 불안정해도 다수로 안전성을 유지하기 위해서다

> Q: quorum이면 read-after-write가 항상 보장되나요?
> 의도: quorum과 일관성 수준을 혼동하지 않는지 확인
> 핵심: 구현과 라우팅에 따라 추가 보장이 필요하다

> Q: quorum이 느려지는 대표 상황은 무엇인가요?
> 의도: majority 확보 비용을 아는지 확인
> 핵심: 노드 장애와 네트워크 불안정이다

## 한 줄 정리

Quorum은 분산 시스템에서 다수의 확인을 안전선으로 삼는 규칙이고, 앱 팀은 이를 지연과 정합성의 예산으로 이해해야 한다.
