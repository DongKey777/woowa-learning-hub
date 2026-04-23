# One-Time Token Consumption Race / Burn-After-Read

> 한 줄 요약: magic link, password reset, email verification, invite, approval link 같은 일회성 토큰은 "한 번만 쓴다"는 말보다, 동시에 두 번 눌렸을 때 누가 이기고 언제 소모 처리할지 정하는 burn-after-read semantics가 더 중요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Email Magic-Link Threat Model](./email-magic-link-threat-model.md)
> - [Password Reset Threat Modeling](./password-reset-threat-modeling.md)
> - [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)

retrieval-anchor-keywords: one-time token, burn after read, consume token once, token consumption race, magic link race, password reset replay, email verification token, invite token, approval link replay, single-use token semantics

---

## 핵심 개념

일회성 토큰 시스템에서 가장 흔한 오해는 "DB에 used=true만 두면 끝난다"는 것이다.

실제 위험은 경쟁 상황에서 나온다.

- 사용자가 두 번 클릭한다
- 보안 스캐너가 먼저 방문한다
- 공격자와 사용자가 거의 동시에 사용한다
- load balancer retry가 재전송한다

즉 one-time token 보안의 핵심은 one-time이라는 표어보다, consume race에서 어떤 상태 전이가 일어나야 하는가를 정하는 것이다.

---

## 깊이 들어가기

### 1. single-use token은 사실상 작은 state machine이다

최소한 이런 상태를 생각해야 한다.

- issued
- pending-consume
- consumed
- expired
- revoked

문제는 consume 요청이 동시에 들어올 수 있다는 점이다.  
그래서 "처리 후 used=true"는 늦다.

### 2. consume는 side effect보다 먼저 원자적으로 선점해야 한다

좋지 않은 흐름:

1. 토큰 유효성 검사
2. 비밀번호 변경 또는 로그인 처리
3. 마지막에 `used=true`

이러면 두 요청이 동시에 1단계를 통과해 둘 다 성공할 수 있다.

더 나은 흐름:

1. `issued -> pending-consume`를 원자적으로 선점
2. side effect 실행
3. 성공 시 `consumed`, 실패 시 명시적 rollback 또는 retry policy

즉 burn-after-read는 읽고 나서 태우는 것이 아니라, 태울 권리를 먼저 잡고 실행하는 것이다.

### 3. scanner/prefetch와 실제 사용자를 구분해야 한다

magic link와 email verification에서 자주 생긴다.

- 이메일 보안 제품이 링크를 먼저 연다
- preview/prefetch가 GET을 때린다
- 실제 사용자는 나중에 눌렀는데 이미 consumed 상태다

대응:

- first GET은 confirmation page만 띄우고 실제 consume는 POST에서 수행
- browser interaction이나 CSRF token을 붙인다
- scanner user-agent만 믿지 말고 구조적으로 burn 시점을 늦춘다

### 4. consume 실패 후 상태를 어떻게 둘지 정해야 한다

원자적 선점을 했더라도 side effect가 중간에 실패할 수 있다.

예:

- reset token 선점 성공
- 비밀번호 저장 DB timeout
- 사용자에게는 실패 응답

이때 선택지가 필요하다.

- pending-consume 유지 후 재시도 허용
- safe rollback 후 issued 복귀
- revoke 후 support flow로 전환

토큰 종류별로 다를 수 있다.

### 5. one-time token에도 audience와 scope가 있어야 한다

단순 문자열 하나로 두지 말고 최소한 의미를 구분하는 편이 낫다.

- password reset용
- email verify용
- invite accept용
- approval action용

그리고 가능하면:

- user id
- tenant id
- intended action
- return target

을 묶어야 오용을 줄일 수 있다.

### 6. "같은 user니까 두 번 써도 괜찮다"는 생각이 위험하다

예를 들어:

- 비밀번호 reset token이 두 번 쓰여 두 번 다른 비밀번호가 저장
- invite token이 두 번 수락되어 membership 중복 처리
- approval link가 두 번 눌려 중복 side effect 발생

즉 동일 사용자 여부보다, 동일 token의 side effect 중복 여부가 중요하다.

### 7. observability는 double-consume attempt를 따로 봐야 한다

유용한 신호:

- consume conflict count
- scanner-first suspicion
- pending-consume timeout count
- expired-but-clicked count
- duplicate consume by different IP/UA

이 정보가 있어야 UX 버그인지 공격인지 구분할 수 있다.

### 8. recovery UX가 없으면 support가 폭증한다

일회성 토큰은 정상 사용자도 실패하기 쉽다.

- 이미 사용됨
- 만료됨
- scanner가 먼저 소모

그래서 필요하다.

- 새 링크 재발급
- 안전한 error copy
- audit와 support lookup

security와 UX는 같이 설계해야 한다.

---

## 실전 시나리오

### 시나리오 1: magic link를 보안 스캐너가 먼저 열어 사용자는 로그인 실패

문제:

- GET 요청만으로 즉시 consume했다

대응:

- GET은 confirmation only
- 실제 consume는 POST/interaction 단계에서만 수행
- scanner-first suspicion metric을 남긴다

### 시나리오 2: password reset 링크를 두 번 눌러 경쟁적으로 비밀번호가 바뀐다

문제:

- `used=true`가 side effect 뒤에만 기록된다

대응:

- consume 선점을 원자적으로 수행한다
- pending-consume 상태를 둔다
- reset 성공 후에만 consumed로 전이한다

### 시나리오 3: invite token이 side effect 실패 후 영구히 pending 상태로 남는다

문제:

- 실패 rollback 정책이 없다

대응:

- pending timeout과 retry 정책을 둔다
- support 재발급 경로를 만든다
- pending age를 alert한다

---

## 코드로 보기

### 1. token state machine 예시

```java
public enum OneTimeTokenState {
    ISSUED,
    PENDING_CONSUME,
    CONSUMED,
    EXPIRED,
    REVOKED
}
```

### 2. 원자적 consume 선점 개념

```java
public void consume(String tokenId) {
    boolean acquired = tokenRepository.markPendingIfIssued(tokenId);
    if (!acquired) {
        throw new TokenAlreadyUsedException();
    }

    try {
        businessAction.run(tokenId);
        tokenRepository.markConsumed(tokenId);
    } catch (Exception e) {
        tokenRepository.rollbackPending(tokenId);
        throw e;
    }
}
```

### 3. 운영 체크리스트

```text
1. one-time token이 explicit state machine을 가지는가
2. consume 선점이 side effect 전에 원자적으로 일어나는가
3. scanner/prefetch를 구조적으로 분리하는가
4. pending-consume 실패와 timeout recovery가 준비돼 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| simple used flag | 구현이 쉽다 | race와 double consume에 약하다 | 가능하면 피한다 |
| atomic pending-consume | 경쟁 상태에 강하다 | 상태 관리가 복잡하다 | 대부분의 single-use token |
| GET 즉시 consume | 흐름이 단순하다 | scanner/prefetch에 취약하다 | 거의 피해야 한다 |
| confirm-then-POST consume | 실사용자 의도를 더 잘 본다 | 단계가 하나 늘어난다 | magic link, verify link, approval link |

판단 기준은 이렇다.

- side effect 중복이 얼마나 치명적인가
- scanner/prefetch가 개입할 가능성이 큰가
- token consume 실패 후 safe rollback이 가능한가
- support 재발급 UX를 감당할 수 있는가

---

## 꼬리질문

> Q: one-time token에 `used=true`만 두면 왜 부족한가요?
> 의도: 경쟁 상태를 이해하는지 확인
> 핵심: 두 요청이 동시에 유효성 검사를 통과하면 둘 다 side effect를 실행할 수 있기 때문이다.

> Q: 왜 GET 즉시 consume가 위험한가요?
> 의도: scanner/prefetch 문제를 아는지 확인
> 핵심: 실제 사용자 클릭 전에도 링크가 자동 방문돼 토큰이 먼저 소모될 수 있기 때문이다.

> Q: pending-consume 상태가 왜 필요한가요?
> 의도: 원자적 선점과 side effect 분리를 이해하는지 확인
> 핵심: consume 권리를 먼저 확보해 double execution을 막기 위해서다.

> Q: side effect 실패 시 토큰을 다시 issued로 돌려도 되나요?
> 의도: 토큰 종류별 rollback 위험을 생각하는지 확인
> 핵심: 경우에 따라 다르다. replay 위험과 UX를 함께 봐서 rollback/revoke/reissue를 정해야 한다.

## 한 줄 정리

일회성 토큰 보안의 핵심은 "한 번만 쓴다"는 선언이 아니라, consume race에서 누가 먼저 권리를 잡고 실패 시 어떤 상태로 복구할지 정하는 burn-after-read semantics다.
