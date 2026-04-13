# Supply Chain Security / SBOM / Signing Basics

> 한 줄 요약: 공급망 보안은 취약한 패키지를 피하는 것만이 아니라, 무엇이 들어왔는지(SBOM)와 누가 만들었는지(signing/provenance)를 증명하는 체계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)
> - [Key Rotation Runbook](./key-rotation-runbook.md)
> - [Envelope Encryption / KMS Basics](./envelope-encryption-kms-basics.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)

retrieval-anchor-keywords: supply chain security, SBOM, signing, provenance, artifact integrity, dependency pinning, package lock, build attestation, artifact verification, supply chain attack, dependency audit

---

## 핵심 개념

공급망 보안은 외부 의존성이 코드에 들어오는 모든 지점을 다룬다.

- package manager
- build pipeline
- container image
- binary artifact
- generated code

핵심은 "취약한 패키지를 막는 것"만이 아니다.

- 무엇이 들어왔는지 알아야 한다
- 누가 빌드했는지 알아야 한다
- 배포된 artifact가 빌드 결과와 같은지 알아야 한다

그래서 SBOM, 서명, provenance가 같이 간다.

---

## 깊이 들어가기

### 1. SBOM은 재료 목록이다

SBOM(Software Bill of Materials)은 소프트웨어에 어떤 구성요소가 들어 있는지 나열한 목록이다.

알고 싶은 것:

- 어떤 library가 들어갔는가
- 어떤 version인가
- 어떤 transitive dependency가 있는가
- 취약점이 나왔을 때 어디가 영향을 받는가

### 2. signing은 artifact의 무결성을 증명한다

서명은 artifact가 배포 중에 바뀌지 않았음을 확인하는 수단이다.

- package signing
- container image signing
- release signing
- provenance attestation

서명 없이는 누가 만든 빌드인지, 중간에 바뀌지 않았는지 알기 어렵다.

### 3. provenance는 "어디서 왔는가"를 말한다

provenance는 build source와 process를 증명한다.

- 어떤 commit에서 빌드됐는가
- 어떤 CI에서 만들어졌는가
- 어떤 dependency가 사용됐는가

이게 있어야 supply chain attack을 더 잘 막을 수 있다.

### 4. dependency pinning이 중요하다

버전 범위를 넓게 두면 다음 문제가 생긴다.

- 같은 버전이 아닐 수 있다
- 재현 가능한 빌드가 어렵다
- 의도치 않은 업데이트가 들어온다

그래서 lockfile, checksum, digest pinning이 중요하다.

### 5. build pipeline 자체가 공격면이다

의존성만 안전해도 빌드가 오염되면 끝이다.

- CI secret 탈취
- runner compromise
- malicious plugin
- poisoned artifact

그래서 build signing과 접근 제어가 필요하다.

---

## 실전 시나리오

### 시나리오 1: 취약 라이브러리 CVE가 터짐

대응:

- SBOM으로 영향 범위를 찾는다
- lockfile과 실제 배포 artifact를 대조한다
- patch와 rebuild를 한다

### 시나리오 2: 릴리스 artifact가 중간에 바뀜

대응:

- signature verification을 추가한다
- digest pinning을 쓴다
- 배포 전후 artifact hash를 비교한다

### 시나리오 3: CI가 compromised 됨

대응:

- build attestation을 확인한다
- runner secret을 rotate한다
- provenance가 맞지 않는 artifact를 폐기한다

---

## 코드로 보기

### 1. dependency lock 개념

```text
1. package version을 고정한다
2. checksum을 검증한다
3. lockfile을 리뷰한다
4. 빌드 결과 artifact를 서명한다
```

### 2. SBOM 사용 개념

```java
public boolean isAffectedByCve(Sbom sbom, String packageName, String affectedVersionRange) {
    return sbom.contains(packageName, affectedVersionRange);
}
```

### 3. signing 검증 개념

```java
public void verifyArtifact(Artifact artifact, Signature signature) {
    if (!signatureVerifier.verify(artifact.digest(), signature)) {
        throw new SecurityException("artifact signature invalid");
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| dependency pinning | 재현성이 좋다 | 업데이트 관리가 필요하다 | 거의 항상 |
| SBOM 생성 | 영향 분석이 쉽다 | 생성/보관 체계가 필요하다 | 규모가 커질수록 필수 |
| artifact signing | 무결성을 증명한다 | 키 관리가 필요하다 | 배포 파이프라인 |
| provenance attestation | build 신뢰성이 높다 | CI/CD 설계가 필요하다 | 고보안 환경 |

판단 기준은 이렇다.

- 배포 artifact가 어디서 왔는지 증명해야 하는가
- dependency 영향 범위를 빠르게 찾아야 하는가
- build pipeline을 신뢰할 수 있는가
- signing key를 안전하게 관리할 수 있는가

---

## 꼬리질문

> Q: SBOM은 왜 필요한가요?
> 의도: 구성요소 가시성과 영향 범위를 아는지 확인
> 핵심: 어떤 dependency가 들어갔는지 추적하기 위해서다.

> Q: signing은 무엇을 보장하나요?
> 의도: artifact 무결성을 이해하는지 확인
> 핵심: 배포 중 변조되지 않았음을 검증한다.

> Q: provenance는 왜 중요한가요?
> 의도: 빌드 출처의 신뢰를 아는지 확인
> 핵심: 어디서 어떤 과정으로 만들어졌는지 증명하기 때문이다.

> Q: supply chain security가 왜 어려운가요?
> 의도: 패키지뿐 아니라 build pipeline도 공격면이라는 점을 아는지 확인
> 핵심: 의존성과 빌드, 배포가 모두 공격 대상이기 때문이다.

## 한 줄 정리

공급망 보안은 SBOM으로 재료를 보이고 signing/provenance로 결과물이 진짜인지 증명하는 체계다.
