---
schema_version: 3
title: JWK Rotation / Cache Invalidation / `kid` Rollover
concept_id: security/jwk-rotation-cache-invalidation-kid-rollover
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- JWK
- JWKS
- kid rollover
- kid miss
aliases:
- JWK
- JWKS
- kid rollover
- kid miss
- key rotation
- cache invalidation
- public key cache
- signing key
- verification key
- rotation window
- stale key
- JWKS TTL
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/jwt-deep-dive.md
- contents/security/jwt-signature-verification-failure-playbook.md
- contents/security/jwt-jwks-outage-recovery-failover-drills.md
- contents/security/jwks-rotation-cutover-failure-recovery.md
- contents/security/token-introspection-vs-self-contained-jwt.md
- contents/security/key-rotation-runbook.md
- contents/security/secret-scanning-credential-leak-response.md
- contents/security/session-revocation-at-scale.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- JWK Rotation / Cache Invalidation / `kid` Rollover 핵심 개념을 설명해줘
- JWK가 왜 필요한지 알려줘
- JWK Rotation / Cache Invalidation / `kid` Rollover 실무 설계 포인트는 뭐야?
- JWK에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 JWK Rotation / Cache Invalidation / `kid` Rollover를 다루는 deep_dive 문서다. JWK 회전은 새 키를 JWKS에 올리는 것보다, 검증자 캐시를 언제 깨고 `kid` 기반으로 어떤 키를 신뢰할지 운영하는 문제가 더 어렵다. 검색 질의가 JWK, JWKS, kid rollover, kid miss처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# JWK Rotation / Cache Invalidation / `kid` Rollover

> 한 줄 요약: JWK 회전은 새 키를 JWKS에 올리는 것보다, 검증자 캐시를 언제 깨고 `kid` 기반으로 어떤 키를 신뢰할지 운영하는 문제가 더 어렵다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
> - [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)
> - [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)

retrieval-anchor-keywords: JWK, JWKS, kid rollover, kid miss, key rotation, cache invalidation, public key cache, signing key, verification key, rotation window, stale key, JWKS TTL, refresh storm, verification outage, stale-if-error, known-good key, cutover failure

---

## 핵심 개념

JWK(JSON Web Key)는 JWT 서명 검증에 쓰는 키 표현이다.  
실무에서는 보통 JWKS endpoint에서 public key 집합을 가져와 검증한다.

문제는 키를 한 번만 배포하고 끝낼 수 없다는 점이다.

- 새 signing key가 생긴다
- 옛 key는 아직 만료 전 토큰을 검증해야 한다
- verifier는 JWKS를 캐시한다
- `kid`가 바뀌면 검증 경로도 바뀐다

즉 JWK 회전은 키 발급보다 캐시 무효화와 cutover 타이밍이 핵심이다.

---

## 깊이 들어가기

### 1. `kid`는 어떤 키를 쓸지 알려주는 힌트다

JWT 헤더의 `kid`는 verifier가 여러 public key 중 무엇으로 검증할지 선택하는 데 도움을 준다.

- 같은 issuer가 여러 key를 동시에 운영할 수 있다
- rotation 기간에는 old/new key가 공존한다
- verifier는 `kid`를 보고 후보 key를 고른다

하지만 `kid`만 믿고 검증을 생략하면 안 된다.

### 2. JWKS는 캐시되기 쉽다

JWKS는 네트워크 요청을 아끼려고 캐시되는 경우가 많다.

- 키 조회 비용을 줄인다
- edge/gateway에서 공통 캐시를 쓴다
- mobile/client SDK도 로컬 캐시를 둘 수 있다

문제는 키가 바뀌어도 캐시가 예전 값을 계속 들고 있을 수 있다는 점이다.

그래서 rotation에는 다음이 필요하다.

- JWKS TTL
- force refresh 조건
- stale-while-revalidate 전략
- key removal 시점 조절

### 3. rotation은 추가만이 아니라 제거의 문제다

새 key를 JWKS에 추가하는 것은 쉽다.  
더 어려운 것은 언제 old key를 제거하느냐이다.

- 너무 빨리 제거하면 아직 유효한 토큰이 검증 실패한다
- 너무 늦게 제거하면 공격자가 오래된 key 기반 토큰을 더 오래 쓸 수 있다

그래서 `token TTL + skew + rollout time`을 함께 계산해야 한다.

### 4. verifier cache invalidation을 어떻게 트리거할까

실무 트리거:

- JWKS `Cache-Control` 만료
- `kid` 미스 발생
- rotation event pub/sub
- 관리자가 수동 refresh

그리고 failure path도 중요하다.

- 새 `kid`를 못 찾으면 즉시 JWKS refresh를 시도한다
- refresh 실패 시 fail-closed 또는 안전한 fallback을 선택한다

### 5. multi-tenant / multi-issuer 환경이 더 어렵다

issuer가 여러 개면 cache key도 달라진다.

- issuer별 JWKS
- tenant별 key set
- environment별 key set

cache key가 잘못 섞이면 다른 issuer의 public key로 검증하는 사고가 난다.

---

## 실전 시나리오

### 시나리오 1: 새 JWT가 발급됐는데 일부 서비스에서만 검증 실패

문제:

- signer는 새 key로 전환했다
- 일부 verifier는 오래된 JWKS 캐시를 쓴다

대응:

- 새 key를 JWKS에 먼저 추가한다
- verifier cache refresh를 강제한다
- old key 제거를 늦춘다

### 시나리오 2: `kid` 미스가 대량 발생함

문제:

- rotate 직후 verifier가 새 `kid`를 모른다

대응:

- `kid` miss를 cache refresh 신호로 쓴다
- refresh storm을 막기 위해 backoff와 collapse를 넣는다
- 관측 지표를 남긴다

### 시나리오 3: old key 제거 후 유효 토큰이 깨짐

문제:

- 토큰 TTL과 key removal 시점을 분리해 생각하지 않았다

대응:

- 제거 전에 최대 토큰 수명을 계산한다
- 서비스 배포 지연과 clock skew를 반영한다
- 제거를 운영 runbook으로 관리한다

---

## 코드로 보기

### 1. JWKS cache refresh 개념

```java
public PublicKey resolveKey(String issuer, String kid) {
    KeySet keySet = jwksCache.getOrLoad(issuer);
    PublicKey key = keySet.findByKid(kid);
    if (key != null) {
        return key;
    }

    jwksCache.refresh(issuer);
    return jwksCache.get(issuer).findByKid(kid);
}
```

### 2. rotation window 계산 개념

```text
1. access token 최대 수명을 확인한다
2. clock skew 허용치를 더한다
3. verifier rollout 시간을 더한다
4. old key 제거 시점을 잡는다
```

### 3. cache invalidation 개념

```java
public void onKeyRotationEvent(String issuer) {
    jwksCache.evict(issuer);
    verificationFleet.refreshIssuer(issuer);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| long JWKS TTL | 부하가 적다 | 새 key 반영이 늦다 | 변화가 적은 환경 |
| short JWKS TTL | 반영이 빠르다 | 조회 부하가 늘어난다 | 자주 회전하는 환경 |
| event-driven invalidation | 즉시성이 좋다 | 이벤트 전달 실패를 고려해야 한다 | 대규모 플랫폼 |
| hard cutover | 정리가 빠르다 | 실패 위험이 높다 | 통제된 내부망 |

판단 기준은 이렇다.

- 토큰 TTL이 얼마나 긴가
- verifier 수가 얼마나 많은가
- key rotation이 얼마나 자주 일어나는가
- JWKS 캐시를 강제로 깨울 수 있는가

---

## 꼬리질문

> Q: `kid`는 왜 필요한가요?
> 의도: 여러 키 공존과 검증 선택을 이해하는지 확인
> 핵심: 어떤 public key로 검증할지 식별하기 위해서다.

> Q: JWKS 캐시가 위험할 수 있는 이유는 무엇인가요?
> 의도: stale key 문제를 아는지 확인
> 핵심: 새 key를 못 보고 오래된 key를 계속 쓸 수 있기 때문이다.

> Q: old key는 언제 제거해야 하나요?
> 의도: 토큰 TTL과 rollout 시간을 연결하는지 확인
> 핵심: 남아 있는 유효 토큰이 모두 만료된 뒤다.

> Q: `kid` 미스가 났을 때 어떻게 해야 하나요?
> 의도: 자동 refresh와 장애 대응을 이해하는지 확인
> 핵심: JWKS를 새로 가져오고, 필요 시 보수적으로 거부한다.

## 한 줄 정리

JWK 회전의 핵심은 새 키 추가가 아니라 `kid` 기반 검증과 JWKS 캐시 무효화를 안전하게 운영하는 것이다.
