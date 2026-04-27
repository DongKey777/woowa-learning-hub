# 비밀번호 저장 기초: 왜 해시를 써야 하나

> 한 줄 요약: 비밀번호는 복호화할 수 있는 암호화가 아니라, 느린 해시로 저장해야 한다. 평문·MD5·SHA-256 저장은 DB 한 번 유출로 계정 전체가 위험해진다.

**난이도: 🟢 Beginner**

관련 문서:

- [비밀번호 저장: bcrypt / scrypt / argon2](./password-storage-bcrypt-scrypt-argon2.md)
- [Brute Force Protection Basics](./brute-force-protection-basics.md)
- [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: password hashing basics, 비밀번호 저장 방법, 비밀번호 해시, why not encrypt password, plain text password danger, md5 sha256 password storage, bcrypt 왜 써야 하나, salt 이란, rainbow table 공격, password storage beginner, 비밀번호 평문 저장 위험, credential leak, security readme password primer, security beginner route, security primer next step, return to security README, 회원가입 만들 때 비밀번호 저장

## 이 문서 다음에 보면 좋은 문서

- security 입문 문서 안에서 다른 primer를 다시 고르고 싶으면 [Security README 기본 primer 묶음](./README.md#기본-primer)으로 돌아가면 된다.
- bcrypt, scrypt, argon2를 어떤 기준으로 고를지와 cost 파라미터를 더 자세히 보려면 [비밀번호 저장: bcrypt / scrypt / argon2](./password-storage-bcrypt-scrypt-argon2.md)로 이어 가면 된다.
- 비밀번호를 안전하게 저장한 뒤에도 로그인 시도 자체를 어떻게 줄일지 궁금하면 [Brute Force Protection Basics](./brute-force-protection-basics.md)를 같이 보면 된다.

## 핵심 개념

비밀번호를 저장할 때 가장 흔한 실수는 세 가지다.

- **평문 저장**: DB에 `password=1234`로 넣는 경우
- **가역 암호화 저장**: AES 같은 암호화로 저장하는 경우 (복호화 키가 탈취되면 전체 노출)
- **빠른 해시 저장**: MD5, SHA-256 같은 해시를 쓰는 경우

세 방법 모두 DB가 유출됐을 때 실질적으로 비밀번호가 노출된다.

비밀번호 저장의 올바른 원칙은 하나다. **느린 해시를 쓰되, 사용자마다 다른 salt를 섞어서 저장한다.**

## 한눈에 보기

| 저장 방식 | DB 유출 시 위험도 | 이유 |
|---|---|---|
| 평문 | 즉시 노출 | 그냥 읽으면 된다 |
| 가역 암호화 | 키 탈취 시 전체 노출 | 키가 같이 저장되는 경우가 많다 |
| MD5 / SHA-256 | Rainbow table / GPU 크래킹 가능 | 너무 빠르다 |
| bcrypt / argon2 + salt | 크래킹 비용이 매우 높다 | 의도적으로 느리게 설계됨 |

## 상세 분해

### 왜 빠른 해시(MD5, SHA-256)는 부족한가

MD5나 SHA-256은 원래 비밀번호 저장용이 아니다. 초당 수십억 번 계산할 수 있어서, 공격자가 "password123", "1234abcd" 같은 흔한 후보를 빠르게 대입해 원본을 찾아낼 수 있다.

### salt가 뭔가

salt는 해시를 계산하기 전에 비밀번호에 덧붙이는 랜덤 값이다. 사용자마다 다른 salt를 쓰면, 같은 비밀번호를 가진 두 사용자의 해시값이 달라진다. 미리 만들어 둔 rainbow table 공격을 무력화한다.

예를 들면 이렇다.

- salt 없이: `hash("1234")` → 두 사람이 같으면 해시도 같다
- salt 사용: `hash("1234" + "x7rQ8z")` → 각자 다른 결과

### bcrypt는 무엇을 다르게 하나

bcrypt는 내부에서 의도적으로 느리게 동작하도록 설계됐고, salt를 자동으로 포함한다. `work factor`(비용 파라미터)를 높이면 계산이 더 오래 걸린다. 하드웨어가 빨라질수록 이 값을 올려 방어력을 유지한다.

## 흔한 오해와 함정

### "암호화해서 저장하면 안전하다"

암호화는 복호화가 가능하다. 복호화 키가 같은 서버에 있다면, DB가 털릴 때 키도 함께 노출될 위험이 있다. 비밀번호 비교는 저장된 해시와 새로 계산한 해시를 비교하면 되므로, 복호화가 필요하지 않다.

### "SHA-256이면 충분히 안전하다"

SHA-256은 파일 무결성 검증처럼 빠른 해시가 필요한 곳에 적합하다. 비밀번호 저장에는 부적합하다. 속도가 너무 빠르기 때문이다.

### "우리 사용자 수가 적으니 괜찮다"

유출 한 번이면 모든 사용자에게 피해가 간다. 사용자가 10명이든 100만 명이든 저장 방식의 안전성은 같은 기준을 적용해야 한다.

## 실무에서 쓰는 모습

Spring Security에서는 `PasswordEncoder` 인터페이스를 통해 비밀번호 인코딩을 추상화한다. 기본 권장은 `BCryptPasswordEncoder`다.

```java
// 등록 시
String encoded = passwordEncoder.encode(rawPassword);

// 로그인 검증 시
boolean matches = passwordEncoder.matches(rawPassword, storedEncoded);
```

이때 `rawPassword`를 직접 DB에 넣거나 로그에 남기지 않는 것이 중요하다.

## 더 깊이 가려면

- bcrypt / scrypt / argon2 파라미터 심화: [비밀번호 저장: bcrypt / scrypt / argon2](./password-storage-bcrypt-scrypt-argon2.md)
- 인증 흐름 전체: [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md)

## 면접/시니어 질문 미리보기

> Q: 비밀번호를 DB에 저장할 때 어떻게 해야 하나요?
> 의도: 평문/암호화/해시 중 올바른 방식을 아는지 확인
> 핵심: 느린 해시(bcrypt 등) + salt 조합. 복호화가 불필요하므로 가역 암호화는 사용하지 않는다.

> Q: salt를 왜 사용하나요?
> 의도: rainbow table 공격과 salt의 관계를 이해하는지 확인
> 핵심: 사용자마다 다른 salt를 섞으면 동일 비밀번호여도 해시가 달라져 미리 계산된 테이블 공격이 무력화된다.

## 한 줄 정리

비밀번호는 평문도, 빠른 해시도 아닌 salt를 포함한 느린 해시(bcrypt 등)로 저장해야 하며, 복호화가 필요 없으므로 가역 암호화는 쓰지 않는다.
