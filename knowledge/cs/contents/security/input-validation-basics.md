# 입력값 검증 기초

> 한 줄 요약: 입력값 검증은 "서버는 클라이언트를 신뢰하지 않는다"는 원칙에서 출발하며, 형식(타입·길이·패턴)과 의미(허용 범위·비즈니스 규칙) 두 층으로 나눠 방어한다.

**난이도: 🟢 Beginner**

관련 문서:

- [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md)
- [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- [security 카테고리 인덱스](./README.md)
- [Spring Bean DI 기초](../spring/spring-bean-di-basics.md)

retrieval-anchor-keywords: input validation basics, 입력값 검증이 뭐예요, 서버사이드 검증 왜 필요해요, validation vs sanitization, bean validation, 클라이언트 검증만 하면 안 되나요, beginner input validation, allowlist vs blocklist, 입력 필터링 기초, 검증 누락 위험

## 핵심 개념

입력값 검증(Input Validation)은 외부에서 들어오는 모든 데이터를 서버가 처리하기 전에 기대 형식과 범위 안에 있는지 확인하는 것이다. 핵심 전제는 **클라이언트는 신뢰할 수 없다**는 것이다. 브라우저의 프론트엔드 검증은 UX 개선용이고, 공격자는 프론트엔드를 우회해 서버에 직접 요청을 보낼 수 있다. 입문자가 헷갈리는 이유는 "프론트엔드에서 이미 검증했는데 왜 서버에서도 해야 하냐"는 질문에서 나온다.

## 한눈에 보기

입력값 검증은 형식(syntactic)과 의미(semantic) 두 층으로 나눈다.

```
1. 형식 검증 (syntactic)
   - 타입: 숫자인가 문자열인가
   - 길이: 이름 ≤ 100자, 비밀번호 ≥ 8자
   - 패턴: 이메일 형식, UUID 형식

2. 의미 검증 (semantic)
   - 범위: 나이 1~150, 날짜 미래인가 과거인가
   - 비즈니스 규칙: 존재하는 사용자 ID인가, 본인 리소스인가
```

Spring에서는 Bean Validation 어노테이션으로 형식 검증을 선언적으로 처리한다.

- `@NotBlank @Size(max = 100) String name;`
- `@Email String email;`
- `@Min(0) @Max(150) int age;`

의미 검증(비즈니스 규칙)은 서비스 레이어에서 추가로 수행한다.

## 상세 분해

- **Allowlist vs Blocklist**: 허용할 것만 명시하는 allowlist 방식이 막을 것을 나열하는 blocklist보다 안전하다. 블랙리스트는 공격자가 우회 변형을 만들 수 있지만, 허용 목록 밖의 입력은 처음부터 거부된다.
- **Validation vs Sanitization의 차이**: Validation은 "이 값이 허용 범위 안에 있는가"를 판단해 거부하거나 통과시킨다. Sanitization은 위험한 문자를 제거하거나 이스케이프해 안전한 형태로 변환한다. HTML 출력에서는 sanitization이, DB 파라미터에서는 PreparedStatement가 핵심이다.
- **Bean Validation 사용**: Spring에서는 `@Valid` / `@Validated` + `@NotBlank`, `@Size`, `@Email` 등의 어노테이션으로 컨트롤러 레이어에서 형식 검증을 선언적으로 처리한다. 의미 검증(도메인 규칙)은 서비스 레이어에서 추가로 수행한다.
- **실패 응답**: 검증 실패 시 `400 Bad Request`로 응답하고, 어떤 필드가 왜 잘못됐는지를 클라이언트에게 알려준다. 내부 상세 에러(스택 트레이스 등)는 노출하지 않는다.

## 흔한 오해와 함정

- **"프론트엔드에서 했으니까 서버는 생략해도 된다"** → 공격자는 Postman·curl로 프론트엔드를 완전히 우회해 직접 서버에 요청한다. 서버 검증은 선택이 아니다.
- **"null 체크만 해도 충분하다"** → 빈 문자열, 공백만 가득한 문자열, 아주 긴 문자열 등 null이 아니지만 비정상인 입력이 많다. `@NotBlank`, 길이 제한, 패턴 검증을 함께 써야 한다.
- **"검증은 컨트롤러에서만 하면 된다"** → 컨트롤러는 형식 검증, 서비스는 비즈니스 규칙 검증을 나눠 처리하는 것이 일반적이다. 비즈니스 규칙을 컨트롤러에 몰아넣으면 유지보수가 어려워진다.

## 실무에서 쓰는 모습

Spring MVC에서는 `@RequestBody`에 `@Valid`를 붙이고, DTO 필드에 `@NotBlank` / `@Size` / `@Email`을 선언한다. 검증 실패 시 `MethodArgumentNotValidException`이 발생하며, `@RestControllerAdvice`에서 잡아 `400` 응답과 필드별 에러 메시지를 반환하는 패턴이 일반적이다. 도메인 레이어에서는 `IllegalArgumentException`이나 커스텀 예외를 던져 비즈니스 규칙 위반을 처리한다.

## 더 깊이 가려면

- [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md) — 입력값 검증이 부족할 때 발생하는 대표적인 공격 심화
- [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md) — 출력 이스케이프(sanitization)와 Spring Security 연동

## 면접/시니어 질문 미리보기

- **"프론트엔드에서 검증이 있는데도 서버에서 다시 검증하는 이유가 뭔가요?"** → 클라이언트는 신뢰 경계 밖에 있고, 프론트엔드를 우회해 직접 HTTP 요청을 만들 수 있으므로 서버가 유일한 신뢰할 수 있는 검증 지점이다.
- **"Allowlist와 Blocklist 중 어떤 방식을 권장하나요?"** → Allowlist는 기대값만 통과시키므로 알려지지 않은 우회 공격도 막을 수 있어 일반적으로 더 안전하다.

## 한 줄 정리

입력값 검증은 "서버는 모든 외부 입력을 의심한다"는 원칙을 형식·의미 두 층으로 구현하는 것이며, 프론트엔드 검증은 서버 검증을 대체할 수 없다.
