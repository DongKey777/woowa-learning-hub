# PATCH DTO에서 `missing` / `null` / 값 있음 을 구분하는 첫 입문

> 한 줄 요약: PATCH 요청에서는 "필드가 안 왔다", "`null`이 명시적으로 왔다", "새 값이 왔다"가 서로 다른 의도일 수 있으므로, beginner는 먼저 `missing = 유지`, `null = 비우기`, `value = 변경` 3칸 표부터 잡는 편이 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java Deep Dive Catalog](./README.md)
- [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- [Spring Controller에서 Entity를 바로 반환하지 않고 DTO를 두는 이유](../../spring/spring-controller-entity-return-vs-dto-return-primer.md)

retrieval-anchor-keywords: patch dto tri-state, patch missing null value beginner, missing vs explicit null patch, partial update beginner java, fieldpatch primer, patch dto 뭐예요, patch null 왜 구분해, patch missing keep value, patch beginner basics, dto partial update 처음, json patch null missing beginner, update dto clear field, present value patch primer, what is patch tri-state

## 핵심 개념

처음에는 PATCH를 이렇게 번역하면 된다.

- 필드가 아예 없음: 기존 값을 그대로 둔다
- 필드가 `null`: 값을 비우려는 의도일 수 있다
- 필드에 새 값이 있음: 그 값으로 바꾸려는 의도다

즉 PATCH는 "새 객체 전체를 보내는 요청"보다
"기존 객체에서 어느 칸을 어떻게 만질지 보내는 요청"에 가깝다.

초보자가 가장 많이 섞는 지점도 여기다.
`null`과 missing을 둘 다 "값이 없네"로 읽어 버리면,
유지와 삭제가 같은 뜻이 되어 버린다.

짧게 외우면 이 한 줄이면 충분하다.

> PATCH의 첫 질문은 "값이 뭐냐"보다 "건드리지 말라는 건지, 지우라는 건지, 바꾸라는 건지"다.

## 한눈에 보기

| payload 상태 | 초보자용 첫 해석 | 서버가 보통 하는 일 |
|---|---|---|
| 필드 누락 | 이번 요청에서는 안 만짐 | 기존 값 유지 |
| `"nickname": null` | 값을 비우려는 요청일 수 있음 | clear 또는 remove |
| `"nickname": "neo"` | 새 값으로 교체 | change |

닉네임 수정 예시를 한 줄씩 보면 더 쉽다.

```json
{}
```

```json
{"nickname": null}
```

```json
{"nickname": "neo"}
```

위 세 요청은 겉보기엔 비슷해 보여도, 보통은 같은 요청이 아니다.

## 왜 `String nickname` 하나로는 자꾸 헷갈릴까

beginner가 흔히 처음 쓰는 DTO는 이런 모양이다.

```java
public record UpdateProfileRequest(String nickname) {}
```

문제는 이 타입만 봐서는 아래 둘을 쉽게 구분하지 못한다는 점이다.

- 클라이언트가 `nickname` 필드를 아예 안 보냈다
- 클라이언트가 `nickname: null`을 명시적으로 보냈다

둘 다 결국 `null`처럼 들어오면 service는 의도를 잃는다.

- "기존 닉네임 유지"를 원했는데 지워 버릴 수 있다
- "명시적으로 비우기"를 원했는데 그냥 무시할 수 있다

즉 문제의 핵심은 `String`이 나쁜 타입이라는 뜻이 아니라,
PATCH가 필요한 표현 공간이 `String 하나`보다 넓다는 데 있다.

## beginner는 tri-state를 어떻게 읽으면 되나

처음부터 복잡한 직렬화 구현을 외울 필요는 없다.
먼저 "한 필드에 상태가 3개 있다"는 감각만 잡으면 된다.

| 상태 | 뜻 | 서비스 적용 감각 |
|---|---|---|
| `Missing` | 안 보냄 | 그대로 둔다 |
| `NullValue` | 명시적 `null` | 비운다 |
| `Present("neo")` | 값 보냄 | 바꾼다 |

코드 모양은 아래 정도로만 읽어도 충분하다.

```java
public sealed interface FieldPatch<T> permits Missing, NullValue, Present {}

public record Missing<T>() implements FieldPatch<T> {}

public record NullValue<T>() implements FieldPatch<T> {}

public record Present<T>(T value) implements FieldPatch<T> {}
```

핵심은 문법이 아니라 이름이다.

- `Missing`은 "값이 없다"가 아니라 "이번엔 안 건드림"이다
- `NullValue`는 "실수로 비었다"가 아니라 "비우기 요청"일 수 있다
- `Present`는 "새 값이 실제로 왔다"는 뜻이다

## 실무에서 쓰는 모습

프로필 수정 요청을 아주 작게 보면 이런 흐름이다.

```java
public record UpdateProfileRequest(FieldPatch<String> nickname) {}
```

```java
public Profile apply(UpdateProfileRequest request, Profile profile) {
    return switch (request.nickname()) {
        case Missing<String> ignored -> profile;
        case NullValue<String> ignored -> profile.clearNickname();
        case Present<String> present -> profile.changeNickname(present.value());
    };
}
```

여기서 beginner가 봐야 할 포인트는 세 가지다.

- `Missing`이면 기존 객체를 그대로 둔다
- `NullValue`면 clear 메서드처럼 "삭제 의도"를 따로 읽는다
- `Present`면 그때만 새 값을 검증하고 바꾼다

이후에 값 객체를 붙이면 더 안정적이다.
예를 들어 `Present<String>`에서 바로 domain으로 넘기지 않고 `new Nickname(...)`으로 바꾸면,
공백 문자열 처리나 같은 값 판단을 한곳에 모을 수 있다.

## 흔한 오해와 함정

- "`null`이면 그냥 값이 없는 거 아닌가요?"
  PATCH에서는 아니다. 안 보낸 것과 지우려는 것은 다른 요청일 수 있다.
- "그럼 모든 DTO를 다 `FieldPatch`로 감싸야 하나요?"
  아니다. 전체 생성(create) 요청처럼 필드가 항상 와야 하는 모델은 보통 필요 없다.
- "`Optional<String>`이면 되지 않나요?"
  beginner 관점에선 보통 부족하다. `Optional`은 "있음/없음" 2칸에 더 가깝고, PATCH는 missing과 explicit `null`을 둘 다 구분해야 할 수 있다.
- "문자열 하나 바꾸는데 너무 복잡한 것 아닌가요?"
  필드를 적게 바꾸는 PATCH일수록 유지/삭제/변경이 더 중요해져서 오히려 작은 tri-state가 도움이 된다.

## 더 깊이 가려면

- raw DTO를 값 객체로 넘기는 감각은 [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)
- 값 객체가 왜 `equals()`/`hashCode()`와 이어지는지는 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- `==`와 `equals()`를 먼저 분리하고 싶다면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- DTO와 도메인 역할 분리는 [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- Spring 요청/응답 DTO 감각은 [Spring Controller에서 Entity를 바로 반환하지 않고 DTO를 두는 이유](../../spring/spring-controller-entity-return-vs-dto-return-primer.md)

## 면접/시니어 질문 미리보기

> Q: PATCH에서 missing과 `null`을 왜 굳이 나누나요?
> 핵심: "유지"와 "삭제"가 다른 명령이기 때문이다.

> Q: create DTO에도 tri-state가 꼭 필요할까요?
> 핵심: 보통은 아니다. partial update처럼 "안 건드림" 상태가 중요한 경우에 더 자주 등장한다.

> Q: `Present<String>`를 바로 domain에 넣어도 되나요?
> 핵심: 가능은 하지만, 값 규칙이 있으면 value object로 한 번 올려 두는 편이 더 안전하다.

## 한 줄 정리

PATCH beginner의 첫 멘탈 모델은 `missing = 유지`, `null = 비우기`, `value = 변경`이고, 이 3칸을 DTO에서 잃지 않아야 부분 수정 의도를 안전하게 읽을 수 있다.
