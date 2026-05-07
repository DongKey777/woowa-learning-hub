---
schema_version: 3
title: JWKS Rotation Cutover Failure / Recovery
concept_id: security/jwks-rotation-cutover-failure-recovery
canonical: false
category: security
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- JWKS rotation failure
- JWKS cutover failure
- kid miss after rotation
- old key removal failure
aliases:
- JWKS rotation failure
- JWKS cutover failure
- kid miss after rotation
- old key removal failure
- signer cutover rollback
- verifier cache skew
- dual-publish window
- key overlap failure
- JWKS recovery
- compromised kid recovery
- old key republish safety
- JWKS Rotation Cutover Failure / Recovery
symptoms:
- JWKS Rotation Cutover Failure / Recovery 관련 운영 사고나 보안 이상 징후가 발생해 대응 순서가 필요하다
intents:
- troubleshooting
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/jwk-rotation-cache-invalidation-kid-rollover.md
- contents/security/jwt-signature-verification-failure-playbook.md
- contents/security/jwt-jwks-outage-recovery-failover-drills.md
- contents/security/key-rotation-runbook.md
- contents/security/signing-key-compromise-recovery-playbook.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- JWKS Rotation Cutover Failure / Recovery 장애가 나면 복구 순서는?
- JWKS rotation failure 운영 대응 체크리스트가 뭐야?
- JWKS Rotation Cutover Failure / Recovery에서 blast radius를 어떻게 줄여?
- JWKS rotation failure 사고 후 어떤 증거를 남겨야 해?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 JWKS Rotation Cutover Failure / Recovery를 다루는 playbook 문서다. JWKS rotation 실패는 단순 `kid` miss가 아니라 signer cutover, verifier cache age, old key removal timing, region skew가 엇갈리는 운영 사고이며, 새 키 추가와 old key 제거를 별도 단계로 분리한 recovery runbook이 필요하다. 검색 질의가 JWKS rotation failure, JWKS cutover failure, kid miss after rotation, old key removal failure처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# JWKS Rotation Cutover Failure / Recovery

> 한 줄 요약: JWKS rotation 실패는 단순 `kid` miss가 아니라 signer cutover, verifier cache age, old key removal timing, region skew가 엇갈리는 운영 사고이며, 새 키 추가와 old key 제거를 별도 단계로 분리한 recovery runbook이 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md)
> - [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)
> - [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)

retrieval-anchor-keywords: JWKS rotation failure, JWKS cutover failure, kid miss after rotation, old key removal failure, signer cutover rollback, verifier cache skew, dual-publish window, key overlap failure, JWKS recovery, compromised kid recovery, old key republish safety

---

## 핵심 개념

JWKS rotation에서 실제 장애는 "키를 돌린다"는 한 문장보다 훨씬 더 구체적이다.

- signer는 새 `kid`로 전환했다
- 일부 verifier는 아직 old JWKS를 본다
- 다른 일부는 새 key는 보지만 old key를 잃었다
- 모바일/edge/CDN 경로는 더 늦다

즉 회전 실패의 본질은 `key publish`, `signer cutover`, `verifier refresh`, `old key removal` 네 단계를 같은 순간으로 착각하는 데서 나온다.

---

## 깊이 들어가기

### 1. rotation 실패는 보통 두 종류다

- new-key failure: 새 토큰만 깨짐
- old-key removal failure: 기존 유효 토큰이 깨짐

이 둘은 복구 방향이 다르다.

- new-key failure는 signer rollback 또는 overlap 복구가 핵심
- old-key removal failure는 old key republish가 핵심

### 2. dual-publish와 signer cutover는 별도 이벤트여야 한다

안전한 순서:

1. 새 key를 JWKS에 먼저 publish
2. verifier fleet가 새 key를 받을 시간을 기다림
3. signer를 새 key로 cutover
4. 충분한 overlap 후 old key 제거

문제는 1-4를 한 번에 해 버릴 때 생긴다.

### 3. region skew와 cache age를 먼저 봐야 한다

실패 시 가장 먼저 볼 것:

- 어떤 issuer인가
- 어떤 `kid`가 문제인가
- 어떤 region/pod/version이 실패하는가
- cache age 분포가 어떻게 되는가

이걸 보기 전 cache 전면 eviction은 오히려 refresh storm을 만들 수 있다.

### 4. old key 제거는 access token TTL보다 더 늦어야 한다

고려할 값:

- max token lifetime
- verifier rollout lag
- edge/CDN/mobile cache
- clock skew

old key 제거를 너무 빨리 하면 "기존 세션만 깨지는" 조용한 장애가 난다.

### 5. cutover rollback과 key republish는 다른 레버다

- signer rollback: 앞으로 발급할 토큰을 old key로 다시 전환
- old key republish: 이미 발급된 old-token 검증 경로 복구

둘 중 하나만 해서는 복구가 반쪽일 수 있다.

### 6. old key republish는 "old key가 여전히 신뢰 가능한 경우"에만 쓴다

이 문서의 레버들은 cutover failure를 다룰 때 유효하다.

- old key가 단순히 너무 빨리 제거된 경우
- signer cutover 순서가 어긋난 경우
- verifier cache skew가 큰 경우

하지만 old key compromise가 의심되면:

- old key republish 금지
- compromised `kid` reject
- new key publish + session/token revoke로 전환

즉 증상이 비슷해 보여도 `trust loss`가 시작된 순간부터는 [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)로 handoff해야 한다.

### 7. duplicate `kid`나 wrong key publish는 availability보다 integrity incident다

이 경우:

- 추측 금지
- 다른 key brute-force 금지
- 명시적 reject + incident 승격

회전 실패와 key ambiguity는 같은 사고가 아니다.

### 8. observability는 `kid`/cache age/region skew 중심이어야 한다

유용한 필드:

- issuer
- `kid`
- cache age
- refresh reason
- verifier version
- region
- bucket: `kid_miss_new_key`, `old_key_removed_too_early`

### 9. drill은 overlap 실패를 일부러 만들어 봐야 한다

훈련 예:

- signer cutover를 먼저 해서 새 토큰만 깨짐
- old key를 너무 빨리 제거해 기존 세션 깨짐
- 특정 region만 stale cache

---

## 실전 시나리오

### 시나리오 1: 새 로그인만 실패한다

문제:

- 새 `kid`가 verifier에 안 퍼졌다

대응:

- signer rollback 검토
- overlap window 복구
- region별 cache age 확인

### 시나리오 2: 이미 로그인한 사용자만 갑자기 튕긴다

문제:

- old key를 너무 빨리 제거했다

대응:

- old key republish
- removal policy 재계산
- mobile/edge 경로를 포함한 tail을 본다

### 시나리오 3: 일부 pod만 `kid` miss가 난다

문제:

- stale cache skew 또는 rollout skew

대응:

- verifier version별 분포 확인
- issuer 단위 single-flight refresh
- region별 skew가 해소되는지 모니터링

### 시나리오 4: 기존 유효 토큰이 깨져 old key republish를 고민하지만 compromise 정황도 함께 있다

문제:

- 단순 cutover failure처럼 보이지만 old key 자체가 유출됐을 가능성이 있다

대응:

- old key republish를 보류한다
- forged token 가능성을 먼저 분류한다
- compromise suspected면 JWKS cutover 복구가 아니라 compromise playbook으로 승격한다

---

## 코드로 보기

### 1. overlap-aware rotation checklist

```text
1. new key publish
2. verifier adoption 확인
3. signer cutover
4. old key overlap 유지
5. old key remove
```

### 2. 운영 체크리스트

```text
1. new-key failure와 old-key removal failure를 구분하는가
2. signer rollback과 old key republish를 별도 레버로 갖는가
3. old key republish가 "still trusted key"일 때만 허용되는가
4. cache age/region skew를 본 뒤 refresh를 하는가
5. duplicate kid를 availability 문제가 아니라 integrity 문제로 보는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 짧은 overlap | old key 제거가 빠르다 | tail failure 위험이 크다 | verifier fleet가 매우 단순할 때만 |
| 긴 overlap | cutover가 안정적이다 | old key 노출 기간이 길어진다 | mobile/edge path가 긴 환경 |
| signer rollback | 새 로그인 장애를 빨리 줄인다 | old-key 복구와는 별개다 | new-key failure |
| old key republish | 기존 세션 복구가 빠르다 | 제거 정책이 느슨해질 수 있다 | old-key removal failure |

판단 기준은 이렇다.

- 새 토큰이 깨졌는지 기존 토큰이 깨졌는지
- verifier cache skew가 큰지
- edge/mobile path가 긴지
- ambiguity incident가 섞였는지

---

## 꼬리질문

> Q: JWKS rotation 실패에서 가장 먼저 구분해야 할 것은 무엇인가요?
> 의도: new-key failure와 old-key removal failure를 구분하는지 확인
> 핵심: 새 토큰만 깨졌는지, 기존 유효 토큰도 깨졌는지다.

> Q: signer rollback과 old key republish는 왜 다른가요?
> 의도: 발급 경로와 검증 경로를 구분하는지 확인
> 핵심: 하나는 앞으로 발급할 토큰을 바꾸고, 다른 하나는 과거 토큰 검증을 복구한다.

> Q: cache 전면 eviction이 왜 위험할 수 있나요?
> 의도: refresh storm를 이해하는지 확인
> 핵심: verifier fleet가 동시에 JWKS를 두드려 outage를 증폭시킬 수 있기 때문이다.

> Q: old key republish는 언제 금지해야 하나요?
> 의도: cutover failure와 compromise handoff 조건을 구분하는지 확인
> 핵심: old key compromise가 의심되면 republish가 아니라 compromised `kid` reject와 compromise playbook 승격이 맞다.

> Q: duplicate `kid`는 왜 바로 incident인가요?
> 의도: ambiguity와 availability를 구분하는지 확인
> 핵심: verifier가 추측하기 시작하면 trust boundary가 무너지기 때문이다.

## 한 줄 정리

JWKS rotation failure를 잘 다루려면 new key publish, signer cutover, verifier adoption, old key removal을 분리해 보고, old key republish는 "여전히 신뢰 가능한 key"일 때만 쓰며 compromise 신호가 보이면 즉시 다른 playbook으로 넘겨야 한다.
