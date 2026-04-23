# Abuse Throttling / Runtime Signals

> 한 줄 요약: abuse throttling은 단순 429 정책이 아니라, 어떤 신호로 공격을 판단하고 어떤 단계의 마찰(step-up, cooldown, CAPTCHA, hard block)을 적용할지 정하는 런타임 제어 시스템이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Rate Limiting vs Brute Force Defense](./rate-limiting-vs-brute-force-defense.md)
> - [Anti-Automation / Device Fingerprint Caveats](./anti-automation-device-fingerprint-caveats.md)
> - [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)

retrieval-anchor-keywords: abuse throttling, runtime throttling signals, login abuse defense, credential stuffing signals, step-up throttling, cooldown policy, friction ladder, risk-based throttling, 429 runtime control, abuse signal pipeline

---

## 핵심 개념

abuse throttling의 목표는 단순히 요청 수를 줄이는 것이 아니다.

- 공격 비용을 올리고
- 정상 사용자의 UX 피해는 줄이며
- 현재 신호 강도에 맞는 마찰을 단계적으로 적용하는 것

즉 rate limit은 정적 정책일 수 있지만, abuse throttling은 런타임 신호 기반 제어면에 가깝다.

---

## 깊이 들어가기

### 1. 신호는 단일 카운터보다 조합이 중요하다

유용한 조합:

- per-account 실패율
- per-IP velocity
- ASN/subnet churn
- device/browser continuity
- username enumeration pattern
- OTP resend / verify imbalance

### 2. 같은 429라도 목적이 다르다

- 자원 보호용 429
- credential stuffing 억제용 429
- signup abuse 억제용 429

각각 복구와 alert 기준이 다르다.

### 3. friction ladder가 있어야 한다

예:

1. soft slowdown
2. cooldown delay
3. step-up auth
4. CAPTCHA / challenge
5. hard block

모든 경우에 hard block부터 가면 정상 사용자 피해가 크다.

### 4. abuse signal은 auth signal과 따로 보지 않는 편이 좋다

예:

- login failure spike
- risk signal 상승
- token misuse suspicion
- support impersonation path abuse

이 신호들을 같이 봐야 false positive를 줄일 수 있다.

### 5. enumeration과 credential stuffing은 패턴이 다르다

- enumeration: 많은 username, 낮은 password depth
- stuffing: 많은 username + 특정 credential set 재사용
- brute force: 한 username에 깊은 password 시도

같은 throttle 키를 쓰면 오탐이 커진다.

### 6. step-up은 throttling의 일부가 될 수 있다

특히 회색 신호에서는:

- 바로 hard block 대신
- 로그인/민감 작업에 step-up 요구

가 더 좋은 균형일 수 있다.

### 7. runtime signal은 release/infra drift와도 구분해야 한다

429 증가가 항상 공격은 아니다.

- trust boundary 문제
- captcha provider 장애
- rate limit config bug
- proxy IP parsing bug

그래서 release version, source class, route class 태깅이 중요하다.

### 8. observability는 "얼마나 막았는가"보다 "어떤 단계로 올렸는가"를 보여야 한다

유용한 지표:

- friction ladder transition count
- hard block rate
- step-up triggered by abuse
- false positive recovery rate
- cooldown success/fail ratio

---

## 실전 시나리오

### 시나리오 1: 로그인 실패율이 오르지만 IP가 계속 바뀐다

문제:

- 봇넷 기반 stuffing 가능성

대응:

- per-account + ASN churn을 같이 본다
- step-up과 cooldown을 먼저 적용한다
- 하드 블록은 더 강한 신호 뒤에 쓴다

### 시나리오 2: OTP 재전송 abuse가 늘어나 support가 폭증한다

문제:

- resend와 verify에 같은 throttle이 없다

대응:

- resend/verify를 별도 signal로 본다
- resend imbalance에 cooldown과 challenge를 둔다

### 시나리오 3: hard block을 늘렸더니 정상 사용자가 많이 잠긴다

문제:

- friction ladder 없이 blunt block만 썼다

대응:

- step-up, cooldown, challenge 같은 중간 단계 추가
- false positive recovery 경로를 만든다

---

## 코드로 보기

### 1. friction ladder 예시

```text
low risk -> allow
medium risk -> cooldown
high risk -> step-up or challenge
critical risk -> hard block
```

### 2. 운영 체크리스트

```text
1. abuse 신호가 per-IP 외에 per-account/device/ASN을 포함하는가
2. hard block 전에 intermediate friction 단계가 있는가
3. step-up을 throttling 제어의 일부로 쓸 수 있는가
4. 429 증가를 공격과 config bug로 구분할 telemetry가 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 정적 rate limit | 단순하다 | 분산 공격과 오탐에 약하다 | 기본 방어 |
| risk-based throttling | 유연하다 | tuning이 어렵다 | 대규모 auth surface |
| hard block 중심 | 공격 억제는 강하다 | UX 피해가 크다 | 강한 악성 신호 |
| friction ladder | UX와 보안 균형이 좋다 | 운영 복잡도가 높다 | consumer auth, high volume login |

판단 기준은 이렇다.

- 공격 유형이 stuffing인지 brute force인지 enumeration인지
- false positive 비용이 큰 서비스인지
- step-up/challenge 같은 중간 마찰을 운영할 수 있는지
- abuse telemetry와 auth telemetry를 함께 볼 수 있는지

---

## 꼬리질문

> Q: abuse throttling과 rate limit의 차이는 무엇인가요?
> 의도: 정적 제한과 신호 기반 제어를 구분하는지 확인
> 핵심: abuse throttling은 공격 신호에 따라 마찰 단계를 조절하는 런타임 제어다.

> Q: 왜 hard block만으로는 부족한가요?
> 의도: false positive와 UX 비용을 이해하는지 확인
> 핵심: 회색 신호 구간에서 정상 사용자를 과도하게 잠글 수 있기 때문이다.

> Q: step-up도 throttling의 일부가 될 수 있나요?
> 의도: 인증과 abuse 제어를 연결하는지 확인
> 핵심: 그렇다. 중간 강도의 신호에서 hard block보다 더 좋은 균형일 수 있다.

> Q: 429 증가가 항상 공격인가요?
> 의도: 운영 버그와 공격을 구분하는지 확인
> 핵심: 아니다. config drift, IP parsing bug, provider 장애도 같은 현상을 만들 수 있다.

## 한 줄 정리

Abuse throttling의 핵심은 요청 수를 단순 차단하는 것이 아니라, 공격 신호 강도에 따라 cooldown, step-up, challenge, hard block을 단계적으로 적용하는 런타임 제어를 만드는 것이다.
