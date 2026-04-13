# Consent / Preferences Platform 설계

> 한 줄 요약: consent and preferences platform은 마케팅 동의, 데이터 처리 동의, 채널 선호를 버전 관리하고 전파하는 정책 집행 시스템이다.

retrieval-anchor-keywords: consent platform, preferences, opt-in, opt-out, privacy policy, consent version, data processing, channel preference, legal basis, preference propagation

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Notification Preferences Graph 설계](./notification-preferences-graph-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Email Delivery Platform 설계](./email-delivery-platform-design.md)

## 핵심 개념

Consent는 단순한 체크박스가 아니다.  
실전에서는 아래를 함께 다뤄야 한다.

- 법적 동의
- 마케팅 opt-in/opt-out
- 채널별 선호
- purpose limitation
- versioned consent text
- revocation and audit

즉, consent platform은 정책과 증거를 함께 관리하는 데이터 시스템이다.

## 깊이 들어가기

### 1. consent와 preference는 다르다

- consent: 법적/규제상의 허용 여부
- preference: 사용자가 선호하는 전달 방식

마케팅 email을 안 받는 것과, 필수 약관 동의 여부는 다르다.

### 2. Capacity Estimation

예:

- 1,000만 사용자
- user마다 여러 목적/purpose
- 초당 수만 policy check

읽기 path가 매우 중요하고, 변경은 드물지만 민감하다.

봐야 할 숫자:

- consent lookup QPS
- change propagation delay
- audit append rate
- revocation rate
- cache invalidation latency

### 3. 데이터 모델

핵심 엔티티:

- consent record
- purpose
- policy version
- channel preference
- audit event

### 4. versioned text와 proof

동의 문구는 바뀐다.

- versioned legal text
- locale
- timestamp
- source of capture
- IP / device metadata

이 기록이 없으면 "어떤 문구에 동의했는지" 증명할 수 없다.

### 5. propagation

동의 철회는 즉시 전파돼야 한다.

- cache invalidation
- downstream suppression
- email/push stop
- analytics masking

이 부분은 [Notification Preferences Graph 설계](./notification-preferences-graph-design.md)와 [Email Delivery Platform 설계](./email-delivery-platform-design.md)와 연결된다.

### 6. legal basis and jurisdiction

지역마다 정책이 다를 수 있다.

- EU consent
- US opt-out
- tenant-specific policy
- age gate

그래서 consent platform은 geo-aware여야 한다.

### 7. auditability

동의는 법적 증거가 된다.

- 언제 동의했는가
- 어떤 버전의 문구였는가
- 누가 철회했는가

이력은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)로 남겨야 한다.

## 실전 시나리오

### 시나리오 1: 마케팅 동의 철회

문제:

- 사용자가 광고 이메일을 끊고 싶다

해결:

- preference 변경
- downstream suppression
- audit 기록

### 시나리오 2: 동의 문구 변경

문제:

- 약관이 업데이트됐다

해결:

- versioned consent text
- 재동의 필요 여부 판단

### 시나리오 3: tenant별 정책 차이

문제:

- 어떤 고객사는 특정 채널 사용을 금지한다

해결:

- tenant policy override
- user preference는 그 안에서만 유효

## 코드로 보기

```pseudo
function canContact(user, channel, purpose):
  consent = consentStore.get(user.id, purpose)
  preference = preferenceStore.get(user.id, channel)
  return consent.allowed && preference.allowed
```

```java
public boolean canProcess(UserId userId, Purpose purpose) {
    return consentRepository.isAllowed(userId, purpose);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Flat consent table | 단순하다 | version 증거가 약하다 | 작은 서비스 |
| Versioned consent ledger | 감사가 쉽다 | 저장이 늘어난다 | 규제 환경 |
| Cache-first checks | 빠르다 | stale risk | high-QPS contact system |
| Geo-aware policy | 규정 대응이 좋다 | 복잡하다 | 글로벌 서비스 |
| Unified consent+preference | UX가 단순하다 | 법적 의미가 섞일 수 있다 | 저위험 경로 |

핵심은 consent platform이 단순 설정이 아니라 **법적 증거와 전달 정책을 함께 관리하는 집행 시스템**이라는 점이다.

## 꼬리질문

> Q: consent와 preference의 차이는 무엇인가요?
> 의도: 법적 허용과 사용자 선호를 구분하는지 확인
> 핵심: consent는 규제, preference는 UX/전달 방식이다.

> Q: 왜 versioned text가 필요한가요?
> 의도: 증거성 이해 확인
> 핵심: 어떤 문구에 동의했는지 나중에 증명해야 하기 때문이다.

> Q: 철회는 얼마나 빨리 반영돼야 하나요?
> 의도: downstream suppression과 최신성 이해 확인
> 핵심: 가능한 즉시 전파되어야 한다.

> Q: audit log 없이 consent를 운영할 수 있나요?
> 의도: 법적 증거성 이해 확인
> 핵심: 위험이 커서 운영하기 어렵다.

## 한 줄 정리

Consent / preferences platform은 동의와 선호를 버전, 지역, 정책 단위로 관리해 법적 증거와 전달 제어를 함께 제공하는 시스템이다.

