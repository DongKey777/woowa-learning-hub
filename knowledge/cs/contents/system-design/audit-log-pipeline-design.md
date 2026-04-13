# Audit Log Pipeline 설계

> 한 줄 요약: 감사 로그 파이프라인은 누가 언제 무엇을 했는지 변경 불가능하게 수집하고, 조회와 규제 대응이 가능하도록 보관하는 시스템이다.

retrieval-anchor-keywords: audit log pipeline, append-only, tamper-evident, compliance, actor action resource, immutable log, retention policy, SIEM, traceability, replay, forensic

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Workflow Orchestration + Saga 설계](./workflow-orchestration-saga-design.md)
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)

## 핵심 개념

Audit log는 단순한 application log가 아니다.  
실전에서는 아래를 만족해야 한다.

- 누가 했는지 actor 추적
- 무엇을 했는지 action 추적
- 어떤 대상에 했는지 resource 추적
- 언제 했는지 timestamp 추적
- 변경 불가능성 또는 tamper evidence
- 긴 보관 기간과 조회 가능성

즉, audit log는 장애 분석용 로그가 아니라, **책임과 증거를 남기는 운영 데이터**다.

## 깊이 들어가기

### 1. 무엇을 audit로 남길 것인가

모든 이벤트를 audit로 남기면 비용이 커진다.  
보통 중요한 건 아래다.

- 권한 변경
- 금전 관련 변경
- 데이터 export
- 관리자 impersonation
- 보안 설정 변경
- 삭제/복구 작업

### 2. Capacity Estimation

예:

- 1,000만 사용자
- 하루 2천만 audit event
- 평균 event 크기 1 KB

그럼 일일 원본량은 약 20 GB이고, 보관/인덱스/replica를 포함하면 더 커진다.  
여기서 핵심은 write QPS보다 retention과 query pattern이다.

### 3. 파이프라인 구조

```text
App Service
  -> Audit Event Producer
  -> Durable Queue / Stream
  -> Normalizer
  -> Immutable Store
  -> Query Index
  -> Export / SIEM
```

흐름:

1. 애플리케이션이 audit event를 생성한다.
2. queue로 보내며 outbox 패턴을 쓸 수 있다.
3. normalizer가 schema를 맞춘다.
4. immutable store에 append-only로 저장한다.
5. 조회용 인덱스를 별도로 만든다.

### 4. Append-only와 tamper evidence

감사 로그는 수정 가능하면 의미가 약해진다.

권장:

- append-only table or object store
- hash chain 또는 batch checksum
- write-once storage 옵션
- 관리자라도 삭제 대신 redaction 이벤트 기록

완전한 불변성을 시스템만으로 보장하기 어렵다면, 적어도 변조 흔적이 남도록 설계해야 한다.

### 5. 데이터 모델

핵심 필드 예:

- event_id
- actor_type
- actor_id
- tenant_id
- action
- resource_type
- resource_id
- before_snapshot
- after_snapshot
- correlation_id
- request_id
- occurred_at
- ip_address

이렇게 해야 나중에 "누가, 언제, 무엇을, 어떤 요청으로"를 복원할 수 있다.

### 6. 조회와 검색

Audit log는 write-heavy지만 조회도 중요하다.

자주 필요한 조회:

- 특정 user의 변경 이력
- 특정 resource의 시간순 변경 내역
- 특정 action의 전체 목록
- 기간별 export

따라서 검색 인덱스와 partitioning이 필요하다.  
이때는 [Search 시스템 설계](./search-system-design.md)와 [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)와 연결해서 생각하면 좋다.

### 7. 보관 정책과 규제

Audit log는 무한정 보관하지 않는다.

- hot storage
- warm archive
- cold archive
- legal hold

삭제보다 보관 정책이 중요하다.  
특히 규제 대응에서는 retention policy가 먼저 정해져야 한다.

## 실전 시나리오

### 시나리오 1: 관리자 권한 변경

문제:

- 운영자가 권한을 바꿨는데 누가 바꿨는지 나중에 알아야 한다

해결:

- admin action을 반드시 audit에 남긴다
- impersonation은 별도 이벤트로 기록한다

### 시나리오 2: 데이터 export

문제:

- 고객 데이터 export는 민감한 작업이다

해결:

- export 시작/완료/실패를 모두 기록한다
- 다운로드 링크와 대상 범위를 남긴다

### 시나리오 3: 사고 조사

문제:

- 데이터가 의도치 않게 삭제되었다

해결:

- correlation id로 요청 체인을 복원한다
- before/after snapshot을 대조한다

## 코드로 보기

```pseudo
function audit(actor, action, resource, payload):
  event = {
    actor: actor,
    action: action,
    resource: resource,
    payload: normalize(payload),
    occurredAt: now()
  }
  queue.publish(event)

function store(event):
  appendOnlyStore.write(event)
  index.write(event.searchKeys)
```

```java
public void record(AuditEvent event) {
    queue.publish(event.normalize());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Inline audit write | 단순하다 | user flow latency 증가 | 작은 시스템 |
| Async queue | 서비스 경로가 가볍다 | eventual consistency | 대부분의 실서비스 |
| Append-only store | 변조 방지에 유리 | 조회 인덱스가 별도 필요 | 컴플라이언스 |
| Full snapshot | 복구가 쉽다 | 저장 비용이 크다 | 중요한 상태 변경 |
| Hash chain | tamper evidence가 좋다 | 구현 복잡도 증가 | 높은 감사 요구 |

핵심은 audit가 단순 로그가 아니라 **법적/운영적 책임을 지탱하는 증거 체계**라는 점이다.

## 꼬리질문

> Q: application log와 audit log는 어떻게 다른가요?
> 의도: 운영 로그와 증거 로그 구분 확인
> 핵심: audit log는 책임 추적과 규제 대응이 목적이다.

> Q: audit log를 수정하면 왜 안 되나요?
> 의도: 불변성과 신뢰성 이해 확인
> 핵심: 변조 가능하면 증거로서 의미가 약해진다.

> Q: sensitive data는 어떻게 다루나요?
> 의도: 보안과 마스킹 감각 확인
> 핵심: 최소 수집, 마스킹, redaction, 접근 통제를 함께 써야 한다.

> Q: search index와 원본 저장소를 왜 분리하나요?
> 의도: write path와 query path 분리 이해 확인
> 핵심: 조회 요구와 보관 요구가 다르기 때문이다.

## 한 줄 정리

Audit log pipeline은 중요한 행위를 append-only로 수집해, 변조 방지와 추적 가능성을 동시에 제공하는 증거 인프라다.

