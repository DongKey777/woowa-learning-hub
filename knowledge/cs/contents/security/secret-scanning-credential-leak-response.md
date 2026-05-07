---
schema_version: 3
title: Secret Scanning / Credential Leak Response
concept_id: security/secret-scanning-credential-leak-response
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- secret scanning
- credential leak
- revoke
- rotate
aliases:
- secret scanning
- credential leak
- revoke
- rotate
- leak response
- commit history
- CI guard
- log masking
- incident response
- token invalidation
- blast radius
- Secret Scanning / Credential Leak Response
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/secret-management-rotation-leak-patterns.md
- contents/security/jwt-deep-dive.md
- contents/security/api-key-hmac-signature-replay-protection.md
- contents/security/webhook-signature-verification-replay-defense.md
- contents/security/mtls-certificate-rotation-trust-bundle-rollout.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Secret Scanning / Credential Leak Response 핵심 개념을 설명해줘
- secret scanning가 왜 필요한지 알려줘
- Secret Scanning / Credential Leak Response 실무 설계 포인트는 뭐야?
- secret scanning에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Secret Scanning / Credential Leak Response를 다루는 deep_dive 문서다. secret scanning은 유출을 "발견"하는 도구이고, 실제 대응은 회전, 폐기, 영향 범위 식별, 로그 추적까지 이어져야 완성된다. 검색 질의가 secret scanning, credential leak, revoke, rotate처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Secret Scanning / Credential Leak Response

> 한 줄 요약: secret scanning은 유출을 "발견"하는 도구이고, 실제 대응은 회전, 폐기, 영향 범위 식별, 로그 추적까지 이어져야 완성된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md)
> - [Webhook Signature Verification / Replay Defense](./webhook-signature-verification-replay-defense.md)
> - [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)

retrieval-anchor-keywords: secret scanning, credential leak, revoke, rotate, leak response, commit history, CI guard, log masking, incident response, token invalidation, blast radius

---

## 핵심 개념

secret scanning은 코드 저장소, CI 로그, artifact, issue, chat transcript 등에서 credential 패턴을 찾는 통제다.  
하지만 scan 자체는 시작점이고, 진짜 중요한 건 유출 후 대응이다.

핵심 질문:

- 어떤 secret이 노출됐는가
- 어디까지 재사용될 수 있는가
- 즉시 revoke 가능한가
- 영향을 받은 시스템이 무엇인가
- 토큰/키/세션을 어디까지 무효화해야 하는가

즉 leak response는 탐지, triage, containment, rotation, verification의 연속이다.

---

## 깊이 들어가기

### 1. 무엇을 찾아야 하나

흔히 찾는 패턴:

- API key
- DB credential
- signing key
- OAuth client secret
- webhook secret
- private key material
- session token

하지만 regex만으로는 부족하다.

- 허위 양성(false positive)이 많다
- 형식이 다양한 secret은 놓칠 수 있다
- base64 또는 URL-safe 변형이 섞인다

그래서 pattern scan과 context scan을 같이 쓴다.

### 2. 발견 후 가장 먼저 해야 하는 것

첫 번째 반응은 "누가 봤는가"보다 "지금 재사용 가능한가"다.

우선순위:

1. secret 종류 확인
2. blast radius 추정
3. revoke 가능 여부 확인
4. rotation 계획 수립
5. 관련 세션/토큰 폐기

### 3. commit history와 artifact가 더 위험할 수 있다

한 번 삭제했다고 끝나지 않는다.

- git history에 남아 있을 수 있다
- CI artifact에 남아 있을 수 있다
- cache, build log, backup에 남아 있을 수 있다

즉 "현재 코드에 없다"는 사실만으로는 충분하지 않다.

### 4. 대응은 secret 종류별로 달라야 한다

- API key: issuer에서 폐기하고 새 key 발급
- JWT signing key: 키셋 교체와 JWKS 갱신
- DB password: 비밀 관리자와 앱 롤링 교체
- webhook secret: provider와 receiver 둘 다 전환
- OAuth client secret: client 등록 정보 교체

### 5. 로그 마스킹은 사후가 아니라 사전 통제다

leak response에서 자주 놓치는 점은 로그가 이미 충분히 위험하다는 것이다.

- Authorization header
- Set-Cookie
- query string credential
- exception stack trace

그래서 로그 마스킹은 detection보다 먼저 묶어야 한다.

---

## 실전 시나리오

### 시나리오 1: git commit에 secret이 들어감

대응:

- 해당 secret을 즉시 rotate한다
- git history rewrite가 필요한지 판단한다
- downstream token까지 무효화한다
- 유출 범위를 audit log로 확인한다

### 시나리오 2: CI 로그에 credential이 찍힘

대응:

- secret masking 규칙을 강화한다
- CI runner와 artifact를 정리한다
- 영향을 받은 credential을 교체한다

### 시나리오 3: webhook secret이 저장소에 노출됨

대응:

- provider와 receiver 모두에서 새 secret을 배포한다
- old secret은 overlap window 후 폐기한다
- replay 가능성이 있는 event를 다시 확인한다

---

## 코드로 보기

### 1. scan 결과 triage 개념

```java
public LeakResponse triage(SecretFinding finding) {
    SecretKind kind = finding.kind();
    if (kind == SecretKind.SIGNING_KEY || kind == SecretKind.OAUTH_CLIENT_SECRET) {
        return LeakResponse.immediateRotation();
    }
    return LeakResponse.reviewAndRotate();
}
```

### 2. 로그 마스킹 개념

```java
public String mask(String value) {
    if (value == null || value.length() < 8) return "***";
    return value.substring(0, 3) + "***" + value.substring(value.length() - 3);
}
```

### 3. incident checklist

```text
1. leak 발견
2. secret 종류와 사용처 확인
3. revoke / rotate
4. session, token, downstream credential 정리
5. 로그와 artifact 검색
6. 재발 방지 규칙 추가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| regex secret scanning | 빠르다 | 허위 양성이 많다 | 기본 탐지 |
| context-aware scanning | 정확도가 높다 | 설정이 복잡하다 | CI/PR gate |
| pre-commit hook | 빠르게 막는다 | 우회 가능하다 | 개발자 보호 |
| runtime log masking | 유출 면적을 줄인다 | 완전하지 않다 | 운영 필수 |

판단 기준은 이렇다.

- 유출 후 재사용 가능한 credential인가
- 어디까지 퍼졌는지 추적 가능한가
- rotate와 revoke를 얼마나 빨리 할 수 있는가
- 로그와 artifact까지 포함해 검사하는가

---

## 꼬리질문

> Q: secret scanning만으로 충분한가요?
> 의도: 탐지와 대응의 차이를 이해하는지 확인
> 핵심: 아니다. 회전, 폐기, 영향 범위 분석이 함께 필요하다.

> Q: git history에 남은 secret은 왜 위험한가요?
> 의도: 삭제 이후에도 남는 흔적을 아는지 확인
> 핵심: 과거 커밋과 클론본에 계속 남아 있을 수 있다.

> Q: 어떤 secret부터 가장 먼저 회전해야 하나요?
> 의도: blast radius와 즉시성을 아는지 확인
> 핵심: 서명 키, client secret, API key처럼 즉시 재사용되는 것부터다.

> Q: 로그 마스킹이 왜 중요한가요?
> 의도: 운영 로그 자체가 공격면이 될 수 있음을 아는지 확인
> 핵심: 로그가 credential 유출 경로가 될 수 있기 때문이다.

## 한 줄 정리

secret scanning은 유출 발견의 출발점이고, 실제 보안은 즉시 회전과 폐기, 범위 추적으로 완성된다.
