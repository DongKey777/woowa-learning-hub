# Hardware Attestation Policy / Failure Recovery

> 한 줄 요약: hardware-backed key보다 더 어려운 것은 attestation policy 운영이며, attestation 실패를 무조건 fatal로 처리하면 정상 사용자가 대량 차단되고, 너무 느슨하면 신뢰 모델이 무너진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Hardware-Backed Keys / Attestation](./hardware-backed-keys-attestation.md)
> - [Device Binding Caveats](./device-binding-caveats.md)
> - [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)
> - [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
> - [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)

retrieval-anchor-keywords: attestation policy, hardware attestation failure, attestation drift, device attestation outage, attestation recovery, hardware-backed key policy, attestation allowlist, attestation fallback, attestation trust anchor recovery, attestation root rollover, attestation bundle drift, key attestation compromise, device re-enrollment recovery

---

## 핵심 개념

hardware-backed key를 도입하면 다음 단계는 attestation policy다.

- 어떤 attestation을 신뢰할지
- 실패 시 차단할지 완화할지
- 플랫폼별 편차를 어떻게 다룰지

즉 실제 운영 문제는 key storage보다 policy failure에서 더 자주 드러난다.

---

## 깊이 들어가기

### 1. attestation failure는 compromise와 운영 문제를 동시에 닮는다

원인:

- 새 OS/기기 모델 rollout
- vendor chain 문제
- attestation parser bug
- 실제 위조/비정상 device

그래서 failure bucket 분리가 필요하다.

### 2. allowlist drift가 흔한 장애 원인이다

- 루트 체인 누락
- device class 추가 반영 지연
- vendor metadata stale

이런 문제는 정상 사용자를 한꺼번에 막을 수 있다.

### 3. attestation failure bucket을 먼저 나눠야 한다

같은 `attestation failed`라도 복구 레버가 다르다.

- `evidence_missing`: report 자체가 없음, 앱/SDK 누락, permission 문제
- `chain_untrusted`: 새로운 intermediate/root가 bundle에 없음
- `freshness_failed`: nonce, timestamp, challenge binding 불일치
- `policy_mismatch`: OS version, device class, boot state policy가 너무 빡셈
- `compromise_suspected`: cloned key, replayed attestation, impossible reuse 같은 위조 신호

`chain_untrusted`와 `compromise_suspected`를 같은 fatal bucket으로 처리하면:

- 정상 rollout이 compromise처럼 취급되거나
- 반대로 실제 공격이 "일시적인 attestation 오류"로 가려진다

### 4. trust anchor 복구는 attestation에서도 별도 단계다

attestation은 leaf evidence만 보는 문제가 아니다.

- platform root/intermediate
- vendor metadata
- verifier trust bundle
- policy allowlist

이 네 개가 어긋나면 대량 차단이 난다.

안전한 recovery 순서:

1. 새 attestation root/intermediate를 verifier trust bundle에 먼저 추가한다
2. shadow verify로 platform/version별 성공률을 본다
3. 새 chain을 쓰는 cohort를 점진적으로 허용한다
4. old chain을 제거하거나 revoked 상태로 전환한다
5. allowlist와 support runbook을 같이 업데이트한다

즉 attestation 장애는 parser hotfix만으로 끝나지 않고, trust bundle convergence를 같이 봐야 한다.

### 5. high-risk와 low-risk route의 policy를 다르게 둘 수 있다

- high-risk enrollment/signing: stronger attestation 요구
- 일반 login continuity: bounded fallback 가능

모든 경로에 같은 fatal policy를 두지 않는 편이 현실적이다.

### 6. shadow mode가 유용하다

새 attestation policy는 먼저:

- shadow evaluate
- platform/version별 divergence 수집

후에 enforce하는 편이 안전하다.

### 7. key compromise 대응은 attestation verifier outage와 다르다

device key compromise suspected면 "attestation 검증이 안 된다"가 아니라 "기존 디바이스 신뢰를 끊고 새 hardware-backed key로 재등록해야 한다"가 핵심이다.

대응 레버:

- 해당 device credential quarantine
- refresh/session family revoke
- step-up 후 device re-registration 요구
- 새 key 생성 후 fresh attestation으로만 복구

중요한 점:

- verifier bug이면 trust bundle/policy를 고친다
- device key compromise면 old device identity를 더 이상 신뢰하지 않는다

둘을 섞으면 정상 사용자도 불필요하게 재등록시키거나, 반대로 compromise device를 너무 오래 살려 둔다.

### 8. fallback은 "아무거나 허용"이 아니라 제한적 완화여야 한다

예:

- read-only 허용
- step-up 요구
- device re-registration 요구

또한 fallback에는 종료 조건이 있어야 한다.

- 어떤 cohort에만 열렸는가
- 언제 닫는가
- 닫기 전에 support가 무엇을 안내하는가

time-box 없이 열린 attestation fallback은 영구적인 trust downgrade가 되기 쉽다.

### 9. observability는 policy failure와 trust drift를 같이 봐야 한다

유용한 필드:

- attestation root/intermediate fingerprint
- platform / OS version / app version
- failure bucket (`chain_untrusted`, `freshness_failed`, `policy_mismatch`)
- challenge nonce mismatch rate
- re-registration success rate
- fallback applied route / cohort

이런 필드가 없으면 vendor chain 문제와 실제 device cloning을 분리하기 어렵다.

---

## 실전 시나리오

### 시나리오 1: 특정 OS 업데이트 후 attestation failure 급증

대응:

- platform/version bucket 분리
- shadow policy로 영향 범위 확인
- 고위험 route만 유지, 나머지는 제한적 완화

### 시나리오 2: attestation provider chain 문제로 정상 디바이스가 막힘

대응:

- allowlist drift 여부 확인
- emergency policy override는 time-boxed로만 적용

### 시나리오 3: attestation root/intermediate가 교체되었는데 verifier trust bundle이 늦게 반영됨

문제:

- 신규 device는 새 chain을 제출하지만 일부 verifier는 old bundle만 신뢰한다

대응:

- `chain_untrusted`를 platform cohort별로 분리한다
- verifier trust bundle fingerprint 수렴 여부를 먼저 확인한다
- bundle convergence 전에는 route별 bounded fallback만 연다

### 시나리오 4: 특정 device credential이 복제된 정황이 보인다

문제:

- attestation 자체는 통과하지만 nonce replay, impossible reuse, session graph 상 이상징후가 같이 보인다

대응:

- 해당 device key를 quarantine 한다
- 세션/refresh family를 같이 회수한다
- 새 hardware-backed key와 fresh attestation으로만 복구한다

### 시나리오 5: 실제 위조 device와 rollout bug가 섞여 보임

대응:

- misuse signal, platform cohort, app version을 함께 본다

---

## 코드로 보기

### 1. 정책 결과 예시

```text
trusted -> allow
unknown but low-risk -> step-up / degrade
untrusted on high-risk route -> deny
```

### 2. trust-anchor recovery 개념

```text
1. new attestation root publish
2. verifier bundle converge 확인
3. shadow verify로 cohort divergence 점검
4. route별 enforce / fallback 조정
5. old root revoke or remove
```

### 3. compromise vs policy failure 분기

```text
policy/parser/bundle 문제 -> verifier trust/policy repair
device key compromise -> device quarantine + re-enrollment
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| strict fatal attestation | spoofed device를 강하게 막는다 | rollout drift에 취약하다 | 고위험 enrollment/signing |
| route-tiered fallback | 정상 사용자 차단을 줄인다 | trust downgrade가 열릴 수 있다 | 일반 login continuity |
| broad emergency allowlist | 빠른 완화가 가능하다 | 실제 compromise를 숨길 수 있다 | chain drift가 명확할 때만 |
| forced device re-registration | compromised device를 강하게 끊는다 | 사용자 마찰이 크다 | key cloning / replay 의심 |

판단 기준은 이렇다.

- failure가 trust bundle drift인지 device compromise인지 구분됐는가
- route별 risk tier가 정해져 있는가
- fallback을 닫을 종료 조건이 있는가
- 새 attestation chain의 verifier convergence를 볼 수 있는가

---

## 꼬리질문

> Q: attestation failure와 device compromise를 왜 같은 bucket으로 보면 안 되나요?
> 의도: verifier 문제와 device identity 문제를 구분하는지 확인
> 핵심: 하나는 trust bundle/policy를 고치면 되고, 다른 하나는 old device identity를 끊어야 하기 때문이다.

> Q: attestation trust anchor recovery에서 가장 먼저 해야 할 일은 무엇인가요?
> 의도: bundle rollout 순서를 이해하는지 확인
> 핵심: 새 attestation root/intermediate를 verifier trust bundle에 먼저 배포하는 것이다.

> Q: fallback을 열 때 꼭 같이 적어야 하는 것은 무엇인가요?
> 의도: 임시 완화가 영구화되는 위험을 아는지 확인
> 핵심: 대상 cohort, 종료 시각, 복구 후 닫는 조건이다.

> Q: device re-registration은 언제 필요한가요?
> 의도: 단순 policy drift와 key compromise를 구분하는지 확인
> 핵심: device key cloning, replay, impossible reuse처럼 old key 신뢰를 끊어야 할 때다.

## 한 줄 정리

Hardware attestation 운영의 핵심은 attestation failure를 policy drift, trust-bundle lag, 실제 device compromise로 나눠 보고, verifier bundle recovery와 device re-enrollment를 서로 다른 runbook으로 다루는 것이다.
