# Key Rotation Runbook

> 한 줄 요약: key rotation은 새 키를 만드는 작업이 아니라, 발급, 배포, 검증, 중복 허용, 폐기, 감사까지 포함한 운영 절차다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
> - [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md)
> - [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)
> - [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)

retrieval-anchor-keywords: key rotation, runbook, dual validation, key version, grace window, revoke old key, JWKS, signing key, rotation incident, cutover, audit trail, kid rollover, verification failure, rollback decision, failover drill, key compromise recovery

---

## 핵심 개념

key rotation은 보안 사고 대응이자 정기 운영이다.  
새 키를 발급하는 것보다 더 중요한 것은 구 키와 신 키가 잠깐 같이 동작하도록 하되, 어느 시점에 구 키를 끊을지 명확히 하는 것이다.

회전 대상:

- JWT signing key
- API signing secret
- webhook secret
- encryption key
- mTLS key/cert

runbook이 없으면 rotation은 장애가 된다.

---

## 깊이 들어가기

### 1. rotation의 핵심은 cutover다

순서는 대체로 이렇다.

1. 새 키 생성
2. 새 키 배포
3. verifier가 새 키를 신뢰하는지 확인
4. signer가 새 키를 쓰도록 전환
5. old key를 잠깐 중복 허용
6. old key 폐기
7. 감사 로그와 지표 확인

### 2. dual validation 기간이 필요하다

회전 직후에는 새 키와 옛 키를 둘 다 검증해야 하는 순간이 생긴다.

- JWT: JWKS에서 새/옛 key를 함께 노출
- webhook: old/new secret을 짧게 병행
- mTLS: trust bundle overlap

이 기간이 너무 짧으면 실패가 난다.  
너무 길면 보안 이득이 줄어든다.

### 3. issuer와 verifier의 배포 속도가 다르다

서비스마다 rollout 속도가 다르므로, 키 회전은 "모든 곳이 동시에 바뀐다"는 가정으로 하면 안 된다.

- auth server는 빨리 바뀔 수 있다
- edge proxy는 늦을 수 있다
- mobile client는 더 늦다

그래서 key version과 grace window가 필요하다.

### 4. revoke와 rotation은 다르다

- `rotation`: 앞으로 쓸 새 키로 이동
- `revoke`: 이미 유출된 키를 즉시 중단

사고 때는 두 가지를 같이 해야 한다.

### 5. runbook은 사람의 기억을 대체한다

실패하지 않는 rotation은 문서화된 rotation이다.

- 누가 승인하는가
- 어디를 먼저 바꾸는가
- 실패 시 되돌리는가
- 어떤 지표를 보고 cutover 하는가

---

## 실전 시나리오

### 시나리오 1: JWT signing key를 교체해야 함

대응:

- 새 private key 생성
- JWKS에 새 public key 추가
- access token TTL을 짧게 유지
- old key 제거 시점을 예약

### 시나리오 2: webhook secret 유출 가능성이 있음

대응:

- old/new secret 동시 허용 시간을 잡는다
- provider와 receiver를 함께 바꾼다
- replay된 event를 재확인한다

### 시나리오 3: rotation 후 일부 서비스만 실패

대응:

- verifier cache를 확인한다
- bundle propagation을 확인한다
- rollback 여부를 판단한다

---

## 코드로 보기

### 1. key version 선택 개념

```java
public String signWithCurrentKey(String payload) {
    KeyVersion current = keyRegistry.currentSigningKey();
    return signer.sign(current.privateKey(), payload, current.keyId());
}
```

### 2. dual validation 개념

```java
public boolean verify(String token) {
    for (PublicKey key : keyRegistry.verificationKeys()) {
        if (verifier.verifyWith(key, token)) {
            return true;
        }
    }
    return false;
}
```

### 3. runbook 체크리스트

```text
1. 새 키 생성
2. 배포 대상 확인
3. dual validation 가능 여부 확인
4. cutover 시점 공지
5. old key revoke
6. 실패 지표 모니터링
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| planned rotation | 사고를 줄인다 | 운영 작업이 필요하다 | 모든 중요한 키 |
| emergency rotation | 유출 대응이 빠르다 | 급격한 장애 위험 | 사고 대응 |
| dual validation | 무중단 전환이 쉽다 | old key가 잠깐 남는다 | 대부분의 회전 |
| hard cutover | 정리가 빠르다 | 실패 가능성이 높다 | 통제된 환경 |

판단 기준은 이렇다.

- verifier와 signer를 모두 통제할 수 있는가
- key version을 명시적으로 관리하는가
- rollback 기준이 있는가
- audit trail이 남는가

---

## 꼬리질문

> Q: key rotation과 revoke의 차이는 무엇인가요?
> 의도: 전환과 중단의 차이를 이해하는지 확인
> 핵심: rotation은 새 키로 옮기는 것이고 revoke는 옛 키를 끊는 것이다.

> Q: dual validation이 왜 필요한가요?
> 의도: 무중단 전환의 현실을 아는지 확인
> 핵심: 배포 시차 때문에 old와 new를 잠깐 같이 받아야 하기 때문이다.

> Q: runbook이 왜 필요한가요?
> 의도: 운영 절차의 중요성을 아는지 확인
> 핵심: rotation 실패가 장애가 되지 않도록 순서를 고정하기 위해서다.

> Q: signing key rotation에서 가장 먼저 확인할 것은 무엇인가요?
> 의도: 배포와 검증 경계 이해 확인
> 핵심: verifier가 새 key를 언제부터 신뢰하는지다.

## 한 줄 정리

key rotation runbook은 "새 키 배포"가 아니라 "무중단 cutover와 안전한 폐기"를 보장하는 운영 절차다.
