# Autovacuum Freeze Debt, XID Age, and Wraparound Playbook

> 한 줄 요약: autovacuum freeze debt는 단순 청소 지연이 아니라 transaction ID age가 임계치로 다가오는 문제이며, 늦게 보면 bloat 문제가 아니라 가용성 사고로 번질 수 있다.

**난이도: 🔴 Advanced**

관련 문서:

- [Vacuum / Purge / Freeze Risk Triage and Runbook Routing](./vacuum-purge-freeze-risk-runbook-routing.md)
- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
- [MVCC History List Growth와 Snapshot Too Old](./mvcc-history-list-snapshot-too-old.md)
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

retrieval-anchor-keywords: autovacuum freeze debt, xid age, wraparound prevention, freeze vacuum, vacuum freeze backlog, pg freeze debt, backend postgres operations, relfrozenxid age, anti-wraparound vacuum, freeze risk routing

## 핵심 개념

일반 vacuum debt가 dead tuple과 bloat 중심이라면, freeze debt는 더 직접적으로 안전 문제와 연결된다.

- 오래된 tuple의 XID age 증가
- autovacuum freeze 미진행
- wraparound 방지 압력 증가

즉 freeze debt는 "좀 느려짐"이 아니라, 방치하면 **강한 운영 개입이 필요한 보호 모드**로 갈 수 있는 부채다.

## 깊이 들어가기

### 1. freeze debt는 왜 일반 vacuum debt와 다르게 봐야 하나

dead tuple 정리가 덜 된 것과, XID age가 위험 수준까지 간 것은 의미가 다르다.

- dead tuple 문제
  - 성능, bloat, scan 비용
- freeze debt 문제
  - transaction ID wraparound 회피
  - 테이블 단위 긴급 vacuum 압력

즉 freeze debt는 성능 이슈이면서 **안전 보존 장치**다.

### 2. 큰 테이블과 낮은 churn 테이블이 의외로 freeze debt를 만들 수 있다

오해:

- 많이 바뀌는 테이블만 vacuum이 중요하다

실제로는:

- 매우 큰데 잘 안 바뀌는 테이블
- rarely touched archive-like table

이 freeze age 누적으로 위험해질 수 있다.

왜냐하면 autovacuum가 충분히 자주 지나가지 않거나, freeze 작업이 뒤로 밀릴 수 있기 때문이다.

### 3. 긴 transaction과 maintenance window 충돌이 freeze debt를 악화시킨다

대표 원인:

- 긴 snapshot
- 대형 batch
- autovacuum worker starvation
- IO budget 부족

즉 freeze debt도 결국 workload와 maintenance scheduling의 상호작용이다.

### 4. forensic 질문은 "어느 relation이 위험 age에 가까운가"다

보통 필요한 질문:

- 가장 age가 큰 relation은 무엇인가
- autovacuum가 최근 제대로 돌았는가
- freeze vacuum이 밀리는 이유는 무엇인가
- 지금 성능 저하를 감수하고라도 선제 개입해야 하는가

즉 전체 평균보다 **worst relation age**가 더 중요할 때가 많다.

### 5. remediation은 성능과 safety의 타협이다

선택지는 보통:

- autovacuum tuning
- 수동 vacuum freeze
- 긴 transaction 제거
- maintenance window 확보

freeze debt가 높을수록 "성능 최적화"보다 "wraparound 방지"가 우선순위가 된다.

### 6. freeze debt는 미리 보는 습관이 중요하다

wraparound 압박이 임박한 뒤엔 선택지가 줄어든다.

그래서 운영적으로는:

- age trend
- autovacuum lag
- big cold table 목록

을 평소에 보고, "위험 relation"을 미리 추적하는 편이 낫다.

## 실전 시나리오

### 시나리오 1. 평소 조용한 큰 테이블이 갑자기 문제

archive 성격이라 거의 안 바뀌던 큰 테이블이 freeze debt로 위험 relation이 된다.

교훈:

- change volume이 적다고 안전한 건 아니다

### 시나리오 2. autovacuum는 돌고 있는데 age가 안 줄어듦

원인:

- freeze 목적 작업이 충분히 못 돌고 있거나
- 긴 snapshot이 방해

### 시나리오 3. 운영자는 bloat만 보고 있었음

실제 위험은 wraparound age였다.

이 경우는 성능보다 먼저 보호성 vacuum이 필요하다.

## 코드로 보기

```text
freeze debt checklist
1. highest relation age
2. recent autovacuum activity
3. long-running transaction presence
4. manual freeze window availability
```

```sql
VACUUM (ANALYZE) orders;
```

핵심은 특정 SQL보다, freeze debt를 "cleanup debt의 특수형"이 아니라 별도 가용성 위험으로 다루는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| autovacuum 기본값 유지 | 단순하다 | 큰 relation age를 놓칠 수 있다 | 작은 시스템 |
| freeze debt 별도 관측 | 위험 relation을 빨리 찾는다 | 운영 metric이 늘어난다 | 중요한 PostgreSQL 운영 |
| 수동 vacuum freeze | 위험을 빠르게 낮춘다 | maintenance 비용이 든다 | 위험 age 접근 시 |
| 긴 transaction 억제 | root cause를 줄인다 | 앱/배치 설계 수정이 필요하다 | 대부분의 안정화 |

## 꼬리질문

> Q: freeze debt는 일반 vacuum debt와 무엇이 다른가요?
> 의도: bloat와 wraparound 압박을 구분하는지 확인
> 핵심: freeze debt는 XID age 안전성과 직결되는 더 강한 운영 위험이다

> Q: 잘 안 바뀌는 큰 테이블도 위험할 수 있나요?
> 의도: low churn relation의 freeze 위험을 아는지 확인
> 핵심: 그렇다. autovacuum가 충분히 지나지 않으면 age가 쌓일 수 있다

> Q: freeze debt는 언제 성능보다 safety가 우선인가요?
> 의도: 운영 우선순위를 이해하는지 확인
> 핵심: wraparound 방지 임계에 가까울수록 성능보다 선제 개입이 우선된다

## 한 줄 정리

autovacuum freeze debt는 dead tuple 정리 문제가 아니라 XID age 안전성 문제이므로, 큰 relation age와 긴 transaction을 미리 관찰하고 wraparound 전에 개입해야 한다.
