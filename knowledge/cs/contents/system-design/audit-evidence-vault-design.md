# Audit Evidence Vault 설계

> 한 줄 요약: audit evidence vault는 조사, 규제, 분쟁 대응에 필요한 증거를 변조 방지와 장기 보관 규칙 아래 안전하게 저장하는 증거 저장소다.

retrieval-anchor-keywords: audit evidence vault, evidence chain, WORM storage, legal hold, tamper evidence, retention, chain of custody, encrypted archive, incident evidence, compliance vault

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Envelope Encryption / KMS Basics](../security/envelope-encryption-kms-basics.md)
> - [Secrets Distribution System 설계](./secrets-distribution-system-design.md)
> - [Fraud Case Management Workflow 설계](./fraud-case-management-workflow-design.md)
> - [Tenant Billing Dispute Workflow 설계](./tenant-billing-dispute-workflow-design.md)
> - [Session Revocation at Scale](../security/session-revocation-at-scale.md)

## 핵심 개념

audit evidence vault는 일반 로그 저장소가 아니다.  
실전에서는 다음을 함께 만족해야 한다.

- 변조 가능성을 낮춘다
- 증거 체인을 유지한다
- 보관 기간과 legal hold를 다룬다
- 접근 권한과 반출을 통제한다
- 복구와 조회가 가능해야 한다

즉, evidence vault는 사고와 분쟁에서 쓸 수 있는 immutable archive다.

## 깊이 들어가기

### 1. audit log와 evidence vault는 다르다

- audit log: 사건의 흐름을 남긴다
- evidence vault: 그중 증거로 제출할 패키지를 보관한다

증거는 더 엄격한 보관과 봉인을 요구한다.

### 2. Capacity Estimation

예:

- 하루 수천 개 evidence package
- 패키지당 수 MB~수 GB
- 보관 기간 수년

핵심은 ingest보다 retrieval, integrity check, storage cost다.

봐야 할 숫자:

- archive ingest rate
- retrieval latency
- integrity verification time
- retention expiration count
- legal hold count

### 3. evidence package

패키지는 보통 다음을 포함한다.

- source audit logs
- attachments and snapshots
- hash manifest
- case metadata
- chain-of-custody record

### 4. tamper evidence

완전한 불변은 어렵더라도 변조 흔적은 남겨야 한다.

- hash chain
- manifest checksum
- signed archive metadata
- immutable storage policy

이 부분은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 [Envelope Encryption / KMS Basics](../security/envelope-encryption-kms-basics.md)와 연결된다.

### 5. legal hold and retention

보관 정책은 법적 요구를 반영해야 한다.

- standard retention
- legal hold
- purge after expiry
- case-based retention override

삭제가 아니라 보관 종료가 정책의 핵심이다.

### 6. access and chain of custody

증거는 접근이 매우 중요하다.

- 누가 열람했는가
- 누가 내보냈는가
- 어떤 사건에 연결됐는가
- 어떤 버전이 제출됐는가

접근 기록은 반드시 남겨야 한다.

### 7. encrypted archive

민감한 증거는 암호화가 기본이다.

- envelope encryption
- key rotation
- per-tenant or per-case key

이 부분은 [Secrets Distribution System 설계](./secrets-distribution-system-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 보안 사고 조사

문제:

- 누가 어떤 세션으로 접근했는지 제출해야 한다

해결:

- evidence package 구성
- hash manifest 생성
- chain of custody 기록

### 시나리오 2: fraud dispute

문제:

- 거래 분쟁에서 근거를 보관해야 한다

해결:

- raw audit log + 스냅샷 + 메타데이터 봉인

### 시나리오 3: legal hold

문제:

- 특정 사건 자료를 삭제하면 안 된다

해결:

- hold flag
- delete block
- retention override

## 코드로 보기

```pseudo
function archiveEvidence(caseId, artifacts):
  manifest = hashAll(artifacts)
  encrypted = encryptArchive(artifacts, caseKey(caseId))
  vault.store(caseId, encrypted, manifest)

function verifyEvidence(caseId):
  archive = vault.load(caseId)
  return verifyManifest(archive)
```

```java
public EvidencePackage store(CaseId caseId, EvidenceBundle bundle) {
    return vaultRepository.save(caseId, bundle);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Normal object storage | 단순하다 | 변조 통제가 약하다 | 일반 파일 |
| WORM archive | 증거성 좋다 | 유연성이 낮다 | 규제/법무 |
| Encrypted vault | 민감 정보 보호 | key 관리 필요 | 고보안 증거 |
| Hash-chained archive | tamper evidence가 좋다 | 구현 복잡 | 사고 조사 |
| Case-based retention | 관리가 쉽다 | 정책이 복잡 | 운영 중대 사건 |

핵심은 evidence vault가 단순 저장소가 아니라 **체인 오브 커스터디와 장기 보관을 보장하는 증거 인프라**라는 점이다.

## 꼬리질문

> Q: audit log와 evidence vault는 어떻게 다른가요?
> 의도: 로그와 증거의 차이를 아는지 확인
> 핵심: vault는 제출 가능한 증거 패키지를 장기 보관한다.

> Q: 왜 hash manifest가 필요한가요?
> 의도: 변조 검출 이해 확인
> 핵심: 저장 후 내용이 바뀌지 않았음을 확인해야 한다.

> Q: legal hold는 왜 중요한가요?
> 의도: 보관 정책과 규제 이해 확인
> 핵심: 특정 사건 자료는 삭제하면 안 될 수 있다.

> Q: chain of custody는 무엇인가요?
> 의도: 증거 취급의 추적성 이해 확인
> 핵심: 누가 언제 어떤 증거를 다뤘는지 기록하는 것이다.

## 한 줄 정리

Audit evidence vault는 사고와 분쟁에 필요한 증거를 변조 방지, 암호화, 장기 보관, 접근 추적으로 안전하게 보관하는 저장 인프라다.

