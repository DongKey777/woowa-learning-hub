# Read-Your-Writes와 Session Pinning 전략

> 한 줄 요약: 사용자는 “방금 바꾼 값이 바로 보여야 한다”고 기대하고, 그 기대를 지키려면 읽기 라우팅에 세션 기억이 들어가야 한다.

**난이도: 🔴 Advanced**

관련 문서: [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md), [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md), [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md), [Client Consistency Tokens](./client-consistency-tokens.md), [Causal Consistency Intuition](./causal-consistency-intuition.md), [Replication Failover and Split Brain](./replication-failover-split-brain.md)
retrieval-anchor-keywords: read-your-writes, read your writes, session pinning, session pinning ttl, sticky session, session affinity, primary pinning, recent write primary fallback, monotonic read, consistency token, causal token, own write not visible, refresh after edit shows old value, profile update not showing, same user sees stale data, my update disappeared after refresh, 수정 직후 새로고침 옛값, 내가 바꾼 값이 안 보임, 사용자 본인 변경 즉시 반영, recent write routing

## 증상별 바로 가기

- `내가 방금 수정한 값이 내 화면에 안 보인다`, `my update disappeared after refresh`처럼 같은 사용자 세션의 최신성 보장이 핵심이면 이 문서에서 session pinning, TTL, primary fallback을 본다.
- `write 직후 전체적으로 stale하다`, `insert succeeded but row is still missing`처럼 replica lag 자체를 먼저 의심해야 하면 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)로 간다.
- `새로고침마다 old/new가 번갈아 나온다`, `retry changed result`, `pagination order keeps flipping`처럼 요청별 라우팅이 흔들리면 [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md)을 먼저 본다.
- 세션 메모리보다 클라이언트 전달 토큰이 더 적합한 경우는 [Client Consistency Tokens](./client-consistency-tokens.md)에서 이어 본다.

## 핵심 개념

Read-your-writes는 한 세션에서 자신이 방금 쓴 데이터가 다음 읽기에서 보이는 성질이다.  
분산 DB나 primary/replica 구조에서는 이 성질이 자동으로 보장되지 않는다.

왜 중요한가:

- 프로필 수정 직후 새로고침하면 옛 값이 보일 수 있다
- 주문 생성 후 상세 조회가 replica를 타면 결과가 안 보일 수 있다
- 사용자 입장에서는 “쓰기 성공”보다 “즉시 반영”이 더 중요할 때가 많다

session pinning은 이런 문제를 막기 위해, 최근 쓰기가 발생한 세션을 특정 읽기 경로에 묶는 전략이다.

## 깊이 들어가기

### 1. 왜 read-your-writes가 깨지는가

쓰기와 읽기가 서로 다른 노드로 가면, replica lag 때문에 최신 write가 아직 보이지 않을 수 있다.

하지만 lag만이 원인은 아니다.

- 첫 읽기는 primary, 다음 읽기는 replica로 바뀐다
- 커넥션 풀 재선택으로 다른 replica를 탄다
- retry가 다른 endpoint로 라우팅된다
- failover 직후 토폴로지 인식이 늦는다

즉 read-your-writes는 복제 지연 문제이면서 동시에 **라우팅 일관성 문제**다.

### 2. session pinning의 기본 방식

가장 단순한 방식은 “최근 write가 있었으면 일정 시간 primary로 보낸다”다.

이 패턴은 다음과 같다.

- write 성공 시 세션에 플래그를 남긴다
- 플래그가 살아 있는 동안 read는 primary로 간다
- TTL이 지나면 replica로 복귀한다

더 정교한 방식은 GTID, LSN, commit token을 세션에 저장해 replica가 그 지점까지 따라왔는지 확인하는 것이다.

### 3. 언제 sticky session이 충분한가

sticky session은 구현이 단순하지만 정확도가 낮다.

- 모바일 앱처럼 한 사용자가 비교적 긴 세션을 유지하는 경우
- read-after-write가 중요하지만, 세션 내 최신성만 맞으면 되는 경우
- 트래픽이 크지 않아 primary 부담을 감당할 수 있는 경우

반대로 관리자 화면, 결제 상태, 재고 화면처럼 정확한 최신성이 중요하면 token 기반 라우팅이 더 낫다.

### 4. 세션 pinning의 함정

- TTL이 너무 길면 primary가 과부하된다
- TTL이 너무 짧으면 read-your-writes가 다시 깨진다
- 세션이 아니라 커넥션에만 묶으면 connection pool 재사용 시 의미가 없다
- 쿠키나 로컬 메모리만 쓰면 멀티 인스턴스에서 사라진다

## 실전 시나리오

### 시나리오 1: 회원 정보 수정 직후 페이지 새로고침

이름을 바꿨는데 새로고침하자마자 옛 이름이 보이면 사용자 신뢰가 깨진다.  
이때 최근 write 세션은 primary로 pinning해야 한다.

### 시나리오 2: 주문 생성 후 주문 목록 조회

주문은 성공했지만 목록이 replica에서 읽혀 아직 반영되지 않았다면, 사용자는 실패했다고 생각할 수 있다.  
주문 생성 직후는 primary fallback이 안전하다.

### 시나리오 3: 고객센터 상담사가 상태 변경 후 화면 확인

관리자 도구는 지연보다 정합성이 중요하다.  
이 경우 sticky session보다 causal token 기반 라우팅이 더 적합하다.

## 코드로 보기

```java
class SessionRoutingContext {
    private boolean recentWrite;
    private long writeAtMillis;

    boolean shouldUsePrimary(long nowMillis) {
        return recentWrite && nowMillis - writeAtMillis < 30_000;
    }
}

class ReadRouter {
    DataSource route(SessionRoutingContext ctx, long nowMillis) {
        if (ctx.shouldUsePrimary(nowMillis)) {
            return primaryDataSource;
        }
        return replicaPool.pick();
    }
}
```

```sql
-- GTID 기반 read-after-write 보강 예시
SELECT WAIT_FOR_EXECUTED_GTID_SET('uuid:1-12345', 1);
SELECT * FROM orders WHERE id = 9001;
```

세션 pinning은 “항상 primary로 읽자”가 아니라, **최근 write의 관측을 유지할 만큼만 primary를 쓰자**는 뜻이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 무작위 replica 읽기 | 확장성이 좋다 | read-your-writes가 깨진다 | 최신성이 덜 중요한 조회 |
| TTL 기반 primary pinning | 구현이 쉽다 | primary 부하가 늘어난다 | 짧은 사용자 플로우 |
| sticky session | 사용자 경험이 안정적이다 | 노드 분산 효율이 낮다 | 세션 중심 서비스 |
| GTID/LSN 기반 라우팅 | 일관성이 높다 | 구현과 운영이 복잡하다 | 결제/관리/상태 변경 경로 |

## 꼬리질문

> Q: read-your-writes를 왜 replica lag만으로 설명하면 안 되나요?
> 의도: 라우팅 자체의 흔들림을 이해하는지 확인
> 핵심: lag가 작아도 다른 replica를 타면 옛 값을 볼 수 있다

> Q: primary pinning은 왜 TTL이 필요하나요?
> 의도: 영구 pinning이 아니라 완화 전략임을 아는지 확인
> 핵심: 최신성이 지나간 뒤에도 primary를 계속 쓰면 부하가 커진다

> Q: sticky session과 causal token 기반 라우팅의 차이는 무엇인가요?
> 의도: 단순 affinity와 정교한 일관성 제어를 구분하는지 확인
> 핵심: sticky는 단순하지만 부정확하고, token 기반은 더 정확하다

## 한 줄 정리

Read-your-writes를 지키려면 replica lag만 보는 게 아니라, 최근 write가 있었던 세션을 primary나 충분히 앞선 replica로 라우팅해야 한다.
