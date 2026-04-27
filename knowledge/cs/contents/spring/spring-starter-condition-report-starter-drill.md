# Spring Starter Condition Report Starter Drill: `spring-boot-starter-data-jpa` 하나를 positive/negative match로 읽는 법

> 한 줄 요약: `spring-boot-starter-data-jpa`를 넣었다는 사실만으로 JPA 관련 bean이 확정되지는 않는다. Condition Evaluation Report에서 `DataSourceAutoConfiguration`과 JPA auto-configuration이 왜 positive 또는 negative였는지 연결해서 봐야 한다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 starter dependency 하나를 Condition Evaluation Report의 positive/negative entry로 직접 이어 보는 **beginner walkthrough drill**을 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Starter Dependency Map 입문: starter, auto-configuration module, SDK/driver는 누가 소유하나](./spring-starter-dependency-map-primer.md)
> - [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)

retrieval-anchor-keywords: starter condition report drill, spring starter to condition evaluation report, spring-boot-starter-data-jpa positive negative match, DataSourceAutoConfiguration beginner drill, JPA starter report walkthrough, starter dependency report mapping, starter added but negative match, DataSourceAutoConfiguration did not match property, DataSourceAutoConfiguration did not find class driver, spring starter report beginner example, condition evaluation report positive negative beginner, mysql connector runtimeOnly starter drill, jpa starter conditions walkthrough

## 핵심 개념

처음에는 이 세 줄만 기억하면 된다.

```text
starter 추가 = 관련 auto-configuration 후보를 classpath에 올림
positive match = 그 후보의 조건이 이번 실행에서 통과함
negative match = 후보는 있었지만 classpath/property/기존 bean 조건 중 하나가 막음
```

즉 "`starter`를 넣었다"는 말과 "`report에서 positive match가 떴다`"는 말은 다르다.

이 문서에서는 starter 하나만 잡고, report를 이렇게 읽는 연습을 한다.

```text
build.gradle / pom.xml의 dependency
-> 어떤 auto-configuration 후보를 기대할지 적는다
-> report에서 positive/negative entry를 찾는다
-> classpath / property / existing bean 중 무엇이 갈랐는지 확인한다
```

---

## 이번 drill의 대상: `spring-boot-starter-data-jpa`

예시는 일부러 가장 흔한 조합으로 잡는다.

```gradle
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    runtimeOnly("com.mysql:mysql-connector-j")
}
```

이 dependency를 beginner 눈높이로 번역하면 아래와 같다.

| 내가 build 파일에 적은 것 | Boot가 기대하는 다음 단계 | report에서 주로 찾을 이름 |
|---|---|---|
| `spring-boot-starter-data-jpa` | JPA / DataSource 관련 auto-configuration 후보 읽기 | `DataSourceAutoConfiguration`, JPA 관련 auto-configuration |
| `mysql-connector-j` | JDBC driver class를 runtime classpath에서 찾기 | classpath 관련 positive/negative 문구 |
| `spring.datasource.*` property | 실제 `DataSource`를 만들 정보 확인 | property 관련 positive/negative 문구 |

핵심은 starter 하나만 보지 말고, **starter + driver + property**를 한 묶음으로 보는 것이다.

---

## 30초 mental model

이 drill은 아래 화살표 하나로 끝난다.

```text
spring-boot-starter-data-jpa 추가
-> DataSource/JPA auto-configuration 후보 등장
-> mysql driver class와 datasource property 확인
-> 조건이 맞으면 positive match
-> 하나라도 비면 negative match
```

즉 report를 볼 때 질문도 딱 세 개면 충분하다.

1. 후보 auto-configuration이 report에 보였나?
2. positive match였나, negative match였나?
3. 갈린 이유가 driver(classpath)인가, datasource property인가?

---

## 먼저 map을 적고 들어간다

초보자는 report를 열기 전에 아래처럼 한 번 적어 두면 훨씬 덜 헤맨다.

| 내가 기대하는 것 | 왜 기대하나 | report에서 먼저 찾을 단서 |
|---|---|---|
| `DataSource`가 생긴다 | JPA starter와 JDBC driver를 넣었다 | `DataSourceAutoConfiguration` |
| JPA 관련 bean이 생긴다 | DataSource가 준비되면 JPA 쪽도 이어진다 | JPA 관련 auto-configuration positive match |
| 안 생기면 이유가 보인다 | Boot는 조건부 등록을 하기 때문이다 | `did not match`, `did not find`, `found bean` |

이 표를 적는 이유는 단순하다.
처음부터 전체 report를 읽지 않고, **`DataSourceAutoConfiguration`부터 좁혀 보기 위해서**다.

---

## 시나리오 A. positive match로 이어지는 경우

아래 조건이 모두 맞는 상황을 상상하면 된다.

- `spring-boot-starter-data-jpa`가 있다
- `mysql-connector-j`가 runtime classpath에 있다
- `spring.datasource.url` 같은 datasource property가 들어왔다

이때 report는 버전마다 문장이 조금 달라도, 초보자가 읽어야 하는 뜻은 거의 같다.

```text
DataSourceAutoConfiguration matched:
  - required class를 찾았다
  - datasource property가 맞다
  - 기존 DataSource bean이 없다
```

beginner 해석은 아래 세 줄이면 충분하다.

| report에서 읽은 뜻 | beginner 해석 | 다음 판단 |
|---|---|---|
| required class를 찾음 | driver/classpath 관문은 통과했다 | classpath 문제는 뒤로 미룬다 |
| datasource property가 맞음 | 연결 정보도 들어왔다 | property 문제도 아니다 |
| 기존 `DataSource` bean이 없음 | Boot 기본 조립이 물러날 이유가 없다 | `DataSource` 생성이 이어질 가능성이 크다 |

즉 positive match면 질문이 이렇게 바뀐다.

```text
"starter가 안 먹었나?"가 아니라
"DataSource 단계는 통과했으니, 그 다음 JPA bean 조립에서 무엇을 더 봐야 하지?"
```

---

## 시나리오 B. starter는 있는데 negative match가 나는 경우

이제 같은 starter를 넣었지만, `spring.datasource.url`이 비어 있다고 가정해 보자.

report는 흔히 이런 방향으로 보인다.

```text
DataSourceAutoConfiguration:
  Did not match:
    - datasource property를 찾지 못했다
```

이때 beginner 해석은 아주 단순하다.

| 보이는 단서 | 바로 붙이는 해석 | 첫 행동 |
|---|---|---|
| `DataSourceAutoConfiguration`가 report에 보임 | 후보 자체는 읽혔다 | starter가 완전히 무시된 것은 아니다 |
| `Did not match` | 조건 중 하나가 false다 | positive/negative부터 갈라 본다 |
| datasource property를 찾지 못함 | property가 빠져서 `DataSource` 조립이 멈췄다 | `application.yml`, profile, env var를 확인한다 |

핵심은 이것이다.

```text
starter가 실패한 것이 아니라
starter가 연 auto-configuration 후보가 property 조건에서 멈춘 것이다
```

---

## 시나리오 C. starter는 있는데 driver classpath에서 negative match가 나는 경우

이번에는 JPA starter는 넣었지만, MySQL driver가 runtime classpath에 없다고 가정한다.

예를 들면 이런 착시가 가능하다.

- `mysql-connector-j`를 빼먹었다
- 환경에 따라 runtime classpath가 달라졌다
- test slice나 다른 실행물에서 driver가 빠졌다

report는 대체로 이런 방향으로 읽힌다.

```text
DataSourceAutoConfiguration:
  Did not match:
    - required driver class를 찾지 못했다
```

여기서 초보자가 잡아야 할 해석은 아래 한 줄이다.

```text
starter는 있었지만, 실제 driver class가 없어서 classpath 조건에서 멈췄다
```

즉 이 경우에는 property보다 먼저 아래를 본다.

- `build.gradle` / `pom.xml`에 driver가 실제로 있는가
- scope가 현재 실행의 runtime classpath에 들어오는가
- 로컬 / 테스트 / 패키징 산출물의 classpath가 같은가

이 분기는 [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)와 바로 이어진다.

---

## positive와 negative를 한 표에 붙여 외운다

| 같은 starter인데 갈리는 지점 | positive 쪽 해석 | negative 쪽 해석 |
|---|---|---|
| driver classpath | 필요한 driver class를 찾았다 | 필요한 driver class를 못 찾았다 |
| datasource property | 연결 정보가 들어왔다 | `spring.datasource.url` 등 필수 property가 비었다 |
| 기존 bean 존재 | Boot가 만들 기본 `DataSource`가 아직 없다 | 이미 같은 역할 bean이 있어 Boot가 back off할 수 있다 |

이 표의 목적은 "report 문장 한 줄"을 보면 바로 원인 축을 떠올리게 만드는 것이다.

- `did not find required class` -> classpath 축
- `did not find property` -> property 축
- `found existing bean` -> back-off 축

---

## beginner가 자주 헷갈리는 말 바꾸기

### 오해 1. "`spring-boot-starter-data-jpa`를 넣었는데 왜 `DataSource`가 없지?"

더 정확한 질문은 아래다.

```text
`DataSourceAutoConfiguration`이 positive match였나,
아니면 driver/property 조건에서 negative match였나?
```

### 오해 2. "starter가 있으면 report도 자동으로 positive일 것이다"

아니다.

- starter는 후보를 연다
- positive match는 이번 실행 문맥이 그 후보를 통과했을 때만 나온다

### 오해 3. "negative match면 starter dependency를 다시 추가해야 한다"

그렇지 않을 때가 많다.

- property를 채우면 끝날 수 있다
- driver scope만 바로잡으면 끝날 수 있다
- 이미 같은 역할 bean이 있어서 정상 back-off일 수 있다

---

## 이 drill을 다른 starter에도 복사하는 법

이 문서의 감각은 다른 starter에도 그대로 복사된다.

| starter | report에서 먼저 찾을 후보 | 초보자용 첫 질문 |
|---|---|---|
| `spring-boot-starter-web` | MVC / Jackson 관련 auto-configuration | web classpath와 기존 bean 때문에 갈렸나? |
| `spring-boot-starter-actuator` | actuator / metrics 관련 auto-configuration | registry 구현체와 exposure property가 맞나? |
| `spring-boot-starter-data-jpa` | `DataSourceAutoConfiguration`, JPA 관련 auto-configuration | driver, datasource property, existing bean 중 무엇이 갈랐나? |

즉 drill 자체는 항상 같다.

```text
starter 이름 적기
-> 기대할 auto-configuration 후보 적기
-> positive/negative match 찾기
-> classpath/property/back-off 축으로 원인 자르기
```

## 한 줄 정리

starter dependency는 "후보를 여는 입구"이고, Condition Evaluation Report의 positive/negative entry는 "이번 실행에서 그 입구가 실제로 통과됐는지"를 보여 주는 판정표다.
