# Rate Limiting vs Brute Force Defense

> 한 줄 요약: rate limiting은 자원 보호 장치이고, brute force defense는 공격 비용을 올리는 보안 장치다. 둘은 겹치지만 같지 않다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Gateway auth / rate limit chain](../network/api-gateway-auth-rate-limit-chain.md)
> - [Rate Limiter Design](../system-design/rate-limiter-design.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Password Storage: bcrypt / scrypt / Argon2](./password-storage-bcrypt-scrypt-argon2.md)
> - [X-Forwarded-For / X-Real-IP trust boundary](../network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)

retrieval-anchor-keywords: rate limit, brute force, credential stuffing, login throttling, account lockout, bot defense, captcha, MFA, sliding window, token bucket, per-account limit, per-IP limit

---

## 핵심 개념

rate limit은 "얼마나 자주 할 수 있는가"를 제한한다.  
brute force defense는 "정답이 나올 때까지 무차별 시도하는 공격"의 성공 확률과 속도를 낮춘다.

둘은 비슷해 보이지만 중심이 다르다.

- `rate limit`: 시스템 자원, 비용, 공정성 보호
- `brute force defense`: 비밀번호 추측, OTP 폭주, credential stuffing 방어

가장 흔한 실수는 "로그인 API에만 429를 걸면 끝"이라고 생각하는 것이다.  
그렇게 하면 다음 공격은 못 막는다.

- 여러 IP를 쓰는 botnet
- user-agent를 바꾸는 자동화 도구
- 계정 단위가 아닌 username enumeration
- 비밀번호 재설정, OTP, SMS 인증 남용

즉 brute force defense는 rate limit 하나가 아니라 여러 제어를 조합해야 한다.

---

## 깊이 들어가기

### 1. 공격 유형부터 나눠야 한다

brute force라고 뭉뚱그리면 대응이 흔들린다.

- `password guessing`: 한 계정에 대해 여러 비밀번호를 시도
- `credential stuffing`: 유출된 계정/비밀번호 조합을 대량 대입
- `OTP abuse`: 인증 코드 재전송과 검증을 반복
- `account enumeration`: 존재하는 계정을 확인하려고 요청 패턴을 바꿈
- `signup abuse`: 무작위 이메일/전화번호로 가입 폭주를 일으킴

각 공격은 방어점이 다르다.

- password guessing은 계정 단위 실패 카운터가 중요하다
- credential stuffing은 IP뿐 아니라 device, ASN, velocity를 같이 봐야 한다
- OTP abuse는 재전송과 검증 모두에 제한이 필요하다

### 2. rate limit을 어디에 거는가

실무에서는 보통 여러 키를 동시에 쓴다.

- `per IP`
- `per account`
- `per device/session`
- `per subnet or ASN`
- `per API key`
- `per tenant`

IP만 보면 안 되는 이유가 있다.

- NAT 뒤에 많은 사용자가 한 IP를 공유한다
- 공격자는 프록시와 봇넷을 쓸 수 있다
- `X-Forwarded-For` 같은 헤더는 trust boundary 밖에서는 믿을 수 없다

그래서 인증 엔드포인트는 보통 IP와 계정 둘 다 본다.

### 3. brute force defense는 "실패 처리"를 포함한다

방어는 단순 차단이 아니다.

- 점진적 지연
- 일정 실패 후 추가 검증
- CAPTCHA
- MFA 요구
- 계정 잠금
- 알림 발송

하지만 lockout은 조심해야 한다.

- 공격자가 피해자 계정을 일부러 잠그는 denial of service가 가능하다
- 그래서 hard lockout보다 soft slowdown을 먼저 쓰는 경우가 많다

### 4. 응답 순서가 중요하다

보안적으로 좋은 순서는 대체로 이렇다.

1. 요청 형태와 헤더를 빠르게 검증한다
2. rate limit 초과를 확인한다
3. 비싼 password hash 검증으로 들어간다
4. 실패 횟수를 기록한다
5. 필요 시 추가 챌린지를 요구한다

하지만 enumeration을 막으려면 응답 메시지는 최대한 같아야 한다.

- "존재하지 않는 계정입니다"와 "비밀번호가 틀렸습니다"를 구분하지 않는다
- 속도는 다르게 가져가되 메시지는 균일하게 유지한다

### 5. 로그인 방어와 운영 보호는 다르다

로그인은 공격자가 가장 좋아하는 표적이지만, rate limit은 여기만 쓰는 게 아니다.

- 비밀번호 재설정
- 이메일 인증 재전송
- SMS 인증 요청
- search, export, report API
- 파일 다운로드와 대용량 변환 작업

즉 brute force defense는 인증 API만이 아니라 민감한 상태 변경과 고비용 작업에도 들어간다.

---

## 실전 시나리오

### 시나리오 1: botnet이 로그인 brute force를 시도함

문제:

- IP별 제한만 있으면 봇 하나당 몇 번씩 시도한다
- 계정 단위 제한이 없으면 한 사용자에 대한 공격이 계속된다

대응:

- `account + IP + device` 조합으로 실패 카운터를 건다
- 실패가 누적되면 점진적 지연을 넣는다
- 위험 계정에만 MFA를 추가로 요구한다

### 시나리오 2: credential stuffing으로 대량 로그인 실패가 남

문제:

- 여러 계정에 대해 같은 비밀번호 조합이 반복된다

대응:

- 실패 패턴과 유출 비밀번호 리스트를 비교한다
- 계정별 이상 징후가 보이면 비밀번호 변경을 유도한다
- 로그인 성공 직후 세션과 refresh token을 재평가한다

### 시나리오 3: OTP 재전송 API가 폭주한다

문제:

- 재전송 버튼을 무한정 눌러 SMS 비용이 증가한다

대응:

- 재전송 쿨다운을 둔다
- 한 번호당 시도 횟수를 제한한다
- 같은 인증 세션에서만 재전송을 허용한다

---

## 코드로 보기

### 1. Redis 기반 다중 카운터 예시

```java
public LoginResult login(String username, String password, String ip, String deviceId) {
    rateLimiter.assertAllowed("login:ip:" + ip, 20, Duration.ofMinutes(1));
    rateLimiter.assertAllowed("login:user:" + username, 5, Duration.ofMinutes(10));
    rateLimiter.assertAllowed("login:device:" + deviceId, 10, Duration.ofMinutes(10));

    User user = userRepository.findByUsername(username)
        .orElseThrow(() -> new InvalidCredentialsException("invalid credentials"));

    if (!passwordEncoder.matches(password, user.passwordHash())) {
        authFailureTracker.record(username, ip, deviceId);
        throw new InvalidCredentialsException("invalid credentials");
    }

    authFailureTracker.reset(username);
    return sessionIssuer.issue(user);
}
```

### 2. 실패 누적 후 점진적 지연

```java
public Duration penaltyDelay(String username) {
    int failures = authFailureTracker.recentFailures(username);
    if (failures < 3) return Duration.ZERO;
    if (failures < 6) return Duration.ofSeconds(2);
    if (failures < 10) return Duration.ofSeconds(10);
    return Duration.ofMinutes(1);
}
```

### 3. 로그 메시지 규칙

```text
1. 사용자에게는 같은 실패 메시지를 준다
2. 내부 로그에는 rate limit hit, username, ip, device, risk score를 남긴다
3. 민감 값은 마스킹한다
4. 재시도 폭주가 보이면 alert를 보낸다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| per-IP rate limit | 구현이 쉽다 | NAT와 프록시 때문에 정확도가 낮다 | 초기 방어, 공개 API |
| per-account limit | 공격 표적을 직접 억제한다 | enumeration에 쓰이기 쉽다 | 로그인, 비밀번호 재설정 |
| per-device limit | 봇 반복 시도를 줄인다 | fingerprint가 불안정할 수 있다 | 브라우저/앱 기반 서비스 |
| hard lockout | 공격자를 빨리 멈춘다 | 계정 잠금 DoS가 가능하다 | 매우 민감한 계정 |
| soft slowdown + MFA | UX와 보안을 균형 있게 잡는다 | 구현이 더 복잡하다 | 대부분의 실서비스 |

판단 기준은 이렇다.

- 공격자가 한 계정만 노리나
- 여러 계정을 자동화하나
- 계정 잠금이 DoS가 될 수 있나
- 인증 흐름에서 추가 챌린지를 넣을 수 있나

---

## 꼬리질문

> Q: rate limit이 있으면 brute force 방어가 끝나나요?
> 의도: 자원 제어와 공격 방어를 구분하는지 확인
> 핵심: 아니요. 계정 단위, 지연, MFA, enumeration 방어가 같이 필요하다.

> Q: IP 기반 제한만 두면 왜 부족한가요?
> 의도: NAT, 프록시, 봇넷, trust boundary 이해 확인
> 핵심: 한 IP에 많은 사용자가 있거나 공격자가 IP를 바꿀 수 있다.

> Q: hard lockout이 왜 위험할 수 있나요?
> 의도: 보안 기능이 DoS가 되는 경로 이해 확인
> 핵심: 공격자가 계정을 일부러 잠가 사용자 접속을 막을 수 있다.

> Q: 왜 실패 메시지를 통일하나요?
> 의도: account enumeration 방어 이해 확인
> 핵심: 계정 존재 여부를 유추하기 어렵게 만들기 위해서다.

## 한 줄 정리

rate limiting은 트래픽을 다스리는 도구이고, brute force defense는 그 위에 계정 단위 신호와 추가 챌린지를 얹는 보안 전략이다.
