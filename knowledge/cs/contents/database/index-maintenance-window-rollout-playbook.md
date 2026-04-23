# Index Maintenance Window, Rollout, and Fallback Playbook

> 한 줄 요약: 운영 인덱스 작업의 핵심은 `CREATE INDEX` 자체보다, 언제 시작하고 얼마나 throttle하며 lag·lock·write cost를 넘기면 중단할지 정한 maintenance window 설계다.

**난이도: 🔴 Advanced**

관련 문서:

- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Instant DDL vs Inplace vs Copy Algorithms](./instant-ddl-vs-copy-inplace-algorithms.md)
- [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
- [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md)
- [Slow Query Analysis Playbook](./slow-query-analysis-playbook.md)
- [gh-ost / pt-online-schema-change Cutover Precheck Runbook](./gh-ost-pt-osc-cutover-precheck-runbook.md)

retrieval-anchor-keywords: index maintenance window, online index build, index rollout playbook, ddl throttle, replica lag guardrail, index cutover, index fallback, backend db operations

## 핵심 개념

운영에서 인덱스 작업은 보통 "이 인덱스가 필요한가"보다 "이 인덱스를 지금 만들어도 되는가"가 더 어렵다.

인덱스 작업이 흔드는 것:

- write amplification
- replica lag
- metadata lock/cutover
- buffer/cache locality
- plan 변화

그래서 인덱스 작업은 개발 변경이 아니라 **maintenance window 운영 절차**로 보는 편이 안전하다.

## 깊이 들어가기

### 1. window는 "트래픽이 적은 시간"보다 guardrail 세트다

좋은 maintenance window는 시각만 정하는 것이 아니다.

필요한 guardrail:

- 최대 허용 replica lag
- 최대 허용 p95/p99 증가
- lock wait 증가 임계치
- 중단/재개 조건

즉 window는 시간대 이름이 아니라, **실행 중단 기준까지 포함한 운영 계약**이다.

### 2. index build는 source와 replica에 다른 비용을 낸다

source(primary)에서 보이는 비용:

- write path 추가 부담
- background build IO/CPU
- metadata/cutover risk

replica에서 보이는 비용:

- build replay 지연
- apply backlog
- read serving 품질 저하

따라서 인덱스 작업은 primary metric만 보고 성공 판단하면 안 된다.

### 3. build 전 canary 질문이 필요하다

시작 전에 확인할 것:

- 정말 필요한 query shape가 명확한가
- narrower index나 query rewrite로 대체 가능한가
- replica lag budget은 얼마인가
- 실패 시 즉시 중단할 기준이 있는가

즉 create index는 기술 작업이기 전에, **왜 지금 이것을 해야 하는지와 멈출 조건을 합의하는 작업**이다.

### 4. 작업 중엔 "끝까지 버티기"보다 "일찍 중단"이 더 안전할 때가 많다

흔한 실수:

- 이미 lag가 커졌는데도 "조금만 더" 계속 진행
- lock wait이 늘어나도 롤백이 아까워 지속

하지만 인덱스 작업은 운영 전체 SLA를 흔들 수 있으므로:

- lag threshold 초과
- write latency 급증
- lock wait spike

가 오면 일찍 멈추는 편이 더 낫다.

### 5. build 후에도 plan verification 기간이 필요하다

인덱스가 만들어졌다고 끝나지 않는다.

봐야 할 것:

- optimizer가 실제로 그 인덱스를 선택하는가
- 예상치 못한 다른 쿼리가 plan을 바꾸는가
- write cost가 허용 범위 안인가
- old index 정리는 언제 할 것인가

즉 인덱스 rollout은 build와 verify의 두 단계다.

### 6. fallback은 "DROP INDEX" 한 줄보다 넓다

실패 시 fallback 선택지:

- query path를 old SQL로 되돌림
- optimizer hint/invisible index로 노출 최소화
- old index 유지
- 새 index는 남겨 두고 사용만 중단

즉 fallback은 항상 즉시 제거가 아니라, **노출을 줄이고 안정화하는 운영 선택**일 수 있다.

## 실전 시나리오

### 시나리오 1. 새 목록 인덱스 생성 중 replica lag 폭증

대응:

- lag threshold 초과 시 작업 중단
- read routing을 일시 보수적으로 조정
- batch/write burst 시간대 회피 후 재시도

### 시나리오 2. 인덱스는 생성됐는데 optimizer가 안 씀

원인:

- 통계 미갱신
- selectivity 기대와 실제 차이
- query shape mismatch

교훈:

- build 전 hypothesis와 build 후 EXPLAIN verification이 같이 있어야 한다

### 시나리오 3. old index 삭제가 오히려 더 무서움

새 인덱스는 잘 쓰이지만, old index를 지우는 순간 fallback 옵션이 줄어든다.

그래서 cleanup은:

- 충분한 관찰 기간 뒤
- 실제 read/write cost 확인 후
- 분리된 maintenance window에서

하는 편이 안전하다.

## 코드로 보기

```text
maintenance window checklist
1. target query and expected plan documented
2. max replica lag threshold
3. max lock wait threshold
4. p95/p99 error budget
5. stop / resume decision owner
6. post-build verification query set
```

```sql
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS\G
SHOW REPLICA STATUS\G
```

```sql
EXPLAIN ANALYZE
SELECT ...
```

핵심은 DDL 명령문 자체보다, 작업 전 guardrail과 작업 후 검증 세트를 먼저 정하는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 즉시 build | 빠르다 | 운영 충격을 키울 수 있다 | 작은 테이블/낮은 트래픽 |
| maintenance window + guardrail | 안전하다 | 준비가 더 필요하다 | 대부분의 운영 인덱스 작업 |
| post-build long observation | fallback이 남는다 | cleanup이 늦어진다 | 중요한 OLTP 인덱스 |
| aggressive immediate cleanup | 관리가 단순하다 | rollback 여지가 줄어든다 | 영향이 아주 작을 때만 |

## 꼬리질문

> Q: maintenance window에서 가장 중요한 것은 시간대인가요?
> 의도: 시간보다 guardrail을 중시하는지 확인
> 핵심: 시간대도 중요하지만, replica lag/lock wait/p99 같은 중단 기준이 더 중요하다

> Q: index build 후 왜 또 verification 기간이 필요한가요?
> 의도: build와 rollout을 구분하는지 확인
> 핵심: 인덱스가 실제로 쓰이는지와 다른 쿼리/쓰기 비용에 미치는 영향을 확인해야 하기 때문이다

> Q: fallback은 항상 새 인덱스를 바로 지우는 건가요?
> 의도: operational fallback 감각을 보는지 확인
> 핵심: 아니다. query path나 planner exposure만 줄이고 구조물은 남길 수도 있다

## 한 줄 정리

운영 인덱스 작업의 성공은 DDL 실행 여부가 아니라, lag·lock·latency guardrail 안에서 build하고 충분히 검증한 뒤 cleanup까지 별도 창으로 분리할 수 있는지에 달려 있다.
