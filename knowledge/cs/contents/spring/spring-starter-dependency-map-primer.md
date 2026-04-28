# Spring Starter Dependency Map 입문: starter, auto-configuration module, SDK/driver는 누가 소유하나

> 한 줄 요약: starter는 소비자 앱이 잡는 "입구 dependency"이고, auto-configuration module은 조건부 bean 등록 규칙이며, SDK/driver는 실제 구현 클래스를 제공하는 런타임 부품이다. 셋이 한 덩어리처럼 보이지만 선언 책임과 누락 증상은 다르다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 starter 이름, auto-configuration module, implementation SDK/driver를 하나의 dependency map으로 연결해 읽게 돕는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)
- [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)

> 관련 문서:
> - [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)
> - [Spring Starter Condition Report Starter Drill: `spring-boot-starter-data-jpa` 하나를 positive/negative match로 읽는 법](./spring-starter-condition-report-starter-drill.md)
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)

retrieval-anchor-keywords: spring starter 뭐예요, spring boot starter 뭐예요, starter 처음 배우는데, starter 큰 그림, what is spring starter, starter vs autoconfiguration module, starter vs sdk driver, spring boot starter vs autoconfigure, starter 넣으면 뭐가 따라와요, starter랑 driver 차이, starter랑 autoconfiguration 차이, 언제 starter 추가해요, starter jar no classes beginner, gradle runtimeonly mysql connector, starter dependency map primer

## 이 문서가 먼저 잡아야 하는 질문

이 문서는 아래처럼 **starter를 처음 보는 질문**에서 deep dive보다 먼저 걸리는 primer를 목표로 한다.

| 학습자 질문 모양 | 이 문서에서 먼저 주는 답 |
|---|---|
| "`spring starter`가 뭐예요?" | starter는 기능을 쓰겠다는 입구 dependency라고 먼저 자른다 |
| "starter 넣으면 끝 아닌가요?" | starter, auto-configuration, driver는 소유자와 역할이 다르다고 설명한다 |
| "starter랑 `spring-boot-autoconfigure`는 뭐가 달라요?" | 소비자용 묶음과 조건부 bean 조립 규칙을 분리한다 |
| "JPA starter 넣었는데 MySQL driver를 또 왜 적어요?" | starter와 vendor driver 책임이 분리된 구조라고 보여 준다 |

질문이 "`starter 넣었는데 왜 바로 Bean이 생겨요?`"라면 [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)로 이어서 "동작 원리"를 본다. 반대로 지금 질문이 "`starter 자체가 뭐예요?`", "`언제 starter를 추가하죠?`", "`왜 driver를 또 적죠?`"라면 이 문서가 첫 정거장이다.

## 이 문서 다음에 보면 좋은 문서

- starter를 넣었는데 실제 bean이 왜 안 뜨는지 증상 기준으로 바로 분기하려면 [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)로 간다.
- starter dependency 한 줄이 Condition Evaluation Report의 positive/negative match로 어떻게 이어지는지 한 번에 연습하려면 [Spring Starter Condition Report Starter Drill: `spring-boot-starter-data-jpa` 하나를 positive/negative match로 읽는 법](./spring-starter-condition-report-starter-drill.md)을 먼저 본다.
- `@Configuration`과 Boot auto-configuration의 관계부터 다시 잡고 싶으면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)로 이어진다.
- classpath 조건이 환경마다 왜 달라지는지 scope와 test slice 관점으로 더 보고 싶으면 [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)를 본다.
- JPA starter와 DB driver 관계가 아직 감으로 안 잡히면 [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)로 넘어가 "`save()` 뒤 SQL은 누가 만들고 driver는 어디서 쓰이는가"를 한 번 더 연결한다.
- Boot 자동 구성 전체 그림과 커스텀 starter 구조를 더 깊게 보려면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)으로 이어진다.

---

## 핵심 개념

용어보다 먼저 아래 세 줄로 잡으면 된다.

```text
starter = "이 기능을 쓰고 싶다"는 소비자용 입구 dependency
auto-configuration module = "조건이 맞으면 Bean을 이렇게 묶어라"는 조립 규칙
SDK/driver = 실제 연결과 동작을 수행하는 구현 클래스
```

초보자에게 중요한 포인트는 이것이다.

- starter 이름은 **앱이 처음 적는 편한 entrypoint**일 뿐이다.
- auto-configuration 코드는 흔히 **starter가 아니라 다른 module**에 들어 있다.
- 런타임 bean 생성은 결국 **SDK/driver class가 실제 classpath에 있느냐**에 달려 있다.

처음 배우는 입장에서는 아래처럼 한 문장씩 끊어 읽는 편이 안전하다.

- starter = "이 기능을 쓰고 싶다"라고 build 파일에 적는 첫 줄
- auto-configuration = "조건이 맞으면 이 Bean들을 묶어 주겠다"는 Spring Boot 쪽 조립 규칙
- driver/SDK = DB나 외부 시스템과 실제로 통신하는 구현 부품

즉 아래 세 질문은 서로 다르다.

1. 소비자 앱은 어떤 dependency를 직접 적는가?
2. 조건부 bean 등록 규칙은 어느 module이 제공하는가?
3. 실제 구현 클래스는 누가 제공하고, 런타임에 어디서 오는가?

---

## 먼저 이 그림으로 본다

```text
consumer application
-> starter 추가
-> starter가 auto-configuration module과 공통 라이브러리를 끌어옴
-> 경우에 따라 앱이 SDK/driver를 직접 추가
-> Boot가 auto-configuration을 읽음
-> SDK/driver class 존재 여부와 property를 검사
-> 조건이 맞으면 Bean 등록
```

핵심은 "`starter`를 넣었다"와 "`필요한 구현 클래스가 런타임에 있다`"를 분리해서 보는 것이다.

---

## 역할을 한 표로 가르기

| 레이어 | 한 줄 역할 | 보통 artifact 이름 | 주로 누가 소유하나 | 앱이 직접 선언하나? |
|---|---|---|---|---|
| starter | 소비자용 entrypoint 묶음 | `spring-boot-starter-web`, `spring-boot-starter-data-jpa` | Boot 또는 starter 제공자 | 보통 예 |
| auto-configuration module | 조건부 bean 등록 규칙 | `spring-boot-autoconfigure`, `*-spring-boot-autoconfigure` | Boot 또는 starter 제공자 | 보통 아니오 |
| implementation SDK/driver | 실제 클라이언트, 드라이버, registry, vendor API | `mysql-connector-j`, `micrometer-registry-prometheus`, `vendor-sdk` | DB/vendor/library 제공자 | 경우에 따라 예 |

여기서 beginner가 자주 헷갈리는 포인트는 두 가지다.

- starter 이름이 보여도 **그 jar 안에 핵심 코드가 다 있는 것은 아니다**.
- direct dependency가 하나 더 필요해도 **starter가 실패한 것이 아니라 계약이 분리된 것**일 수 있다.

---

## 30초 분리표

| 지금 궁금한 것 | 먼저 봐야 하는 대상 | 보통 답이 있는 곳 |
|---|---|---|
| "앱에서 무엇을 추가해야 하지?" | starter 선언과 direct SDK/driver 선언 | `build.gradle`, `pom.xml` |
| "어떤 조건에서 Bean이 생기지?" | auto-configuration class와 `@ConditionalOn...` | `spring-boot-autoconfigure`, `*-autoconfigure` |
| "왜 런타임에만 안 되지?" | implementation class 존재 여부와 dependency scope | SDK/driver artifact, `runtimeOnly`/`runtime` |

즉 증상이 bean 누락이어도, 실제 원인은 build 파일의 서로 다른 층에 있을 수 있다.

---

## 예시 1. `spring-boot-starter-web`: starter 하나로 충분한 경우

이 경우 beginner는 보통 starter 하나만 적는다.

```gradle
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
}
```

```xml
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
  </dependency>
</dependencies>
```

이 dependency map을 역할별로 나누면 아래처럼 읽는다.

| 레이어 | 이 예시에서 보는 것 | beginner 해석 |
|---|---|---|
| starter | `spring-boot-starter-web` | 소비자 앱이 "웹 앱을 쓰겠다"라고 선언하는 입구 |
| auto-configuration module | Boot의 MVC/JSON/embedded server 관련 auto-configuration | 조건이 맞으면 DispatcherServlet, converter, server 설정을 묶어 준다 |
| implementation libs | `spring-webmvc`, Jackson, embedded server 관련 라이브러리 | starter가 transitively 함께 끌어오는 실제 구현 부품 |

여기서 포인트는 다음과 같다.

- consumer는 starter 하나만 적는다.
- auto-configuration 코드는 `spring-boot-autoconfigure` 쪽에서 읽힌다.
- 실제 MVC/JSON/server 구현 라이브러리는 transitive dependency로 따라온다.

즉 이 경우는 "starter 하나로 충분한 모양"이다.

---

## 예시 2. `spring-boot-starter-data-jpa` + MySQL driver: driver는 앱이 직접 고르는 경우

JPA starter는 JPA/Hibernate 쪽 Spring integration을 쉽게 붙여 주지만, **어느 DB vendor driver를 쓸지는 앱이 직접 선택**하는 경우가 많다.

```gradle
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    runtimeOnly("com.mysql:mysql-connector-j")
}
```

```xml
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
  </dependency>
  <dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <scope>runtime</scope>
  </dependency>
</dependencies>
```

이걸 dependency map으로 다시 풀면 이렇다.

| 레이어 | 이 예시에서 보는 것 | 누가 고르나 |
|---|---|---|
| starter | `spring-boot-starter-data-jpa` | 소비자 앱이 JPA integration을 쓰겠다고 고른다 |
| auto-configuration module | Boot의 `DataSource`/JPA 관련 auto-configuration | Boot가 조건에 따라 활성화한다 |
| implementation SDK/driver | `mysql-connector-j` | 앱이 DB vendor를 직접 고른다 |

여기서 중요한 beginner 포인트는 이것이다.

- starter는 JPA integration entrypoint다.
- auto-configuration은 `DataSource`, JPA, transaction bean 조립 규칙을 제공한다.
- MySQL driver는 실제 JDBC 연결을 담당하는 vendor 부품이다.

그래서 아래 기대는 틀릴 수 있다.

```text
JPA starter를 넣었으니 MySQL driver도 알아서 있겠지
```

실제에 가까운 해석은 아래다.

```text
JPA starter는 Spring 쪽 integration을 붙여 준다
MySQL driver 선택은 앱의 책임이다
```

즉 이 패턴에서 direct driver dependency는 중복이 아니라 **의도적 선택 지점**이다.

---

## 예시 3. `starter`는 있는데 구현 registry는 따로 필요한 경우

DB driver만 분리되는 것은 아니다. 메트릭 exporter 같은 구현 module도 별도로 붙는 경우가 있다.

```gradle
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    runtimeOnly("io.micrometer:micrometer-registry-prometheus")
}
```

```xml
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
  </dependency>
  <dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
    <scope>runtime</scope>
  </dependency>
</dependencies>
```

이 예시는 "starter + implementation module" 패턴을 보여 준다.

| 레이어 | 이 예시에서 보는 것 | beginner 해석 |
|---|---|---|
| starter | `spring-boot-starter-actuator` | metrics와 운영 endpoint 진입점 |
| auto-configuration module | Boot/Micrometer auto-configuration | registry 구현체가 보이면 적절한 `MeterRegistry`를 연결 |
| implementation module | `micrometer-registry-prometheus` | 실제 Prometheus exporter 구현 |

즉 "`Actuator starter`를 넣었는데 왜 Prometheus export가 안 보이지?"는 starter 자체보다 **registry implementation artifact가 있는가**를 먼저 봐야 할 수 있다.

---

## 자주 하는 오해

### 오해 1. starter artifact가 곧 auto-configuration 코드 위치다

대개 그렇지 않다.

- starter는 소비자용 묶음이다.
- auto-configuration 코드는 흔히 `spring-boot-autoconfigure` 또는 `*-autoconfigure` module에 있다.

따라서 "`starter`를 열어 봤는데 코드가 별로 없네?"는 이상 현상이 아니라 흔한 구조다.

### 오해 2. direct SDK/driver dependency가 필요하면 starter가 불완전하다

그렇게 볼 필요는 없다.

- DB vendor
- exporter/registry 구현체
- cloud vendor SDK

이런 것들은 소비자 앱이 직접 선택해야 자연스러운 경우가 많다.
Boot나 starter 작성자가 특정 vendor를 강제로 고르면 오히려 선택 폭이 줄어든다.

### 오해 3. classpath 조건은 starter 이름을 본다

실제로는 implementation class를 보는 경우가 많다.

예를 들어 auto-configuration은 보통 이런 질문을 한다.

```text
mysql driver class가 있나?
prometheus registry class가 있나?
특정 sdk client class가 있나?
```

즉 "`starter`는 추가했는데 bean이 없다"면, starter artifact 존재보다 **required class 존재**를 먼저 봐야 한다.

### 오해 4. direct dependency를 선언했으니 버전도 항상 직접 적어야 한다

꼭 그렇지는 않다.

- Spring Boot BOM이 관리하는 artifact면 버전은 BOM이 잡아 줄 수 있다.
- 그래도 **포함 여부 자체**는 앱이 직접 선언해야 할 수 있다.

즉 beginner는 "`버전을 누가 관리하나`"와 "`dependency 포함 결정을 누가 하나`"를 분리해서 생각하면 편하다.

---

## starter를 봤을 때 바로 묻는 5문장

1. 이 starter는 소비자용 entrypoint인가?
2. 실제 auto-configuration 코드는 어느 module에 있나?
3. required implementation class는 transitive로 오나, 앱이 직접 추가해야 하나?
4. 그 implementation artifact는 `runtimeOnly`/`runtime`이 맞나?
5. bean이 없으면 `@ConditionalOnClass`가 어떤 class를 찾고 있는가?

이 다섯 문장만 잡아도 "`starter`, `auto-configuration`, `driver`가 한 덩어리로 보이는 혼란"을 대부분 줄일 수 있다.

참고로 `runtimeOnly`/`runtime`은 앱 코드가 구현 class를 직접 import하지 않고 auto-configuration에 맡길 때 흔하다.
앱 코드에서 vendor SDK type이나 registry type을 직접 참조한다면 compile classpath에도 필요하므로 `implementation` 또는 일반 Maven dependency가 더 맞을 수 있다.

---

## 한 줄 정리

starter는 소비자용 입구이고, auto-configuration module은 bean 조립 규칙이며, SDK/driver는 실제 구현 부품이다. build 파일을 볼 때 이 셋의 선언 책임을 분리하면 "`왜 starter를 넣었는데도 뭔가 더 필요하지?`"라는 혼란이 훨씬 빨리 풀린다.
