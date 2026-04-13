# 비밀번호 저장: bcrypt / scrypt / argon2

> 한 줄 요약: 비밀번호는 암호화해서 되돌리는 것이 아니라, 느린 해시로 저장하고 비교해야 한다. 저장 방식이 약하면 DB 유출 한 번으로 계정이 연쇄로 털린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)

---

## 핵심 개념

비밀번호는 복구 가능한 형태로 저장하면 안 된다.  
중요한 건 "원문을 알아내는 것"이 아니라 "입력한 값이 같은지 확인하는 것"이다.

그래서 비밀번호 저장은 다음 원칙을 따른다.

- 원문을 저장하지 않는다
- 빠른 해시(SHA-256 단독 사용 등)를 쓰지 않는다
- 사용자별 salt를 붙인다
- 연산이 느린 KDF를 쓴다
- 가능하면 pepper와 강한 파라미터를 함께 쓴다

대표 선택지:

- `bcrypt`
- `scrypt`
- `argon2id`

`bcrypt`는 오래 검증된 선택이고, `scrypt`와 `argon2id`는 메모리 비용까지 활용해 GPU/ASIC 공격을 더 어렵게 만든다.

---

## 깊이 들어가기

### 1. 해시와 암호화는 다르다

암호화는 복호화가 가능하지만, 비밀번호는 복호화가 가능하면 안 된다.  
그래서 평문을 되돌리는 구조가 아니라, 입력값을 다시 같은 방식으로 계산해 비교한다.

```text
사용자 입력 -> salt 포함 KDF -> 저장된 hash와 비교
```

### 2. salt, pepper, work factor

`salt`는 각 비밀번호마다 다른 랜덤 값이다.

- 같은 비밀번호라도 다른 해시가 나온다
- rainbow table 공격을 막는다

`pepper`는 서비스 측 비밀값이다.

- DB만 털려도 바로 검증하기 어렵게 만든다
- 애플리케이션 비밀 관리가 필요하다

`work factor`는 계산 비용이다.

- 너무 낮으면 공격이 쉬워진다
- 너무 높으면 로그인 지연이 커진다

### 3. 알고리즘 차이

| 알고리즘 | 장점 | 단점 | 적합한 경우 |
|---|---|---|---|
| `bcrypt` | 검증된 구현, 도구 지원이 많다 | 메모리 하드니스가 약하다 | 일반적인 웹 서비스 |
| `scrypt` | 메모리 공격에 강하다 | 파라미터 조정이 까다롭다 | 방어 강도를 더 올리고 싶을 때 |
| `argon2id` | 현대적인 선택, 메모리/CPU 균형이 좋다 | 운영 경험이 덜한 팀에선 파라미터 실수가 잦다 | 새로 설계하는 서비스 |

### 4. 로그인 시 재해시 전략

해시 알고리즘이나 work factor를 바꾸면 기존 사용자 비밀번호를 어떻게 옮길지 정해야 한다.

- 로그인 성공 시 새 알고리즘으로 재해시한다
- `upgradeEncoding()` 같은 메커니즘을 활용한다
- 대량 일괄 재암호화보다 점진적 마이그레이션이 안전하다

---

## 실전 시나리오

### 시나리오 1: DB가 유출됐다

빠른 SHA-256만 저장했다면 오프라인 대입 공격에 매우 취약하다.  
반대로 `argon2id` + salt + 적절한 work factor면 공격 비용이 급격히 올라간다.

### 시나리오 2: 모든 사용자가 같은 비밀번호를 썼다

salt가 없으면 해시가 동일하게 나와서 재사용 여부가 바로 드러난다.  
salt가 있으면 같은 비밀번호도 서로 다른 해시가 된다.

### 시나리오 3: 로그인만 느려진다고 work factor를 낮춤

로그인 지연은 줄지만 공격자도 더 빨라진다.  
운영에서는 latency budget과 공격 비용을 같이 봐야 한다.

### 시나리오 4: 비밀번호를 되찾아야 한다고 요구함

복구 가능한 암호화를 쓰고 싶어지는 순간이 있지만, 비밀번호는 그 대상이 아니다.  
재설정 흐름을 만들어야지 복구를 설계하면 안 된다.

---

## 코드로 보기

### Spring Security의 기본 패턴

```java
@Configuration
public class PasswordConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return PasswordEncoderFactories.createDelegatingPasswordEncoder();
    }
}
```

```java
public class AccountService {
    private final PasswordEncoder passwordEncoder;

    public AccountService(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    public String hashPassword(String rawPassword) {
        return passwordEncoder.encode(rawPassword);
    }

    public boolean matches(String rawPassword, String encodedPassword) {
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }
}
```

### 알고리즘 교체 시 점진적 업그레이드

```java
public void login(String rawPassword, String storedHash) {
    if (!passwordEncoder.matches(rawPassword, storedHash)) {
        throw new IllegalArgumentException("invalid password");
    }

    if (passwordEncoder.upgradeEncoding(storedHash)) {
        String upgraded = passwordEncoder.encode(rawPassword);
        accountRepository.updatePasswordHash(upgraded);
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `bcrypt` | 검증된 표준에 가깝다 | 메모리 방어력이 약하다 | 대부분의 일반 서비스 |
| `scrypt` | 메모리 하드닝이 된다 | 파라미터 관리가 어렵다 | 방어 강도가 더 중요할 때 |
| `argon2id` | 최신 권장 선택지에 가깝다 | 튜닝과 운영 경험이 필요하다 | 새 시스템, 높은 보안 요구 |
| 빠른 해시 | 구현이 쉽다 | 비밀번호 저장에 부적합하다 | 사용하지 않는다 |

핵심 판단 기준은 단순하다.

- DB만 유출됐을 때 버틸 수 있는가
- 로그인 latency budget을 감당할 수 있는가
- 재설계 없이 해시 파라미터를 올릴 수 있는가

---

## 꼬리질문

> Q: SHA-256에 salt를 붙이면 충분하지 않은가?
> 의도: 빠른 해시와 느린 KDF의 차이를 아는지 확인
> 핵심: salt만으로는 brute force 비용을 충분히 올리지 못한다.

> Q: bcrypt, scrypt, argon2id 중 무엇을 고르겠는가?
> 의도: 알고리즘 이름 암기가 아니라 운영 맥락 판단을 보는 질문
> 핵심: 새 설계면 argon2id를 우선 검토하고, 호환성과 팀 경험도 같이 본다.

> Q: pepper를 쓰면 무엇이 좋아지는가?
> 의도: DB 유출과 애플리케이션 비밀 분리 이해 여부 확인
> 핵심: DB만 털렸을 때 즉시 검증을 어렵게 만든다.

## 한 줄 정리

비밀번호는 복구하는 값이 아니라 검증하는 값이므로, salt가 붙은 느린 해시와 점진적 업그레이드 전략으로 저장해야 한다.
