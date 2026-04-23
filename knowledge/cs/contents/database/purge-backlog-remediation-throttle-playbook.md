# Purge Backlog Remediation, Throttling, and Recovery Playbook

> 한 줄 요약: purge backlog remediation의 핵심은 thread 수를 올리는 것보다, backlog를 만든 long transaction과 write churn을 먼저 줄이고 그다음 throttling과 cleanup capacity를 조절하는 순서를 지키는 것이다.

**난이도: 🔴 Advanced**

관련 문서:

- [Vacuum / Purge / Freeze Risk Triage and Runbook Routing](./vacuum-purge-freeze-risk-runbook-routing.md)
- [Purge Thread Scheduling and Lag Control](./purge-thread-scheduling-lag-control.md)
- [Undo Tablespace Truncation and Purge Debt](./undo-tablespace-truncation-purge-debt.md)
- [Change Buffer, Purge, History List Length](./change-buffer-purge-history-length.md)
- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
- [MVCC History List Growth와 Snapshot Too Old](./mvcc-history-list-snapshot-too-old.md)

retrieval-anchor-keywords: purge backlog remediation, purge debt recovery, history list length incident, innodb_max_purge_lag remediation, undo debt throttle, cleanup backlog playbook, backend db recovery, purge incident routing, history backlog triage

## 핵심 개념

purge backlog가 커졌을 때 흔한 실수는 곧바로 purge thread 수만 올리는 것이다.

하지만 remediation 순서는 보통 다음이 더 안전하다.

1. blocker 제거
2. write churn 완화
3. 필요 시 throttling
4. cleanup capacity 조정
5. backlog 감소 확인

즉 purge backlog 대응은 파라미터 튜닝보다 **부채 발생 속도와 정리 속도의 차이를 다시 줄이는 절차**다.

## 깊이 들어가기

### 1. 먼저 purge가 "못 하는" 상태인지 "못 따라가는" 상태인지 나눈다

두 경우는 다르다.

- 못 하는 상태
  - long transaction/snapshot이 purge를 막음
- 못 따라가는 상태
  - purge는 돌지만 write churn이 더 빠름

첫 번째인데 thread만 늘리면 거의 소용이 없다.

### 2. remediation의 첫 단계는 backlog 생성기를 줄이는 것이다

대표 원인:

- 오래 열린 report transaction
- giant batch update/delete
- soft delete churn
- retry 폭주로 인한 hot row updates

즉 purge backlog 대응은 cleanup subsystem보다 **애플리케이션 write shape**를 먼저 건드릴 때가 많다.

### 3. throttling은 실패가 아니라 의도된 완화 수단일 수 있다

운영 중 선택지:

- foreground DML 속도 일시 제한
- batch pause / chunk 축소
- report job 중단

즉 backlog remediation은 "모든 걸 계속 돌리면서 청소만 더 빨리"가 아니라, **일부 쓰기를 의도적으로 느리게 해서 debt 증가를 멈추는 것**일 수 있다.

### 4. backlog가 줄기 시작했는지 확인하는 지표가 필요하다

대표 지표:

- history list length 추세
- undo tablespace 성장/정체
- long transaction count
- foreground p95/p99 회복 여부

단순 절대값보다 중요한 것은:

- 증가 속도가 꺾였는가
- cleanup 속도가 write churn을 추월했는가

### 5. backlog remediation은 단계적으로 풀어야 한다

복구가 시작됐다고 곧바로 모든 throttling을 풀면:

- write burst가 다시 들어오고
- backlog가 재상승하며
- incident가 재발할 수 있다

따라서:

- history list stabilizes
- blocker 없음
- write churn 정상 범위

를 확인한 뒤 천천히 완화하는 편이 낫다.

### 6. incident 후엔 "왜 debt가 누적되게 허용했나"를 남겨야 한다

재발 방지 질문:

- batch chunk가 너무 컸나
- long transaction 감시가 없었나
- report replica가 필요했나
- soft delete/purge 전략이 잘못됐나
- `innodb_max_purge_lag` guardrail이 충분했나

즉 remediation의 마지막 단계는 postmortem이다.

## 실전 시나리오

### 시나리오 1. history list length가 계속 상승

대응 순서:

- long transaction 탐지
- giant batch pause
- purge thread / lag control 조정

### 시나리오 2. 야간 delete batch 뒤 purge debt 폭증

대응:

- batch chunk 축소
- 다음 window부터 commit frequency 증가
- soft delete 후 async cleanup 구조 재검토

### 시나리오 3. purge thread를 늘렸는데도 효과 없음

원인:

- purge blocker가 여전히 존재

교훈:

- "막힘"과 "capacity 부족"을 분리해야 한다

## 코드로 보기

```sql
SHOW STATUS LIKE 'Innodb_history_list_length';
SHOW ENGINE INNODB STATUS\G
SELECT trx_id, trx_started, trx_state, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;
```

```text
remediation order
1. kill or finish long blocker transaction
2. pause / slow backlog-generating batch
3. enable or tighten purge-related throttling
4. adjust purge capacity
5. verify trend reversal
6. gradually remove throttles
```

```sql
SHOW VARIABLES LIKE 'innodb_max_purge_lag';
SHOW VARIABLES LIKE 'innodb_max_purge_lag_delay';
SHOW VARIABLES LIKE 'innodb_purge_threads';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| blocker 제거 우선 | root cause를 바로 줄인다 | 사용자 작업 영향 가능 | long transaction이 명확할 때 |
| write throttling | backlog 증가를 멈출 수 있다 | 앱 latency가 오른다 | 운영 안정성이 우선일 때 |
| purge thread 증가 | cleanup 속도를 높일 수 있다 | IO/CPU 경쟁이 커진다 | blocker가 없고 capacity가 부족할 때 |
| batch chunk 축소 | 재발을 줄인다 | 총 처리 시간이 늘어난다 | batch-induced backlog |

## 꼬리질문

> Q: purge backlog 대응에서 가장 먼저 할 일은 무엇인가요?
> 의도: thread tuning보다 blocker 제거를 우선하는지 확인
> 핵심: purge를 막는 long transaction이 있는지 먼저 봐야 한다

> Q: throttling은 실패 대응인가요?
> 의도: 의도된 안정화 수단으로 이해하는지 확인
> 핵심: 아니다. backlog 증가를 멈추기 위한 정상적인 완화 전략일 수 있다

> Q: backlog가 줄기 시작했는지는 무엇으로 보나요?
> 의도: 절대값보다 추세를 보는지 확인
> 핵심: history list length와 write churn 대비 cleanup 추세가 꺾였는지 본다

## 한 줄 정리

purge backlog remediation은 cleanup thread를 더 돌리는 작업이 아니라, backlog를 만든 blocker와 write churn을 먼저 줄이고 그다음에 throttling과 purge capacity를 조정해 추세를 되돌리는 절차다.
