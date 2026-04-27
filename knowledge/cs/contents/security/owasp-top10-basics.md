# OWASP Top 10 기초: 웹 보안 취약점 열 가지

> 한 줄 요약: OWASP Top 10은 웹 애플리케이션에서 가장 자주 발생하는 보안 취약점 열 가지로, 신입 개발자가 코드를 짤 때 먼저 피해야 할 위험 목록이다.

**난이도: 🟢 Beginner**

관련 문서:

- [SQL 인젝션 기초](./sql-injection-basics.md)
- [XSS와 CSRF 기초](./xss-csrf-basics.md)
- [입력 값 검증 기초](./input-validation-basics.md)
- [네트워크 HTTP 메서드·REST·멱등성](../network/http-methods-rest-idempotency.md)
- [Security 카테고리 README](./README.md)

retrieval-anchor-keywords: owasp top 10 basics, owasp가 뭔가요, 웹 취약점 목록, 보안 취약점 입문, injection attack beginner, broken access control, 인젝션 공격이란, 접근 제어 실패, security misconfiguration, 웹 보안 처음 배우기, owasp 개요, top 10 vulnerability, 취약점부터 어디서 봐야 하나, owasp category, 웹 보안 공부를 시작할 때

## 핵심 개념

OWASP(Open Worldwide Application Security Project)는 웹 보안 연구 비영리 단체다. 4년마다 실제 데이터를 기반으로 가장 위험한 웹 취약점 열 가지를 발표하는데, 이것이 **OWASP Top 10**이다.

입문자가 이 목록을 알아야 하는 이유는 간단하다. 실제 보안 사고의 상당수가 이 열 가지 안에서 나온다. 목록에 익숙해지면 코드를 짤 때 "지금 이 부분이 A01에 해당하지 않나?"라고 스스로 질문할 수 있다.

## 한눈에 보기

| 순위 | 이름 | 한 줄 요약 |
|---|---|---|
| A01 | Broken Access Control | 권한 없는 사람이 데이터에 접근 |
| A02 | Cryptographic Failures | 암호화 없이 민감 데이터 전송·저장 |
| A03 | Injection | 입력을 코드로 실행 (SQL, LDAP 등) |
| A04 | Insecure Design | 보안을 설계 단계에서 고려하지 않음 |
| A05 | Security Misconfiguration | 기본 설정 방치, 불필요한 기능 활성화 |
| A06 | Vulnerable Components | 취약점 있는 라이브러리 사용 |
| A07 | Auth & Session Failures | 인증·세션 관리 결함 |
| A08 | Software Integrity Failures | CI/CD 파이프라인·의존성 무결성 미검증 |
| A09 | Logging/Monitoring Failures | 침해 감지를 위한 로깅·모니터링 부재 |
| A10 | SSRF | 서버가 내부 시스템에 요청을 중계 |

## 상세 분해

### A01: Broken Access Control — 가장 흔한 취약점

사용자 A가 URL을 `/users/1/profile` → `/users/2/profile`로 바꿔서 다른 사람의 정보를 볼 수 있는 경우다. 서버가 "이 URL을 요청한 사람이 해당 자원의 주인인지" 확인하지 않을 때 발생한다.

### A02: Cryptographic Failures

HTTP(암호화 없음)로 비밀번호를 전송하거나, DB에 비밀번호를 평문으로 저장하는 경우다. 전송 구간에는 HTTPS, 저장 시에는 bcrypt 같은 느린 해시가 필요하다.

### A03: Injection

SQL 인젝션이 가장 대표적이다. 사용자 입력을 검증하지 않고 SQL 쿼리에 그대로 이어붙이면 공격자가 쿼리 구조를 바꿀 수 있다. Prepared Statement로 막는다.

### A05: Security Misconfiguration

개발 편의를 위해 켜둔 H2 콘솔, 스택 트레이스를 그대로 노출하는 에러 응답, 기본 관리자 비밀번호 방치 등이 해당한다. 운영 환경에서는 불필요한 기능을 끄고, 에러 응답에서 내부 구현을 숨겨야 한다.

### A07: Auth & Session Failures

세션 ID가 너무 단순해서 추측 가능한 경우, 로그아웃 후에도 세션이 무효화되지 않는 경우, 비밀번호 재설정 링크가 만료되지 않는 경우 등이 포함된다.

## 흔한 오해와 함정

### "이미 Spring Security를 쓰고 있으니 A01은 안전하다"

Spring Security는 인증(로그인)은 처리하지만, 특정 자원의 소유자 확인은 개발자가 코드로 추가해야 한다. `/users/{id}` 엔드포인트에서 `id`가 현재 로그인한 사용자의 것인지 확인하는 로직은 프레임워크가 자동으로 해주지 않는다.

### "Top 10에 없는 취약점은 신경 안 써도 된다"

Top 10은 가장 흔하고 위험한 것의 목록이지, 보안의 전부가 아니다. 출발점으로 삼되, 도메인에 따라 추가 위협을 분석해야 한다.

### "보안은 나중에 추가하면 된다"

A04(Insecure Design)이 Top 10에 들어간 이유가 이것이다. 설계 단계에서 보안을 고려하지 않으면 나중에 바꾸는 비용이 매우 크다.

## 실무에서 쓰는 모습

Spring Boot API 서버를 만들 때 Top 10을 빠르게 체크하는 실용적인 방법이다.

A01 체크: `@PreAuthorize`나 서비스 레이어에서 "이 사용자가 이 자원의 주인인가?"를 확인하는 코드가 있는가. A03 체크: DB 쿼리가 모두 PreparedStatement 또는 JPA를 사용하는가. A02 체크: 비밀번호는 BCrypt로 저장하고, 외부 통신은 HTTPS인가. A05 체크: `spring.h2.console.enabled=false`, 에러 응답에 스택 트레이스가 포함되지 않는가.

이 네 가지만 먼저 확인해도 가장 흔한 취약점의 상당 부분을 막을 수 있다.

## 더 깊이 가려면

- SQL 인젝션 원리와 방어: [SQL 인젝션 기초](./sql-injection-basics.md)
- XSS와 CSRF 상세: [XSS와 CSRF 기초](./xss-csrf-basics.md)
- 입력 검증 원칙: [입력 값 검증 기초](./input-validation-basics.md)

## 면접/시니어 질문 미리보기

> Q: OWASP Top 10에서 A01이 Broken Access Control인 이유가 무엇인가요?
> 의도: 접근 제어의 중요성을 이해하는지 확인
> 핵심: 인증(로그인)을 통과하더라도 자원의 소유자 확인을 빠뜨리는 경우가 실무에서 매우 흔하다. 프레임워크가 인증은 처리하지만 소유권 확인은 개발자 책임이다.

> Q: Security Misconfiguration(A05)을 예방하기 위해 운영 배포 시 확인할 점은 무엇인가요?
> 의도: 설정 보안 기초를 아는지 확인
> 핵심: H2 콘솔 비활성화, 에러 응답에서 내부 스택 트레이스 숨김, 기본 계정 비밀번호 변경, 불필요한 HTTP 메서드 차단 등이 기본 체크 포인트다.

## 한 줄 정리

OWASP Top 10은 실제 사고에서 가장 자주 나오는 취약점 목록이고, A01(접근 제어 실패)·A03(인젝션)·A05(잘못된 설정)부터 체크하는 것이 백엔드 개발자의 첫 번째 보안 습관이다.
