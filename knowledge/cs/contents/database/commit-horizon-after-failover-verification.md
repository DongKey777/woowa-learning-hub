# Commit Horizon After Failover, Loss Boundaries, and Verification

> 한 줄 요약: failover 뒤 가장 중요한 질문은 "누가 primary인가"보다, 새 primary가 어디까지의 commit horizon을 포함하고 있고 어느 구간부터는 유실 또는 재검증 대상이 되는가다.

**난이도: 🔴 Advanced**

관련 문서:

- [Replication Failover and Split Brain](./replication-failover-split-brain.md)
- [Primary Switch와 Write Fencing](./primary-switch-write-fencing.md)
- [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md)
- [Failover Visibility Window, Topology Cache, and Freshness Playbook](./failover-visibility-window-topology-cache-playbook.md)
- [Read Repair와 Failover Reconciliation](./read-repair-reconciliation-after-failover.md)

retrieval-anchor-keywords: commit horizon after failover, promotion verification, failover loss boundary, last applied position, write loss audit, failover verification, backend db recovery

## 핵심 개념

failover 직후에는 보통 "새 primary 승격 완료"만 확인하고 넘어가기 쉽다.  
하지만 운영적으로 더 중요한 건 다음이다.

- 새 primary가 마지막으로 포함한 commit 위치는 어디인가
- old primary에는 있었지만 새 primary에는 없을 수 있는 구간이 있는가
- 그 구간에 해당하는 비즈니스 작업은 무엇인가

즉 failover verification의 핵심은 topology보다 **commit horizon 확인**이다.

## 깊이 들어가기

### 1. commit horizon은 "새 primary가 확실히 가진 마지막 진실 시점"이다

replica 승격 시점에 새 primary는 어떤 지점까지 적용했는지 갖고 있다.

- 그 이전 commit: 비교적 안전한 포함 구간
- 그 이후 commit: 유실 가능 또는 재검증 필요 구간

이 경계가 바로 loss boundary다.

### 2. 최신 replica 승격과 충분한 horizon 확보는 같은 말이 아니다

승격 대상이 가장 최신 replica여도:

- 마지막 몇 초 트랜잭션이 빠져 있을 수 있고
- giant transaction은 partially visible하지 않지만 뒤 트랜잭션만 빠져 있을 수 있고
- external side effect는 이미 나갔는데 DB commit은 새 primary에 없을 수 있다

그래서 "가장 최신"보다 **정확히 어디까지 확정됐는가**가 중요하다.

### 3. failover 뒤엔 손실 가능 구간을 비즈니스 이벤트로 투영해야 한다

DB 위치 차이만 알면 운영자가 바로 움직이기 어렵다.

필요한 해석:

- 어떤 order/payment/user change가 영향받았는가
- outbox/event relay와 commit 순서가 어땠는가
- 외부 결제 승인/웹훅 발송은 이미 일어났는가

즉 commit horizon은 기술 지표이면서 **재무/주문/권한 영향 범위 계산의 기준점**이다.

### 4. verification은 "새 primary 포함 구간"과 "재검토 구간"을 나눠야 한다

추천 절차:

1. promotion 시점의 last applied position 기록
2. old primary의 last durable / last accepted write 경계 확인
3. gap 구간 추정
4. 해당 구간의 비즈니스 row / outbox / side effect를 재검토

핵심은 failover를 binary success/fail로 보지 않고, **확실한 포함 구간과 불확실 구간을 분리**하는 것이다.

### 5. read consistency 문제와 write loss 문제를 섞으면 안 된다

사용자 증상은 비슷할 수 있다.

- "방금 쓴 게 안 보여요"

하지만 원인은 다르다.

- visibility window 문제
- replica lag 문제
- 실제 write loss / horizon gap 문제

commit horizon 문서는 세 번째를 다룬다.  
즉 "안 보인다"가 아니라 **실제로 새 primary에 없는가**를 확인하는 문제다.

### 6. post-failover reconciliation도 horizon 기준으로 잘라야 한다

무조건 전체 데이터를 재검증할 필요는 없다.

더 현실적인 범위:

- failover 직전 N분
- 특정 affected aggregate
- 특정 outbox/event ids

즉 reconciliation 범위도 commit horizon gap에서 역산하는 편이 낫다.

## 실전 시나리오

### 시나리오 1. 결제 승인 직후 failover

외부 결제사는 성공했지만 새 primary에는 payment row가 없다.

이 경우는:

- commit horizon 이후 구간 손실 가능성
- payment provider record와 DB 재조인
- outbox/idempotency key 기준 복구

가 필요하다.

### 시나리오 2. 대량 배치 중 failover

작은 트랜잭션이 여러 개면 일부만 빠졌을 수 있다.  
한 giant transaction이면 통째로 적용 전이거나 적용 후일 가능성이 높다.

즉 write shape에 따라 horizon 해석이 달라진다.

### 시나리오 3. failover 후 read는 정상처럼 보임

visibility는 정상인데 특정 최근 주문만 빠져 있다면, routing 문제가 아니라 commit horizon gap일 수 있다.

## 코드로 보기

```text
post-failover verification
1. new primary last applied position
2. old primary last durable/accepted position
3. uncertain gap interval
4. affected business rows/events
5. replay or manual reconciliation plan
```

```sql
-- 예시 감각: 승격 후 read-only 상태와 topology 확인
SELECT @@read_only, @@super_read_only;
```

```sql
-- outbox / idempotency row를 horizon 주변 범위로 재검토
SELECT *
FROM outbox_event
WHERE created_at >= NOW() - INTERVAL 10 MINUTE;
```

핵심은 특정 SQL보다, promotion 순간의 위치 정보와 비즈니스 row를 연결해 손실 가능 구간을 줄이는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| failover success만 확인 | 빠르다 | 손실 구간을 놓친다 | 비중요 서비스 |
| commit horizon 검증 | loss boundary가 명확해진다 | 운영 절차가 늘어난다 | 주문/결제/권한 데이터 |
| 전체 재검증 | 안전감이 높다 | 비용이 크다 | 영향 범위가 불명확할 때 |
| horizon 기반 부분 reconciliation | 현실적이다 | 위치/이벤트 매핑이 필요하다 | 운영 성숙도가 있을 때 |

## 꼬리질문

> Q: failover 뒤 왜 commit horizon을 확인해야 하나요?
> 의도: topology 전환과 데이터 포함 범위를 분리하는지 확인
> 핵심: 새 primary가 어디까지의 commit을 실제로 포함했는지 알아야 손실 가능 구간을 알 수 있기 때문이다

> Q: stale read와 commit horizon gap은 같은 문제인가요?
> 의도: visibility 문제와 write loss 문제를 구분하는지 확인
> 핵심: 아니다. 전자는 읽기 경로 문제일 수 있고, 후자는 새 primary에 실제로 데이터가 없을 수 있는 문제다

> Q: failover 후 무엇을 재검증 대상으로 삼나요?
> 의도: 기술 위치와 비즈니스 영향 범위를 연결하는지 확인
> 핵심: horizon 이후 uncertain 구간에 해당하는 주문, 결제, outbox, idempotency row를 우선 본다

## 한 줄 정리

failover verification의 핵심은 승격 성공이 아니라, 새 primary가 확실히 포함한 commit horizon과 그 이후 uncertain 구간을 비즈니스 영향 범위로 번역해 재검증하는 것이다.
