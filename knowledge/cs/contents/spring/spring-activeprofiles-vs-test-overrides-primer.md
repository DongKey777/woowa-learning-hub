# Spring `@ActiveProfiles` vs test override primer: `application-test.yml`, `@TestPropertySource`, annotation `properties`

> 한 줄 요약: `@ActiveProfiles`는 **어떤 profile을 켤지 고르는 스위치**이고, `application-test.yml`, `@TestPropertySource`, 테스트 annotation의 `properties`는 **실제 property 값을 어디서 가져올지 정하는 도구**다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `@ActiveProfiles`, `application-test.yml`, `@TestPropertySource`, `@SpringBootTest(properties = ...)`를 초보자가 "profile 선택"과 "property override"라는 두 축으로 분리해 이해하도록 돕는 **beginner testing primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](./spring-testing-basics.md)
> - [Spring External Config File Precedence Primer: packaged `application.yml`, external file, `spring.config.location`, `spring.config.import`](./spring-external-config-file-precedence-primer.md)

retrieval-anchor-keywords: ActiveProfiles vs TestPropertySource, ActiveProfiles vs application-test.yml, spring test profile override beginner, application-test.yml not loaded, @ActiveProfiles test profile select, @TestPropertySource beginner, SpringBootTest properties beginner, WebMvcTest properties attribute, DataJpaTest properties attribute, application-test.yml override confusion, profile selection vs property override, spring test property source primer, spring test properties annotation vs file, test profile file loading, active profile does not set properties

## 핵심 개념

초보자는 먼저 이 둘을 분리하면 된다.

```text
1. 어떤 profile을 켤까? -> @ActiveProfiles
2. 그다음 실제 값을 어디서 가져올까? -> application-test.yml / @TestPropertySource / properties
```

즉 `@ActiveProfiles`는 값을 직접 적는 도구가 아니다.
`test` profile을 켜서 `application-test.yml` 같은 **후보 파일을 읽게 만드는 스위치**에 가깝다.

반대로 아래 셋은 실제 값을 공급한다.

- `application-test.yml`
- `@TestPropertySource`
- 테스트 annotation의 `properties`

가장 중요한 한 줄은 이것이다.

**`@ActiveProfiles`는 "무슨 파일이 후보가 되나"를 정하고, override 도구들은 "같은 key가 있을 때 어떤 값이 최종값이 되나"를 정한다.**

---

## 1. 네 가지를 한 표로 분리

| 도구 | 하는 일 | 값을 직접 적나 | 범위 감각 | 초보자용 한 줄 |
|---|---|---|---|---|
| `@ActiveProfiles("test")` | active profile 선택 | 아니다 | 이 테스트 컨텍스트 | "`test` profile을 켠다" |
| `application-test.yml` | `test` profile용 설정 파일 | 파일에 적는다 | 보통 여러 테스트가 공유 | "`test` profile일 때 읽히는 기본 테스트 설정" |
| `@TestPropertySource` | 테스트용 property source 추가 | 파일/inline 둘 다 가능 | 테스트 클래스 또는 상속 구조 | "테스트에서만 쓸 설정 묶음을 올린다" |
| `@SpringBootTest(properties = ...)` 또는 `@WebMvcTest(properties = ...)` | 테스트 annotation에서 바로 override | 그렇다 | 이 테스트 클래스 로컬 | "이 클래스 위에 짧은 메모를 붙인다" |

핵심 차이는 이것이다.

- `@ActiveProfiles`는 profile selector다.
- 나머지 셋은 property source 또는 override 도구다.

그래서 `@ActiveProfiles("test")`만 붙였다고 값이 생기는 것은 아니다.
그 profile에 해당하는 파일이나 다른 override가 있어야 실제 값이 들어온다.

---

## 2. 가장 흔한 착시: `@ActiveProfiles("test")`를 값 override로 오해하기

예를 들어 파일이 이렇게 있다고 하자.

```yaml
# application.yml
app:
  mode: default
```

```yaml
# application-test.yml
app:
  mode: test-file
```

테스트가 이렇다면:

```java
@SpringBootTest
@ActiveProfiles("test")
class MemberServiceTest {
}
```

이때 `app.mode`는 `test-file`이 된다.
이유는 `@ActiveProfiles("test")`가 직접 `app.mode=test-file`을 넣어서가 아니라, **`application-test.yml`을 읽게 만들었기 때문**이다.

즉 실제 값 공급자는 `application-test.yml`이고, `@ActiveProfiles`는 그 파일을 활성화한 쪽이다.

반대로 `application-test.yml`이 아예 없으면:

```java
@SpringBootTest
@ActiveProfiles("test")
class MemberServiceTest {
}
```

이 테스트는 그냥 "`test` profile로 컨텍스트를 띄운다"는 뜻만 가진다.
profile 기반 bean 분기에는 영향을 줄 수 있지만, 모든 key가 자동으로 테스트값으로 바뀌는 것은 아니다.

---

## 3. `application-test.yml`은 "파일", `@TestPropertySource`는 "테스트용 추가 source"

둘 다 테스트에서 값을 공급할 수 있지만 감각이 다르다.

### `application-test.yml`

- `test` profile이 active일 때만 읽힌다
- 보통 공통 테스트 기본값을 담는다
- 예: H2 설정, 테스트용 logging level, feature flag 기본값

```yaml
# application-test.yml
spring:
  datasource:
    url: jdbc:h2:mem:testdb

app:
  payment:
    retry: false
```

### `@TestPropertySource`

- profile 활성화와 별개로 테스트에 property source를 추가한다
- 파일로 줄 수도 있고 inline으로 줄 수도 있다
- 여러 테스트가 공유할 테스트 설정 묶음을 표현할 때 잘 맞는다

```java
@SpringBootTest
@ActiveProfiles("test")
@TestPropertySource(properties = {
        "app.payment.retry=true",
        "app.partner.timeout=2s"
})
class PaymentServiceTest {
}
```

이 경우 초보자 mental model은 이렇게 잡으면 된다.

```text
application-test.yml = test profile용 기본 테스트 노트
@TestPropertySource = 이 테스트에 추가로 덧붙인 노트
```

---

## 4. annotation `properties`는 가장 로컬한 override다

`@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest` 같은 테스트 annotation에는 `properties` 속성을 둘 수 있다.

```java
@WebMvcTest(controllers = OrderController.class, properties = {
        "app.api.auth.enabled=false",
        "app.banner.enabled=false"
})
class OrderControllerTest {
}
```

이 방식은 아래 상황에 잘 맞는다.

- 이 테스트 클래스에서만 값 1~2개 바꾸고 싶다
- 파일 하나 더 만들 정도는 아니다
- 읽는 사람이 annotation만 보고 바로 의도를 파악하면 좋다

초보자 기준 한 줄 요약:

**`properties`는 "공통 테스트 설정"보다 "이 테스트만 잠깐 바꾸는 상수 메모"에 가깝다.**

---

## 5. 같은 key가 여러 곳에 있으면 어떻게 읽나

beginner 기준으로는 세밀한 전체 우선순위를 외우기보다 아래 순서를 잡으면 된다.

```text
1. @ActiveProfiles가 어떤 profile 파일을 후보로 올린다
2. application-test.yml 같은 profile 파일이 값을 제공한다
3. @TestPropertySource나 annotation properties가 있으면 그 값이 다시 덮을 수 있다
```

즉 `@ActiveProfiles`는 보통 "선택 단계"이고,
`application-test.yml`, `@TestPropertySource`, `properties`는 "값 결정 단계"라고 보면 된다.

아래 예시를 보자.

```yaml
# application.yml
app:
  mode: base
```

```yaml
# application-test.yml
app:
  mode: test-file
```

```java
@SpringBootTest(properties = "app.mode=inline")
@ActiveProfiles("test")
class AppModeTest {
}
```

이 테스트에서 초보자가 읽어야 하는 흐름은 이렇다.

1. `@ActiveProfiles("test")`가 `test` profile을 켠다
2. 그래서 `application-test.yml`이 후보가 된다
3. 하지만 이 테스트 클래스가 `app.mode=inline`을 직접 override했으므로 최종값은 `inline` 쪽으로 읽힌다

즉 `application-test.yml`이 무시된 것이 아니라, **더 가까운 테스트 override에 가려진 것**이다.

---

## 6. 무엇을 먼저 고를까

| 질문 | 먼저 볼 도구 | 이유 |
|---|---|---|
| 테스트 전반에서 `test` 환경을 켜야 하나 | `@ActiveProfiles("test")` | profile 파일과 profile bean 분기를 함께 맞출 수 있다 |
| `test` profile일 때 공통 기본값이 필요하나 | `application-test.yml` | 여러 테스트가 공유하는 기본 테스트 설정에 맞다 |
| 특정 테스트 그룹에 파일/inline 설정 묶음을 더 올려야 하나 | `@TestPropertySource` | 테스트용 추가 source를 명시적으로 붙이기 좋다 |
| 이 클래스에서만 고정값 1~2개 바꾸면 되나 | annotation `properties` | 가장 짧고 로컬하다 |

실무에서 자주 쓰는 조합은 아래와 같다.

```text
공통 테스트 환경 = @ActiveProfiles("test") + application-test.yml
개별 테스트 미세 조정 = @TestPropertySource 또는 properties
```

---

## 7. 흔한 오해

### 1. `@ActiveProfiles("test")`를 붙이면 `application-test.yml`이 없어도 테스트용 값이 자동으로 들어온다

아니다. `@ActiveProfiles`는 profile을 켜는 도구지, key/value를 만들어 주는 도구가 아니다.

### 2. `application-test.yml`은 테스트에서 항상 자동 적용된다

아니다. `test` profile이 active여야 한다.
보통은 `@ActiveProfiles("test")`나 다른 profile 활성화 방식이 필요하다.

### 3. `@TestPropertySource`와 annotation `properties`는 완전히 같은 의미다

겹치는 부분은 있지만 용도가 다르다.

- `@TestPropertySource`는 테스트용 설정 묶음
- annotation `properties`는 테스트 클래스 로컬 override

### 4. profile을 고르는 것과 값을 덮어쓰는 것은 같은 문제다

아니다. 초보자 혼란의 핵심이 여기 있다.

- profile 선택: `@ActiveProfiles`
- 값 override: `application-test.yml`, `@TestPropertySource`, annotation `properties`

---

## 8. 한 번에 읽는 결정 트리

```text
이 테스트에서 test 환경을 켜야 하나?
-> 예: @ActiveProfiles("test")

그 환경의 공통 기본값이 필요한가?
-> 예: application-test.yml

그래도 이 테스트에서만 값을 조금 바꿔야 하나?
-> 적은 수면 annotation properties
-> 묶음/파일이면 @TestPropertySource
```

`@ActiveProfiles`를 property override 도구로 착각하지 않으면,
`application-test.yml`이 왜 안 먹는지와 inline override가 왜 더 세게 보이는지 대부분 바로 풀린다.

## 한 줄 정리

`@ActiveProfiles`는 **profile 선택**, `application-test.yml`은 **선택된 profile의 파일**, `@TestPropertySource`는 **테스트용 추가 property source**, annotation `properties`는 **이 테스트 클래스의 짧은 로컬 override**로 보면 초보자의 혼란이 가장 빨리 정리된다.
