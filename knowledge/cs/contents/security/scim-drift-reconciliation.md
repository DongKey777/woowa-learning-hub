# SCIM Drift / Reconciliation

> 한 줄 요약: SCIM drift는 IdP와 서비스의 사용자, 그룹, 역할 상태가 어긋나는 현상이며, reconciliation은 그 차이를 안전하게 되돌리는 작업이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SCIM Provisioning Security](./scim-provisioning-security.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)

retrieval-anchor-keywords: SCIM drift, reconciliation, identity sync, directory sync, diff, backfill, orphan account, entitlement reconciliation, deprovisioning lag, source of truth

---

## 핵심 개념

SCIM 동기화는 한 번 성공한다고 끝나지 않는다.  
실제 운영에서는 IdP와 서비스 사이에 drift가 쌓인다.

예:

- 그룹은 바뀌었는데 서비스 반영이 늦다
- 계정이 삭제됐는데 로컬엔 남아 있다
- tenant 매핑이 어긋난다
- entitlements가 뒤집힌다

reconciliation은 이런 차이를 찾아서 다시 맞추는 프로세스다.

---

## 깊이 들어가기

### 1. drift는 왜 생기나

- event loss
- retry 실패
- partial update
- manual override
- schema mismatch
- human operation delay

### 2. reconciliation은 수정이 아니라 합의다

무작정 덮어쓰면 안 된다.

- source of truth가 어디인지 확인한다
- 어떤 필드를 IdP가 소유하는지 정한다
- 어떤 필드는 로컬 서비스가 소유하는지 정한다

### 3. orphan account를 잡아야 한다

drift의 흔한 결과는 orphan account다.

- IdP에서는 비활성인데 서비스엔 활성
- tenant membership이 사라졌는데 role이 남아 있음
- support 계정이 영구 권한을 유지함

### 4. backfill과 replay가 필요하다

새 reconciliation 프로세스를 도입하면 과거 drift도 정리해야 한다.

- 과거 event replay
- full snapshot diff
- batch backfill

### 5. dry-run이 중요하다

바로 수정하면 사고가 날 수 있다.

- 먼저 diff를 본다
- 영향을 받는 계정을 집계한다
- 큰 변경은 승인 후 반영한다

---

## 실전 시나리오

### 시나리오 1: IdP 그룹 변경이 서비스에 늦게 반영됨

대응:

- reconciliation job을 주기적으로 돌린다
- drift report를 만든다
- 대량 변경은 알림을 보낸다

### 시나리오 2: 퇴사자 계정이 서비스에 남음

대응:

- orphan account를 찾아 비활성화한다
- session revoke와 refresh revoke를 같이 한다
- audit log를 남긴다

### 시나리오 3: tenant 매핑 drift가 발생함

대응:

- tenant source of truth를 고정한다
- cross-tenant role을 재검증한다
- security test를 추가한다

---

## 코드로 보기

### 1. diff 개념

```java
public DriftReport reconcile(Snapshot idp, Snapshot local) {
    return diffEngine.diff(idp, local);
}
```

### 2. orphan account 정리

```java
public void disableOrphans(List<UserAccount> accounts) {
    for (UserAccount account : accounts) {
        account.disable();
    }
}
```

### 3. dry-run workflow

```text
1. IdP snapshot과 local snapshot을 비교한다
2. drift report를 만든다
3. 위험도 높은 변경만 먼저 본다
4. 승인 후에 실제 반영한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| realtime sync | 반영이 빠르다 | 실패에 민감하다 | 소규모 |
| periodic reconciliation | drift를 잡기 쉽다 | 지연이 생긴다 | 대부분의 운영 |
| snapshot backfill | 대규모 복구가 쉽다 | 비용이 든다 | 초기 도입 |
| manual review | 통제가 강하다 | 느리다 | 고위험 변경 |

판단 기준은 이렇다.

- source of truth가 명확한가
- drift를 자동으로 감지할 수 있는가
- orphan account를 허용할 수 있는가
- deprovisioning 지연이 위험한가

---

## 꼬리질문

> Q: SCIM drift는 왜 생기나요?
> 의도: sync failure와 schema mismatch를 아는지 확인
> 핵심: event loss, retry failure, partial update 때문에 생긴다.

> Q: reconciliation은 무엇인가요?
> 의도: drift를 되돌리는 안전한 절차를 아는지 확인
> 핵심: IdP와 local 상태를 비교해 다시 맞추는 작업이다.

> Q: 왜 dry-run이 중요한가요?
> 의도: 대량 변경의 위험을 아는지 확인
> 핵심: 잘못된 일괄 변경을 막기 위해서다.

> Q: orphan account가 왜 위험한가요?
> 의도: deprovisioning 지연 리스크를 아는지 확인
> 핵심: 권한이 남아서 불필요한 접근이 계속될 수 있기 때문이다.

## 한 줄 정리

SCIM drift reconciliation은 IdP와 서비스 상태의 어긋남을 찾아 안전하게 되돌리는 운영 프로세스다.
