# Metadata Lock Outage Triage, Cancel, and Recovery Runbook

> 한 줄 요약: metadata lock 장애는 "DDL이 느리다"가 아니라, 어떤 long transaction이 cutover를 가로막아 대기열 전체를 늘리고 있는지 찾고, 언제 취소하고 언제 계속할지 결정하는 운영 문제다.

**난이도: 🔴 Advanced**

관련 문서:

- [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [Index Maintenance Window, Rollout, and Fallback Playbook](./index-maintenance-window-rollout-playbook.md)

retrieval-anchor-keywords: metadata lock outage, mdl triage, waiting for table metadata lock, ddl cancel runbook, cutover blocker, metadata lock incident, online ddl outage, backend db recovery

## 핵심 개념

MDL incident의 본질은 보통 이렇다.

- DDL/cutover는 더 강한 metadata lock이 필요함
- long transaction이 그 lock을 못 주고 있음
- 대기 중인 DDL 뒤로 새 요청까지 꼬이기 시작함

즉 문제는 DDL 하나가 느린 게 아니라, **DDL queue가 애플리케이션 트래픽까지 간접적으로 흔들기 시작했다는 것**이다.

## 깊이 들어가기

### 1. 가장 먼저 할 일은 blocker와 blast radius를 함께 본다

초기 질문:

- blocker session은 누구인가
- explicit transaction인가 autocommit statement인가
- pending DDL이 하나인가 여러 개인가
- 애플리케이션 요청까지 지연이 번졌는가

즉 blocker만 찾는 것으로 끝나지 않고, 이미 얼마나 넓게 퍼졌는지 같이 봐야 한다.

### 2. cancel vs continue는 운영 판단이다

항상 DDL을 끝까지 밀어붙이는 게 정답이 아니다.

즉시 cancel이 맞는 경우:

- 앱 p95/p99가 급격히 증가
- pending queue가 쌓이기 시작
- blocker를 안전하게 종료하기 어렵다

continue가 가능한 경우:

- blast radius가 아직 작다
- blocker 정리가 곧 가능하다
- cutover 실패 비용이 더 크다

즉 MDL incident는 기술 이슈이면서 **stop-loss 판단** 문제다.

### 3. blocker kill도 순서가 있다

일반적으로는:

1. long idle transaction
2. 잘못 열린 report/query session
3. batch job

순으로 의심하고, 가장 안전한 blocker부터 정리하는 편이 낫다.

무조건 DDL부터 kill하면:

- 다음 maintenance window를 다시 잡아야 하고
- 복사/동기화 상태를 다시 확인해야 할 수 있다

반대로 무조건 blocker를 kill하면 애플리케이션 의미 있는 작업을 날릴 수도 있다.

### 4. outage 회복 뒤엔 왜 이런 blocker가 생겼는지 남겨야 한다

MDL incident 원인 후보:

- app에서 read transaction을 오래 유지
- 배치가 autocommit off로 긴 SELECT를 수행
- cutover 시각에 운영 report/ETL이 겹침
- maintenance window guardrail 부재

즉 incident 종료 뒤에는 "누가 막았나"보다 **왜 그 세션이 그 시간에 살아 있었나**를 문서화해야 재발이 줄어든다.

### 5. mdl incident는 DDL 도구 문제보다 scheduling 문제일 때가 많다

`gh-ost`, `pt-osc`, direct DDL 무엇을 쓰든:

- cutover 순간
- rename 순간
- metadata swap 순간

은 여전히 MDL에 민감하다.

그래서 tooling보다:

- blocker-free window 보장
- 긴 transaction 감시
- cancel threshold

가 더 중요하다.

### 6. recovery는 "대기 제거"와 "후속 검증" 두 단계다

MDL 대기를 풀었다고 끝나지 않는다.

후속 확인:

- pending metadata lock 없어졌는가
- app latency 정상화됐는가
- cutover 상태가 반쯤 진행된 건 아닌가
- 재시도 시점과 사전 정리 목록이 명확한가

## 실전 시나리오

### 시나리오 1. `ALTER TABLE`이 20분째 `Waiting for table metadata lock`

앱 latency도 같이 올라간다.

대응:

- blocker 탐색
- blast radius 평가
- cancel vs blocker kill 선택

### 시나리오 2. 온라인 스키마 변경 cutover에서만 멈춤

복사는 다 끝났는데 rename/cutover에서 pending.

교훈:

- 데이터량 문제가 아니라 metadata window 문제
- maintenance window와 blocker hygiene가 핵심

### 시나리오 3. 배치 리포트가 매번 DDL window를 깨뜨림

이 경우는 DDL 도구 변경보다:

- report replica 분리
- blocker precheck
- 시간대 재배치

가 더 근본적이다.

## 코드로 보기

```sql
SELECT OBJECT_SCHEMA, OBJECT_NAME, LOCK_TYPE, LOCK_DURATION, LOCK_STATUS, OWNER_THREAD_ID
FROM performance_schema.metadata_locks
WHERE LOCK_STATUS = 'PENDING';
```

```sql
SHOW FULL PROCESSLIST;
```

```text
incident steps
1. find blocker
2. assess app blast radius
3. decide cancel vs continue
4. kill safest blocker or cancel DDL
5. verify pending MDL queue drained
6. document blocker class for next window
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| DDL 즉시 cancel | 앱 보호가 빠르다 | maintenance를 다시 해야 한다 | blast radius가 커질 때 |
| blocker kill | cutover를 살릴 수 있다 | 사용자 작업 손실 가능성 | blocker가 명백할 때 |
| continue 기다림 | 작업은 끝날 수 있다 | outage가 길어질 수 있다 | pending impact가 작을 때 |
| stronger precheck | 재발을 줄인다 | 준비 비용이 든다 | 반복되는 schema changes |

## 꼬리질문

> Q: metadata lock incident에서 첫 질문은 무엇인가요?
> 의도: blocker만이 아니라 blast radius를 같이 보는지 확인
> 핵심: 누가 막고 있는지와 그 대기가 앱으로 얼마나 번졌는지를 함께 봐야 한다

> Q: 항상 blocker를 kill하는 게 맞나요?
> 의도: cancel vs continue가 운영 판단임을 이해하는지 확인
> 핵심: 아니다. business impact와 maintenance state를 같이 봐야 한다

> Q: online DDL 도구를 쓰면 MDL outage가 사라지나요?
> 의도: tooling과 cutover metadata window를 구분하는지 확인
> 핵심: 아니다. cutover 순간은 여전히 MDL에 민감하다

## 한 줄 정리

metadata lock outage 대응의 핵심은 blocker를 찾는 것만이 아니라, 앱 영향이 퍼지기 전에 cancel/continue 기준으로 stop-loss를 걸고 재시도 조건을 남기는 것이다.
