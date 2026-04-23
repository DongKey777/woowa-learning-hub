# Replication Lag Forensics and Root-Cause Playbook

> 한 줄 요약: replication lag를 줄이려면 "얼마나 늦었는가"보다 먼저, transport delay인지 apply delay인지, 특정 긴 트랜잭션/DDL 때문인지, replica 자원 포화 때문인지 분류해야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md)
- [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)
- [Replication Failover와 Split-Brain](./replication-failover-split-brain.md)
- [Group Commit, Binlog, fsync, Durability](./group-commit-binlog-fsync-durability.md)
- [CDC Backpressure, Binlog/WAL Retention, and Replay Safety](./cdc-backpressure-binlog-retention-replay.md)

retrieval-anchor-keywords: replication lag forensics, apply lag, transport lag, replica SQL thread delay, long transaction replication delay, relay log backlog, read replica incident, backend db forensics

## 핵심 개념

replication lag는 하나의 현상이지 하나의 원인이 아니다.

대표적인 지연 유형:

- transport lag
  - primary 변경이 replica로 아직 전달되지 않음
- apply lag
  - 전달은 됐지만 replica가 반영을 못 따라감
- visibility lag
  - 적용은 됐지만 read routing/cache/session 정책 때문에 늦게 보임

운영에서 중요한 건 lag 숫자를 보는 것이 아니라, **어느 단계가 병목인지 빠르게 분류하는 것**이다.

## 깊이 들어가기

### 1. 먼저 transport와 apply를 분리한다

lag 원인을 잘못 짚는 가장 흔한 경우는 네트워크/전송 지연과 SQL apply 지연을 섞어 보는 것이다.

분리 질문:

- source position은 계속 전진하는가
- replica I/O/receiver는 정상인가
- relay/binlog는 받아 왔는데 apply가 밀리는가
- 지연이 특정 순간부터 계단처럼 쌓였는가

보통:

- transport lag
  - 네트워크, receiver, source send 쪽 문제
- apply lag
  - replica CPU/IO, single-thread bottleneck, long transaction replay, DDL replay 문제

### 2. apply lag는 "긴 트랜잭션 하나"로도 크게 생긴다

replica는 보통 primary의 commit order 또는 dependency order를 따라가야 한다.  
그래서 primary에서 길고 무거운 트랜잭션 하나가 지나가면:

- replica apply thread가 오래 붙잡히고
- 뒤에 있는 작은 트랜잭션이 줄줄이 밀리며
- 전체 lag가 갑자기 치솟을 수 있다

대표 원인:

- 대량 UPDATE/DELETE
- online DDL 또는 index build replay
- 큰 batch commit
- hot table purge/flush pressure와 겹친 apply slowdown

### 3. lag가 steady하게 쌓이는지, spike 후 회복되는지 본다

패턴에 따라 원인이 달라진다.

- steady growth
  - replica capacity 부족
  - apply throughput < primary write throughput
- burst spike then recover
  - 특정 giant transaction
  - DDL replay
  - checkpoint/flush stall
- saw-tooth
  - batch 주기, purge, fsync, compaction 간섭

즉 lag 그래프 모양 자체가 forensic signal이다.

### 4. read incident와 replication incident를 분리해서 본다

사용자는 "방금 수정한 값이 안 보인다"고 말해도, 원인이 꼭 replication lag는 아닐 수 있다.

가능한 원인:

- 실제 replica apply delay
- stale cache
- session pinning 실패
- 잘못된 read routing

그래서 사용자 이슈를 다룰 때는:

1. source commit 시점
2. replica apply 시점
3. read request가 어느 경로로 갔는지

를 연결해야 한다.

### 5. forensic 질문은 항상 "어느 트랜잭션이 lag를 만들었나"로 수렴한다

특히 apply lag에서는 다음을 찾아야 한다.

- 현재 replay 중인 giant transaction이 있는가
- 최근 DDL/maintenance가 있었는가
- 특정 tenant/batch가 write burst를 만들었는가
- replica에서 hot page/flush/purge debt가 apply를 늦추는가

즉 lag는 복제 계층만의 문제가 아니라, **source write shape와 replica storage 상태가 만나는 지점**에서 생긴다.

### 6. 완화책도 원인별로 달라야 한다

대표적인 대응:

- transport 문제
  - network/receiver/source health 확인
- giant transaction apply 문제
  - batch chunk 축소, commit frequency 조정
- steady capacity 부족
  - replica 증설, parallel apply 개선, 읽기 부하 분산
- DDL/maintenance 유발
  - 작업 윈도우 재설계, lag gate 도입

timeout이나 fallback만 키우면 근본 원인은 그대로 남는다.

## 실전 시나리오

### 시나리오 1. 야간 배치 뒤 lag가 40분 치솟음

형태:

- 평소 정상
- 특정 시각부터 급격히 spike
- 이후 서서히 회복

우선 의심:

- giant batch transaction
- 대량 delete/update replay
- index build/DDL replay

### 시나리오 2. 하루 종일 lag가 조금씩 증가

형태:

- steady growth
- peak traffic에만 더 심해짐

우선 의심:

- replica apply capacity 부족
- replica IO saturation
- parallelism 부족

### 시나리오 3. 사용자는 stale read를 보고하지만 lag metric은 낮음

우선 의심:

- routing/pinning 문제
- cache invalidation 실패
- consistency token 미적용

이 경우는 replication forensics보다 read path forensics가 더 중요하다.

## 코드로 보기

```sql
-- MySQL 계열 점검 감각
SHOW REPLICA STATUS\G
SHOW FULL PROCESSLIST;
SHOW ENGINE INNODB STATUS\G
```

```text
forensic checklist
1. source position advancing?
2. relay/binlog received but not applied?
3. currently replaying giant transaction?
4. recent DDL / batch / maintenance?
5. replica IO/CPU/flush/purge debt signs?
6. user issue path actually hit replica?
```

```sql
-- primary/replica write shape 확인용 예시
SHOW MASTER STATUS;
SHOW BINARY LOG STATUS;
```

핵심은 한 개 지표보다, "전송-적용-가시화" 세 단계를 연결해서 보는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| lag metric만 본다 | 단순하다 | 원인 분리가 안 된다 | 초기 관측 |
| transport/apply 분리 관측 | 원인 분류가 빨라진다 | 메트릭 설계가 필요하다 | 운영 replica |
| batch chunk 축소 | giant transaction lag를 줄인다 | 처리 시간이 늘 수 있다 | 야간 배치/대량 수정 |
| primary fallback 확대 | 사용자 stale read를 줄인다 | primary 부하가 커진다 | incident 완화 |

## 꼬리질문

> Q: replication lag에서 가장 먼저 나눠 봐야 할 축은 무엇인가요?
> 의도: 전송 지연과 적용 지연을 구분하는지 확인
> 핵심: transport lag인지 apply lag인지 먼저 나눠야 한다

> Q: giant transaction 하나가 왜 뒤에 있는 작은 트랜잭션까지 밀리게 하나요?
> 의도: apply ordering의 성격을 이해하는지 확인
> 핵심: replica는 commit/dependency 질서를 따라가야 해서 긴 작업이 파이프라인을 막을 수 있다

> Q: 사용자 stale read가 항상 replication lag 때문인가요?
> 의도: read routing 문제와 replication 문제를 구분하는지 확인
> 핵심: 아니다. cache/routing/session pinning 실패도 같은 증상을 만든다

## 한 줄 정리

replication lag forensics의 본질은 lag 숫자를 보는 게 아니라, transport·apply·read visibility 중 어디서 지연이 생겼는지와 어떤 write shape가 그 지연을 만들었는지 분리하는 것이다.
