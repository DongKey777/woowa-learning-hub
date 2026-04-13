# Application-Level Fencing Token Propagation

> 한 줄 요약: fencing token은 DB에만 저장하면 반쪽짜리고, 모든 write 경로와 재시도 경계에 같이 실어 보내야 효과가 있다.

관련 문서: [DB Lease와 Fencing Token](./db-lease-fencing-coordination.md), [Ghost Reads와 Mixed Routing Write Fence Tokens](./ghost-reads-mixed-routing-write-fence-tokens.md), [Stale Lease Renewal Failure와 Fencing](./stale-lease-renewal-failure-fencing.md)
Retrieval anchors: `fencing token propagation`, `epoch propagation`, `write guard`, `stale writer`, `token forwarding`

## 핵심 개념

Fencing token은 누가 최신 주체인지 나타내는 단조 증가 값이다.  
하지만 토큰을 발급만 하고 애플리케이션 경로에 전달하지 않으면 stale write를 막지 못한다.

왜 중요한가:

- 작업자끼리 역할은 바뀌어도, 실제 write 요청은 여러 계층을 통과한다
- 토큰이 누락되면 오래된 요청이 최신 상태를 덮을 수 있다
- 재시도/큐/서브작업까지 토큰이 따라가야 한다

즉 fencing은 저장소의 기능이 아니라 **end-to-end write guard**로 봐야 한다.

## 깊이 들어가기

### 1. 왜 propagation이 중요한가

토큰이 DB에만 있으면 다음 문제가 남는다.

- 서비스 A에서 토큰을 받았지만 서비스 B로 안 넘김
- 메시지 재시도 중 토큰이 유실
- 서브작업이 옛 토큰으로 write

결국 stale writer가 통과한다.

### 2. 어디에 실어야 하나

- API header
- command payload
- message metadata
- batch job context

모든 write entry point가 최신 token을 검증해야 한다.

### 3. 재시도와 토큰

재시도는 같은 토큰을 유지해야 할 수도 있고, 새로운 epoch로 승격해야 할 수도 있다.  
핵심은 “재시도 = 무조건 같은 값”이 아니라, **재시도 중에도 stale인지 판단할 수 있어야 한다**는 것이다.

### 4. 감사 로그와 토큰

토큰을 로그에 남기면 장애 분석에 도움이 된다.

- 어떤 write가 어떤 epoch로 들어왔는지 추적 가능
- stale write가 어디서 시작됐는지 찾기 쉬움

## 실전 시나리오

### 시나리오 1: 서비스 간 호출에서 토큰이 빠짐

상위 서비스는 새 epoch를 받았지만 하위 서비스는 옛 토큰으로 write한다.  
이 경우 stale write가 막히지 않는다.

### 시나리오 2: 메시지 재처리 시 옛 토큰이 재사용됨

큐에서 다시 소비된 이벤트가 최신성 확인 없이 처리되면, 이전 주체가 다시 쓸 수 있다.

### 시나리오 3: batch child job이 토큰을 잃음

부모 job은 fencing을 알고 있지만, 자식 job이 토큰을 전달받지 못해 stale write를 낸다.

## 코드로 보기

```java
class WriteContext {
    final long fencingToken;
    WriteContext(long fencingToken) { this.fencingToken = fencingToken; }
}

void updateAccount(WriteContext ctx) {
    accountRepository.updateIfTokenFresh(ctx.fencingToken);
}
```

```sql
UPDATE account_state
SET balance = balance + 100,
    fencing_token = 42
WHERE id = 1
  AND fencing_token < 42;
```

토큰은 “있다”보다 “전파된다”가 중요하다.  
어디 한 군데라도 빠지면 stale write 방어가 무너진다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| DB-only fencing | 저장소는 강하다 | 경로 누락이 생긴다 | 매우 단순한 구조 |
| end-to-end propagation | 안전하다 | 구현이 복잡하다 | 중요한 write 경로 |
| header + payload propagation | 유연하다 | 중복 관리 필요 | 서비스 간 호출 |
| token at gateway only | 일괄 통제가 쉽다 | 내부 전파가 약할 수 있다 | 단일 진입점 |

## 꼬리질문

> Q: fencing token을 DB에만 넣으면 왜 부족한가요?
> 의도: 경로 중간에서 토큰이 사라지는 문제를 아는지 확인
> 핵심: write가 여러 계층을 통과하면 토큰도 같이 전달되어야 한다

> Q: token propagation의 가장 흔한 누락 지점은 어디인가요?
> 의도: 서비스 호출과 재시도 경계의 위험을 아는지 확인
> 핵심: 메시지 metadata, child job, retry path다

> Q: 토큰이 로그에 있으면 왜 도움이 되나요?
> 의도: 장애 추적 가능성 이해 여부 확인
> 핵심: stale write가 어디서 유입됐는지 역추적할 수 있다

## 한 줄 정리

Application-level fencing은 토큰을 발급하는 것으로 끝나지 않고, 모든 write 경로와 재시도 경계에 끝까지 전파해야 완성된다.
