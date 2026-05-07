---
schema_version: 3
title: mTLS Certificate Rotation / Trust Bundle Rollout
concept_id: security/mtls-certificate-rotation-trust-bundle-rollout
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- mTLS
- certificate rotation
- trust bundle
- CA bundle
aliases:
- mTLS
- certificate rotation
- trust bundle
- CA bundle
- SVID
- workload identity
- rolling rollout
- cert expiry
- root CA
- intermediate CA
- trust anchor
- trust bundle recovery
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/service-to-service-auth-mtls-jwt-spiffe.md
- contents/security/secret-management-rotation-leak-patterns.md
- contents/security/signing-key-compromise-recovery-playbook.md
- contents/security/hardware-attestation-policy-failure-recovery.md
- contents/security/https-hsts-mitm.md
- contents/network/tls-loadbalancing-proxy.md
- contents/network/service-mesh-sidecar-proxy.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- mTLS Certificate Rotation / Trust Bundle Rollout 핵심 개념을 설명해줘
- mTLS가 왜 필요한지 알려줘
- mTLS Certificate Rotation / Trust Bundle Rollout 실무 설계 포인트는 뭐야?
- mTLS에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 mTLS Certificate Rotation / Trust Bundle Rollout를 다루는 deep_dive 문서다. mTLS는 연결이 아니라 인증서 생명주기를 운영하는 문제다. 회전, trust bundle 배포, 폐기 타이밍을 따로 설계해야 장애 없이 안전하게 바꿀 수 있다. 검색 질의가 mTLS, certificate rotation, trust bundle, CA bundle처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# mTLS Certificate Rotation / Trust Bundle Rollout

> 한 줄 요약: mTLS는 연결이 아니라 인증서 생명주기를 운영하는 문제다. 회전, trust bundle 배포, 폐기 타이밍을 따로 설계해야 장애 없이 안전하게 바꿀 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
> - [Hardware Attestation Policy / Failure Recovery](./hardware-attestation-policy-failure-recovery.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [Service Mesh, Sidecar Proxy](../network/service-mesh-sidecar-proxy.md)

retrieval-anchor-keywords: mTLS, certificate rotation, trust bundle, CA bundle, SVID, workload identity, rolling rollout, cert expiry, root CA, intermediate CA, trust anchor, trust bundle recovery, CA compromise recovery, bundle convergence, emergency root rollover, mTLS trust anchor incident

---

## 핵심 개념

mTLS는 양방향 TLS이지만, 운영 관점에서는 "서로를 믿는 인증서 집합을 어떻게 안전하게 바꿀 것인가"가 더 어렵다.

중요한 구성요소:

- `leaf certificate`: 실제 workload 또는 client가 쓰는 인증서
- `intermediate CA`: leaf를 발급하는 중간 인증기관
- `root CA` 또는 `trust anchor`: 최종 신뢰 기준
- `trust bundle`: 검증에 필요한 CA 집합
- `rotation`: 만료 전에 새 인증서로 바꾸는 것

문제는 인증서가 한 번에 다 바뀌지 않는다는 점이다.

- 한쪽은 새 인증서를 썼다
- 다른 쪽은 아직 옛 bundle을 쓰고 있다
- sidecar, gateway, app, load balancer가 서로 다른 시점에 바뀐다

즉 mTLS 운영은 인증서 한 장이 아니라 trust topology 전체를 바꾸는 작업이다.

---

## 깊이 들어가기

### 1. leaf rotation만으로는 부족하다

인증서 만료를 피하려면 leaf만 바꾸면 된다고 생각하기 쉽다.  
하지만 실제로는 trust bundle도 같이 바뀔 수 있다.

예:

- 새 root CA로 이동한다
- intermediate를 교체한다
- 일부 workload는 새 chain을 아직 신뢰하지 않는다

그래서 leaf rotation과 trust bundle rollout은 분리해서 계획해야 한다.

### 2. rollout 순서가 중요하다

안전한 순서는 보통 이렇다.

1. 새 root/intermediate를 trust bundle에 먼저 추가한다
2. 모든 검증자가 새 bundle을 신뢰하게 만든다
3. workload에 새 leaf를 배포한다
4. old leaf를 제거한다
5. old root/intermediate를 폐기한다

이 순서를 거꾸로 하면 handshake failure가 난다.

### 3. overlapping validity window가 필요하다

회전 시에는 old와 new를 잠깐 동시에 허용해야 한다.

- old cert가 아직 살아 있는 동안 new cert가 배포된다
- old bundle이 아직 남아 있는 동안 new bundle이 유효하다
- 중간 상태의 연결 실패를 줄인다

하지만 overlap이 길어지면 보안상 좋지 않다.  
그래서 overlap은 짧게, 관찰 가능하게, 자동화해서 가져가야 한다.

### 4. planned rotation과 compromise recovery는 다르다

정기 rotation이면 old chain을 짧게 overlap할 수 있다.  
하지만 CA/intermediate compromise면 old chain을 오래 남기면 안 된다.

즉 compromise 상황에서는:

1. 새 trust anchor를 verifier bundle에 먼저 배포한다
2. leaf를 새 chain으로 재발급한다
3. old compromised chain acceptance를 즉시 줄인다
4. old chain으로 맺어진 long-lived connection, resumption ticket, cached bundle을 정리한다

여기서는 "장애를 줄이기 위한 overlap"보다 "신뢰 상실을 끊는 속도"가 더 중요하다.

### 5. bundle convergence를 보지 않으면 일부 fleet만 오래된 신뢰를 유지한다

trust bundle rollout은 단순 config apply가 아니다.

- sidecar는 새 bundle을 로드했는가
- gateway는 hot reload가 되었는가
- 앱 프로세스는 새 trust store를 reopen했는가
- node agent는 같은 generation/fingerprint를 보고 있는가

즉 "배포했다"와 "실제로 신뢰 경계가 바뀌었다"는 다르다.

### 6. cert expiry는 운영 지표다

만료는 사고가 아니라 예고된 장애다.

- expiry alert를 일찍 낸다
- 남은 수명을 기준으로 경보를 계층화한다
- 자동 회전 실패를 즉시 감지한다

실무에서는 "만료 30일 전", "7일 전", "24시간 전"처럼 단계별 알림을 둔다.

### 7. trust bundle 배포는 코드 배포보다 느릴 수 있다

bundle rollout이 느린 이유:

- sidecar 캐시
- gateway config reload
- node-level agent sync
- env/config map propagation

그래서 인증서 회전 자동화는 인증서 발급만이 아니라 배포 경로까지 포함해야 한다.

### 8. handshake 복구 후에도 long-lived state를 정리해야 한다

특히 다음이 남아 있으면 old chain을 끊었다고 착각하기 쉽다.

- TLS session resumption ticket
- upstream connection pool
- sidecar cached SDS push
- node-local trust store cache

즉 verifier가 새 bundle을 읽어도 기존 세션이 old chain으로 한동안 살아 있을 수 있다.

---

## 실전 시나리오

### 시나리오 1: 새 인증서를 배포했는데 일부 서비스가 handshake 실패

문제:

- 일부 verifier가 새 CA를 아직 신뢰하지 않는다

대응:

- trust bundle을 먼저 배포한다
- rollout 상태를 관찰한 뒤 leaf를 교체한다
- 실패한 node와 proxy의 cache를 확인한다

### 시나리오 2: root CA 교체가 필요함

문제:

- 기존 root를 폐기해야 하는데 모든 workload가 동시에 바뀔 수 없다

대응:

- 새 root를 bundle에 먼저 추가한다
- 충분한 overlap을 둔다
- old root 제거 시점을 명확히 예약한다

### 시나리오 3: intermediate CA compromise가 확인되어 old chain을 빨리 끊어야 함

문제:

- planned overlap을 길게 유지하면 compromised chain acceptance가 남는다

대응:

- verifier fleet에 새 trust bundle generation을 먼저 밀어 넣는다
- workload leaf를 새 chain으로 재발급한다
- old chain acceptance가 남은 proxy/pod를 우선 격리한다
- resumption ticket과 long-lived connection을 짧게 재설정한다

### 시나리오 4: 자동 회전이 동작하지 않아 만료가 다가옴

문제:

- SPIRE나 control plane 장애로 SVID 발급이 멈췄다

대응:

- 만료 경보를 control plane과 workload 둘 다에서 받는다
- 수동 emergency rotation 절차를 문서화한다
- fallback 통신 경로를 별도 마련한다

---

## 코드로 보기

### 1. trust bundle 교체 개념

```java
public class TrustBundleManager {
    public void addIntermediateCa(Certificate ca) {
        trustStore.add(ca);
        trustStore.refresh();
    }

    public void removeExpiredCa(String subject) {
        trustStore.removeBySubject(subject);
        trustStore.refresh();
    }
}
```

### 2. rotation readiness 체크

```java
public boolean isReadyForLeafCutover() {
    return trustBundleDiscoveredByAllVerifiers()
        && metrics.noRecentHandshakeFailures()
        && certIssuer.hasFreshLeafAvailable();
}
```

### 3. rollout 순서 개념

```text
1. 새 CA를 먼저 배포한다
2. 모든 verifier가 새 bundle을 로드했는지 확인한다
3. 새 leaf를 발급한다
4. old leaf를 폐기한다
5. old CA를 제거한다
```

### 4. compromise recovery 개념

```text
1. new trust anchor publish
2. verifier bundle fingerprint converge 확인
3. leaf 재발급
4. old chain acceptance 차단
5. resumption / connection pool / cache flush
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 짧은 leaf rotation | 노출 기간이 짧다 | 발급 자동화가 필요하다 | 거의 항상 |
| root 교체 포함 rotation | 신뢰 체인을 정리할 수 있다 | 운영 복잡도가 크다 | 장기적인 PKI 리셋 |
| broad overlap | 장애가 적다 | 구 버전 신뢰가 오래 남는다 | 대규모 rollout |
| strict cutover | 보안 정리가 빠르다 | handshake 실패 위험이 있다 | 통제된 환경 |
| compromise-driven cutoff | compromised chain을 빨리 끊는다 | bundle convergence가 부족하면 대규모 실패가 난다 | CA/intermediate compromise |

판단 기준은 이렇다.

- 인증서 만료가 예고된 장애인가
- trust bundle을 먼저 깔 수 있는가
- sidecar/gateway/node의 rollout 속도가 같은가
- old chain을 얼마나 오래 허용할 수 있는가

---

## 꼬리질문

> Q: mTLS에서 leaf rotation만 보면 안 되는 이유는 무엇인가요?
> 의도: trust bundle과 leaf의 차이를 이해하는지 확인
> 핵심: 검증하는 쪽의 CA bundle도 같이 바뀌기 때문이다.

> Q: trust bundle rollout을 leaf보다 먼저 해야 하는 이유는 무엇인가요?
> 의도: rollout 순서의 중요성을 아는지 확인
> 핵심: 새 인증서를 검증하지 못하면 handshake가 실패하기 때문이다.

> Q: overlap window가 왜 필요한가요?
> 의도: 무중단 교체의 현실을 이해하는지 확인
> 핵심: 배포가 완전 동시가 아니어서 old와 new를 잠깐 같이 허용해야 한다.

> Q: CA compromise 때도 overlap을 길게 가져가면 되나요?
> 의도: planned rotation과 compromise recovery를 구분하는지 확인
> 핵심: 아니다. compromise면 old chain acceptance를 빨리 끊어야 하므로 bundle convergence와 재발급을 먼저 맞춘 뒤 차단해야 한다.

> Q: cert expiry를 왜 모니터링해야 하나요?
> 의도: 인증서를 운영 지표로 보는지 확인
> 핵심: 만료는 예고된 장애이기 때문이다.

## 한 줄 정리

mTLS 회전과 복구의 핵심은 leaf만 바꾸는 것이 아니라 trust bundle generation, bundle convergence, old chain cutoff를 함께 다뤄 trust topology 전체를 다시 세우는 것이다.
